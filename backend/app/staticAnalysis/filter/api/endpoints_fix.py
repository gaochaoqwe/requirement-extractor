"""
静态分析自动修复 API 端点

三个粒度：
- single：单问题修复（同步返回生成结果，前端弹窗直接展示 diff）
- file  ：文件级批量修复（后台任务 + 进度轮询）
- rule  ：按规则分类批量修复（后台任务 + 进度轮询）

导出两种模式：
- 导出当前文件（单文件，多编码读取，text/plain）
- 导出修复后的代码库（整包 zip）

挂在 filter router 下，最终路径形如：
  /api/staticAnalysis/filter/{task_id}/fix/generate
"""
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Query
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database.database import get_db
from ..database.fix_migration import ensure_fix_schema
from ..models.models import (
    StaticAnalysisSession,
    StaticAnalysisIssue,
    StaticAnalysisFixTask,
    StaticAnalysisFix,
)
from ..services.fix_service import CodeFixService, FixServiceError

router = APIRouter()

# 首次导入时确保修复相关库表就绪（幂等）
try:
    ensure_fix_schema()
except Exception as _exc:  # noqa: BLE001
    print(f"[修复API] 初始化修复表结构失败: {_exc}")


class FixScope(BaseModel):
    type: str = 'single'      # single / file / rule
    value: Optional[str] = None


class FixGenerateRequest(BaseModel):
    scope: Optional[FixScope] = None
    problem_ids: Optional[List[int]] = None
    user_prompt: Optional[str] = ''
    options: Optional[Dict[str, Any]] = None
    rule_type: Optional[str] = None


class FixIdsRequest(BaseModel):
    fix_ids: List[int]


class FixRegenerateRequest(BaseModel):
    fix_id: int
    user_prompt: Optional[str] = ''


def _get_session_or_404(db: Session, task_id: str) -> StaticAnalysisSession:
    session = None
    try:
        numeric_id = int(task_id)
    except (TypeError, ValueError):
        numeric_id = None
    if numeric_id is not None:
        session = db.query(StaticAnalysisSession).filter(StaticAnalysisSession.id == numeric_id).first()
    if not session:
        session = db.query(StaticAnalysisSession).filter(
            StaticAnalysisSession.session_id == task_id
        ).first()
    if not session:
        raise HTTPException(status_code=404, detail='任务不存在')
    return session


def _collect_issues(db: Session, service: CodeFixService, session: StaticAnalysisSession,
                    payload: FixGenerateRequest) -> List[StaticAnalysisIssue]:
    """根据 scope 收集待修复的问题"""
    scope = payload.scope or FixScope(type='single')

    if payload.problem_ids:
        return db.query(StaticAnalysisIssue).filter(
            StaticAnalysisIssue.id.in_(payload.problem_ids)
        ).all()

    if scope.type == 'single':
        if not scope.value:
            raise HTTPException(status_code=400, detail='单问题修复需要提供 problem_id')
        try:
            pid = int(scope.value)
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail='problem_id 必须是数字')
        issue = db.query(StaticAnalysisIssue).filter(StaticAnalysisIssue.id == pid).first()
        if not issue:
            raise HTTPException(status_code=404, detail='问题不存在')
        return [issue]

    query = db.query(StaticAnalysisIssue).filter(
        StaticAnalysisIssue.task_id == session.id,
        StaticAnalysisIssue.is_filtered == False,  # noqa: E712
    )
    if payload.rule_type:
        query = query.filter(StaticAnalysisIssue.rule_type == payload.rule_type)

    issues = query.all()

    if scope.type == 'file':
        if not scope.value:
            raise HTTPException(status_code=400, detail='文件级修复需要提供文件路径')
        target = str(scope.value).replace('\\', '/')
        matched = []
        for issue in issues:
            rel = service.resolve_rel_path(session, issue.issue_file)
            if not rel:
                continue
            if rel == target or rel.split('/')[-1] == target.split('/')[-1]:
                matched.append(issue)
        if not matched:
            raise HTTPException(status_code=404, detail=f'该文件没有问题可修复: {scope.value}')
        return matched

    if scope.type == 'rule':
        if not scope.value:
            raise HTTPException(status_code=400, detail='规则级修复需要提供 rule_code')
        matched = [issue for issue in issues if issue.rule_code == scope.value]
        if not matched:
            raise HTTPException(status_code=404, detail=f'该规则没有问题可修复: {scope.value}')
        return matched

    raise HTTPException(status_code=400, detail=f'不支持的修复范围类型: {scope.type}')


async def _run_batch_generation(task_id: str, fix_task_id: int, issue_ids: List[int],
                                user_prompt: str, options: Dict[str, Any]):
    """后台批量生成任务（独立 DB 会话）"""
    from ..database.database import get_db_session

    db = get_db_session()
    try:
        task = db.query(StaticAnalysisFixTask).filter(StaticAnalysisFixTask.id == fix_task_id).first()
        if task is None:
            return
        issues = db.query(StaticAnalysisIssue).filter(StaticAnalysisIssue.id.in_(issue_ids)).all()
        service = CodeFixService(task_id)
        await service.generate_batch_fixes(fix_task_id, issues, user_prompt, options, db=db)
    except Exception as exc:  # noqa: BLE001
        print(f"[修复API] 批量生成失败: {exc}")
        try:
            task = db.query(StaticAnalysisFixTask).filter(StaticAnalysisFixTask.id == fix_task_id).first()
            if task:
                task.status = 'error'
                db.commit()
        except Exception:  # noqa: BLE001
            db.rollback()
    finally:
        db.close()


def _task_progress(task: StaticAnalysisFixTask) -> Dict[str, Any]:
    total = task.total or 0
    done = (task.succeeded or 0) + (task.failed or 0) + (task.conflicted or 0)
    return {
        'fix_task_id': task.id,
        'status': task.status,
        'scope_type': task.scope_type,
        'scope_value': task.scope_value,
        'total': total,
        'succeeded': task.succeeded or 0,
        'failed': task.failed or 0,
        'conflicted': task.conflicted or 0,
        'progress': int(done * 100 / total) if total else 0,
        'user_prompt': task.user_prompt,
        'created_at': task.created_at.isoformat() if task.created_at else None,
    }


@router.post("/{task_id}/fix/generate")
async def generate_fix(
    task_id: str,
    background_tasks: BackgroundTasks,
    payload: Optional[FixGenerateRequest] = Body(default=None),
    db: Session = Depends(get_db),
):
    """
    创建修复任务。
    - scope.type = single：同步生成并直接返回条目
    - scope.type = file / rule：创建任务后异步生成，前端轮询 /fix/status
    """
    payload = payload or FixGenerateRequest()
    ensure_fix_schema()
    session = _get_session_or_404(db, task_id)
    service = CodeFixService(str(session.id))

    if not session.codebase_path:
        raise HTTPException(status_code=400, detail='该任务没有代码库，无法执行自动修复')

    scope = payload.scope or FixScope(type='single')
    options = payload.options or {}
    user_prompt = payload.user_prompt or ''

    issues = _collect_issues(db, service, session, payload)
    if not issues:
        raise HTTPException(status_code=404, detail='没有可修复的问题')

    scope_value = scope.value
    if scope.type == 'single':
        scope_value = str(issues[0].id)

    fix_task = StaticAnalysisFixTask(
        task_id=session.id,
        rule_type=issues[0].rule_type if len({i.rule_type for i in issues}) == 1 else 'mixed',
        scope_type=scope.type,
        scope_value=str(scope_value) if scope_value is not None else None,
        user_prompt=user_prompt,
        options_json=json.dumps(options, ensure_ascii=False),
        status='pending',
        total=len(issues),
    )
    db.add(fix_task)
    db.commit()
    db.refresh(fix_task)

    # 单问题：同步生成
    if scope.type == 'single' and len(issues) == 1:
        fix_task.status = 'generating'
        db.commit()
        result = await service.generate_single_fix(db, issues[0], user_prompt, options)
        row = StaticAnalysisFix(
            fix_task_id=fix_task.id,
            problem_id=issues[0].id,
            file_path=result.get('file_path'),
            line_no=result.get('line_no'),
            rule_code=issues[0].rule_code,
            rule_type=issues[0].rule_type,
            original_snippet=result.get('original_snippet'),
            fixed_snippet=result.get('fixed_snippet'),
            diff_text=result.get('diff_text'),
            ai_explanation=result.get('ai_explanation'),
            can_fix=bool(result.get('can_fix')),
            confidence=result.get('confidence'),
            status=result.get('status', 'failed'),
            error_message=result.get('error_message'),
            raw_response=result.get('raw_response'),
        )
        db.add(row)
        db.flush()

        issues[0].fix_id = row.id
        if row.status == 'generated':
            issues[0].fix_status = 1
        elif row.status == 'applied':
            issues[0].fix_status = 2

        fix_task.succeeded = 1 if row.status == 'generated' else 0
        fix_task.conflicted = 1 if row.status == 'conflict' else 0
        fix_task.failed = 1 if row.status == 'failed' else 0
        fix_task.status = 'done' if row.status == 'generated' else (
            'partial' if row.status == 'conflict' else 'error'
        )
        db.commit()
        db.refresh(row)

        return {
            'success': True,
            'fix_task_id': fix_task.id,
            'mode': 'single',
            'status': fix_task.status,
            'items': [row.to_dict()],
            'message': '修复方案生成完成' if row.status == 'generated' else (row.error_message or '生成失败'),
        }

    # 批量：后台生成
    issue_ids = [issue.id for issue in issues]
    background_tasks.add_task(_run_batch_generation, str(session.id), fix_task.id, issue_ids, user_prompt, options)

    return {
        'success': True,
        'fix_task_id': fix_task.id,
        'mode': 'batch',
        'status': 'pending',
        'total': len(issues),
        'message': f'已创建批量修复任务，共 {len(issues)} 个问题',
    }


@router.get("/{task_id}/fix/status/{fix_task_id}")
def get_fix_status(task_id: str, fix_task_id: int, db: Session = Depends(get_db)):
    """轮询修复任务进度"""
    task = db.query(StaticAnalysisFixTask).filter(StaticAnalysisFixTask.id == fix_task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail='修复任务不存在')
    return {'success': True, 'data': _task_progress(task)}


@router.get("/{task_id}/fix/list/{fix_task_id}")
def list_fixes(task_id: str, fix_task_id: int, db: Session = Depends(get_db)):
    """获取修复任务下的所有条目（含 diff）"""
    task = db.query(StaticAnalysisFixTask).filter(StaticAnalysisFixTask.id == fix_task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail='修复任务不存在')

    rows = db.query(StaticAnalysisFix).filter(
        StaticAnalysisFix.fix_task_id == fix_task_id
    ).order_by(StaticAnalysisFix.id.asc()).all()

    # 补充问题描述信息便于前端展示
    problem_ids = [row.problem_id for row in rows if row.problem_id]
    issue_map = {}
    if problem_ids:
        issues = db.query(StaticAnalysisIssue).filter(StaticAnalysisIssue.id.in_(problem_ids)).all()
        issue_map = {issue.id: issue for issue in issues}

    items = []
    for row in rows:
        item = row.to_dict()
        issue = issue_map.get(row.problem_id)
        if issue is not None:
            item['issue_name'] = issue.issue_name
            item['issue_file'] = issue.issue_file
            item['issue_line'] = issue.issue_line
            item['issue_description'] = issue.issue_description
            item['problem_status'] = issue.problem_status
            item['fix_status'] = issue.fix_status
        items.append(item)

    return {'success': True, 'data': {'task': _task_progress(task), 'items': items}}


@router.post("/{task_id}/fix/apply")
def apply_fixes(task_id: str, payload: FixIdsRequest, db: Session = Depends(get_db)):
    """确认落盘：把生成的修复写回副本代码库"""
    ensure_fix_schema()
    if not payload.fix_ids:
        raise HTTPException(status_code=400, detail='fix_ids 不能为空')
    service = CodeFixService(task_id)
    try:
        report = service.apply_fixes(db, payload.fix_ids)
    except FixServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        raise HTTPException(status_code=500, detail=f'应用修复失败: {exc}')
    return {
        'success': True,
        'message': f"已应用 {len(report['applied'])} 条，冲突 {len(report['conflicted'])} 条，失败 {len(report['failed'])} 条",
        'data': report,
    }


@router.post("/{task_id}/fix/rollback")
def rollback_fixes(task_id: str, payload: FixIdsRequest, db: Session = Depends(get_db)):
    """回滚已应用的修复"""
    if not payload.fix_ids:
        raise HTTPException(status_code=400, detail='fix_ids 不能为空')
    service = CodeFixService(task_id)
    try:
        report = service.rollback_fixes(db, payload.fix_ids)
    except FixServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        raise HTTPException(status_code=500, detail=f'回滚失败: {exc}')
    return {
        'success': True,
        'message': f"已回滚 {len(report['rolled_back'])} 条，失败 {len(report['failed'])} 条",
        'data': report,
    }


@router.post("/{task_id}/fix/regenerate")
async def regenerate_fix(task_id: str, payload: FixRegenerateRequest, db: Session = Depends(get_db)):
    """带新的用户提示词重新生成单条修复"""
    ensure_fix_schema()
    row = db.query(StaticAnalysisFix).filter(StaticAnalysisFix.id == payload.fix_id).first()
    if row is None:
        raise HTTPException(status_code=404, detail='修复记录不存在')
    if row.status == 'applied':
        raise HTTPException(status_code=400, detail='该修复已应用，请先回滚再重新生成')

    issue = db.query(StaticAnalysisIssue).filter(StaticAnalysisIssue.id == row.problem_id).first()
    if issue is None:
        raise HTTPException(status_code=404, detail='关联问题不存在')

    fix_task = db.query(StaticAnalysisFixTask).filter(
        StaticAnalysisFixTask.id == row.fix_task_id
    ).first()
    options = {}
    if fix_task and fix_task.options_json:
        try:
            options = json.loads(fix_task.options_json)
        except Exception:  # noqa: BLE001
            options = {}

    service = CodeFixService(task_id)
    result = await service.generate_single_fix(db, issue, payload.user_prompt or '', options)

    row.file_path = result.get('file_path') or row.file_path
    row.line_no = result.get('line_no')
    row.original_snippet = result.get('original_snippet')
    row.fixed_snippet = result.get('fixed_snippet')
    row.diff_text = result.get('diff_text')
    row.ai_explanation = result.get('ai_explanation')
    row.can_fix = bool(result.get('can_fix'))
    row.confidence = result.get('confidence')
    row.status = result.get('status', 'failed')
    row.error_message = result.get('error_message')
    row.raw_response = result.get('raw_response')
    row.applied_at = None
    db.commit()
    db.refresh(row)

    return {'success': True, 'item': row.to_dict(), 'message': row.error_message or '重新生成完成'}


@router.get("/{task_id}/fix/fixed-files")
def list_fixed_files(task_id: str, db: Session = Depends(get_db)):
    """已应用修复的文件列表（导出下拉展示用）"""
    service = CodeFixService(task_id)
    try:
        files = service.list_fixed_files(db)
    except FixServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {'success': True, 'data': {'files': files, 'count': len(files)}}


@router.get("/{task_id}/fix/export-file")
def export_current_file(
    task_id: str,
    file_path: str = Query(..., description='相对代码库根目录的文件路径'),
    db: Session = Depends(get_db),
):
    """导出单个文件（多编码读取），用于"导出当前文件"模式"""
    service = CodeFixService(task_id)
    try:
        content, filename = service.export_current_file(db, file_path)
    except FixServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f'导出失败: {exc}')

    return Response(
        content=content,
        media_type='text/plain; charset=utf-8',
        headers={'Content-Disposition': f"attachment; filename*=UTF-8''{quote(filename)}"},
    )


@router.get("/{task_id}/fix/export-package")
def export_fixed_package(task_id: str, db: Session = Depends(get_db)):
    """导出整个修复后的代码库（zip，保留目录结构）"""
    service = CodeFixService(task_id)
    try:
        buffer, filename, _file_count, _fixed_count = service.export_fixed_package(db)
    except FixServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f'导出代码包失败: {exc}')

    return StreamingResponse(
        buffer,
        media_type='application/zip',
        headers={'Content-Disposition': f"attachment; filename*=UTF-8''{quote(filename)}"},
    )
