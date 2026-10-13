"""
静态分析自动修复服务

核心思路：AI 生成结构化补丁（原文片段 / 修复后片段），后端在副本代码库中
精确匹配定位后局部替换，生成 unified diff；默认"先生成、预览确认、再落盘"。

依赖：
- 副本代码库：session.codebase_path（本地磁盘可读写）
- AI 客户端：StaticAnalysisAIClient.chat_completion
- 上下文提取：utils/code_context.build_function_aware_source_snippet
"""
import asyncio
import difflib
import io
import json
import os
import re
import threading
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.staticAnalysis.filter.config.config import (
    FIX_BACKUP_DIR,
    FIX_MAX_CONCURRENCY,
    FIX_MAX_PROBLEMS_PER_FILE,
    FIX_AI_RETRY,
    FIX_SUPPORTED_EXTENSIONS,
)
from app.staticAnalysis.filter.models.models import (
    StaticAnalysisSession,
    StaticAnalysisIssue,
    StaticAnalysisFixTask,
    StaticAnalysisFix,
)
from app.staticAnalysis.filter.utils.code_context import (
    build_function_aware_source_snippet,
    read_file_with_multiple_encodings,
)

# 同文件串行写入锁
_FILE_LOCKS: Dict[str, threading.Lock] = {}
_FILE_LOCKS_GUARD = threading.Lock()


def _get_file_lock(key: str) -> threading.Lock:
    with _FILE_LOCKS_GUARD:
        lock = _FILE_LOCKS.get(key)
        if lock is None:
            lock = threading.Lock()
            _FILE_LOCKS[key] = lock
        return lock


class FixConflictError(Exception):
    """补丁定位失败（原文片段无法在文件中唯一定位）"""


class FixServiceError(Exception):
    """修复服务通用异常"""


# ==================== 文本匹配 / Diff 工具 ====================

def _normalize_line(text: str) -> str:
    return re.sub(r'\s+', ' ', (text or '').strip())


def _find_line_spans(content_lines: List[str], snippet_lines: List[str]) -> List[int]:
    """在 content_lines 中查找与 snippet_lines 逐行（忽略缩进/多余空白）匹配的起始行下标"""
    norm_snippet = [_normalize_line(line) for line in snippet_lines]
    while norm_snippet and not norm_snippet[0]:
        norm_snippet.pop(0)
    while norm_snippet and not norm_snippet[-1]:
        norm_snippet.pop()
    if not norm_snippet:
        return []

    size = len(norm_snippet)
    norm_content = [_normalize_line(line) for line in content_lines]
    if size > len(norm_content):
        return []

    starts = []
    for idx in range(len(norm_content) - size + 1):
        if norm_content[idx:idx + size] == norm_snippet:
            starts.append(idx)
    return starts


def _locate_once(content: str, snippet: str, needle: str = None) -> Tuple[int, int, int]:
    """
    定位 snippet 在 content 中的替换区间。

    Returns:
        (start_char, end_char, start_line_1based)

    Raises:
        FixConflictError: 无法唯一定位
    """
    snippet = snippet if snippet is not None else ''

    # 1) 原文精确匹配
    if snippet:
        count = content.count(snippet)
        if count == 1:
            start = content.index(snippet)
            return start, start + len(snippet), content[:start].count('\n') + 1

    # 2) 按行（忽略缩进差异）匹配
    if snippet:
        content_lines = content.split('\n')
        snippet_lines = snippet.split('\n')
        while snippet_lines and not snippet_lines[-1].strip():
            snippet_lines.pop()
        starts = _find_line_spans(content_lines, snippet_lines)
        if len(starts) == 1:
            idx = starts[0]
            end_idx = idx + len(snippet_lines) - 1
            return (
                sum(len(line) + 1 for line in content_lines[:idx]),
                sum(len(line) + 1 for line in content_lines[:end_idx + 1]) - 1,
                idx + 1,
            )

    # 3) needle 退化：仅替换 needle 所在行
    if needle:
        content_lines = content.split('\n')
        starts = _find_line_spans(content_lines, [needle])
        if len(starts) == 1:
            idx = starts[0]
            return (
                sum(len(line) + 1 for line in content_lines[:idx]),
                sum(len(line) + 1 for line in content_lines[:idx + 1]) - 1,
                idx + 1,
            )

    raise FixConflictError('未能在文件中唯一定位待修复代码片段（原文可能已被修改或存在重复）')


def _apply_edits(content: str, edits: List[Dict[str, Any]]) -> Tuple[str, str, str, int]:
    """
    顺序应用多条 edit，返回 (新内容, 合并后的原文, 合并后的修复文本, 首个变更行号)
    """
    working = content
    originals: List[str] = []
    fixeds: List[str] = []
    first_line: Optional[int] = None

    for edit in edits:
        original = edit.get('original_snippet') or ''
        fixed = edit.get('fixed_snippet') or ''
        needle = edit.get('needle') or ''

        if not original and not needle:
            raise FixConflictError('AI 未给出可定位的原文片段')
        if original and fixed is not None and original == fixed:
            # 无变化，跳过
            continue

        start, end, line_no = _locate_once(working, original, needle)
        working = working[:start] + fixed + working[end:]
        originals.append(original)
        fixeds.append(fixed)
        if first_line is None or line_no < first_line:
            first_line = line_no

    if not fixeds:
        raise FixConflictError('AI 未产生任何有效改动')

    return working, '\n'.join(o for o in originals if o), '\n'.join(fixeds), (first_line or 1)


def build_unified_diff(original: str, fixed: str, file_label: str) -> str:
    diff_lines = difflib.unified_diff(
        original.splitlines(keepends=True),
        fixed.splitlines(keepends=True),
        fromfile=f'a/{file_label}',
        tofile=f'b/{file_label}',
        n=3,
    )
    return ''.join(diff_lines)


def _changed_line_numbers(original: str, fixed: str) -> List[int]:
    """计算修复后新增/修改的行号（相对片段，1-based）"""
    sm = difflib.SequenceMatcher(None, original.split('\n'), fixed.split('\n'))
    changed: List[int] = []
    for tag, _i1, _i2, j1, j2 in sm.get_opcodes():
        if tag in ('replace', 'insert'):
            changed.extend(range(j1 + 1, j2 + 1))
    return changed


# ==================== 提示词模板 ====================

SYSTEM_PROMPT = (
    "你是资深 C/C++ 嵌入式代码修复专家。严格遵守：\n"
    "1) 只修复被指出的规则违反点，不重构、不改变原有业务逻辑与代码风格；\n"
    "2) 禁止修改函数签名、全局变量、宏定义（除非问题本身要求）；\n"
    "3) 只输出 JSON，不要任何解释性文字或 Markdown 代码块。"
)


def build_user_prompt(
    rule_code: str,
    rule_name: str,
    requirement: str,
    impact: str,
    suggestion: str,
    file_path: str,
    line_no: Any,
    issue_desc: str,
    code_context: str,
    user_prompt: str = '',
    options: Optional[Dict[str, Any]] = None,
) -> str:
    options = options or {}
    add_comment = options.get('add_comment')
    constraints = [
        '只允许改动问题行附近，不做无关改动',
        '保持原有缩进与换行风格',
    ]
    if options.get('keep_style', True):
        constraints.append('严格保持原有代码风格')
    if add_comment:
        constraints.append('在修复处补充一行中文注释说明修复原因')
    else:
        constraints.append('不要添加多余注释')

    return f"""[规则] {rule_code} {rule_name}
[规范要求] {requirement}
[影响] {impact}
[官方改进建议] {suggestion}
[问题] {file_path}:{line_no} {issue_desc}
[代码上下文]
```c
{code_context}
```
[修复约束] {'；'.join(constraints)}。
[额外要求（用户提供，可为空）] {user_prompt or '（无）'}

请输出严格的 JSON：
{{
  "can_fix": true,
  "reason": "不可修复时说明原因，可修复时留空",
  "explanation": "修复说明（中文，1-3 句）",
  "confidence": 0.0,
  "edits": [
    {{
      "needle": "用于在文件中唯一定位原文的简短片段（尽量只含问题行）",
      "original_snippet": "将被替换的完整原文（含原始缩进，尽量只覆盖问题行）",
      "fixed_snippet": "替换后的完整文本",
      "note": "本条改动说明"
    }}
  ]
}}
若无法自动修复，请返回 {{"can_fix": false, "reason": "原因", "edits": []}}。"""


def _clean_json_string(text: str) -> str:
    text = (text or '').replace('```json', '').replace('```', '').strip()
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        return text[start:end + 1]
    return text


def parse_fix_response(content: str) -> Dict[str, Any]:
    """解析 AI 返回的修复 JSON，容错处理"""
    try:
        data = json.loads(_clean_json_string(content))
    except Exception as exc:  # noqa: BLE001
        raise FixServiceError(f'AI 响应不是合法 JSON: {exc}') from exc

    edits = data.get('edits') or []
    if not isinstance(edits, list):
        edits = []
    data['edits'] = [e for e in edits if isinstance(e, dict)]
    data.setdefault('can_fix', bool(data['edits']))
    try:
        data['confidence'] = float(data.get('confidence') or 0)
    except (TypeError, ValueError):
        data['confidence'] = 0.0
    return data


class CodeFixService:
    """代码修复服务（单实例对应一个静态分析任务）"""

    def __init__(self, task_id: str, ai_client=None, logger=None):
        self.task_id = task_id
        self._ai_client = ai_client
        self.logger = logger

    # ---------- 基础工具 ----------

    def _log(self, level: str, msg: str):
        if self.logger:
            getattr(self.logger, level, self.logger.info)(msg)
        else:
            print(f"[CodeFixService] {msg}")

    def get_ai_client(self):
        if self._ai_client is None:
            from app.staticAnalysis.filter.services.ai_client import StaticAnalysisAIClient
            self._ai_client = StaticAnalysisAIClient(session_id=self.task_id, logger=self.logger)
        return self._ai_client

    def resolve_session(self, db) -> StaticAnalysisSession:
        session = None
        try:
            numeric_id = int(self.task_id)
        except (TypeError, ValueError):
            numeric_id = None
        if numeric_id is not None:
            session = db.query(StaticAnalysisSession).filter(StaticAnalysisSession.id == numeric_id).first()
        if not session:
            session = db.query(StaticAnalysisSession).filter(
                StaticAnalysisSession.session_id == self.task_id
            ).first()
        if not session:
            raise FixServiceError(f'任务不存在: {self.task_id}')
        return session

    def codebase_path(self, session: StaticAnalysisSession) -> str:
        if not session.codebase_path:
            raise FixServiceError('该任务没有代码库，无法执行自动修复')
        base = Path(session.codebase_path)
        if not base.exists():
            raise FixServiceError(f'代码库目录不存在: {base}')
        return str(base)

    def list_source_files(self, session: StaticAnalysisSession) -> List[str]:
        """返回副本代码库内所有源码文件的相对路径（POSIX 风格）"""
        base = Path(self.codebase_path(session))
        result: List[str] = []
        for path in base.rglob('*'):
            if path.is_file() and path.suffix.lower() in FIX_SUPPORTED_EXTENSIONS:
                rel = path.relative_to(base).as_posix()
                result.append(rel)
        return result

    def resolve_rel_path(self, session: StaticAnalysisSession, issue_file: str) -> Optional[str]:
        """把问题单里的 issue_file 解析为代码库内的相对路径"""
        if not issue_file:
            return None
        normalized = str(issue_file).replace('\\', '/').strip().lstrip('./')
        files = self.list_source_files(session)
        if not files:
            return None

        # 1) 精确匹配
        if normalized in files:
            return normalized
        # 2) 忽略大小写
        lowered = normalized.lower()
        for rel in files:
            if rel.lower() == lowered:
                return rel
        # 3) 后缀匹配
        for rel in files:
            if rel.lower().endswith('/' + lowered) or rel.lower().endswith(lowered):
                return rel
        # 4) 仅文件名匹配
        base_name = normalized.split('/')[-1].lower()
        candidates = [rel for rel in files if rel.split('/')[-1].lower() == base_name]
        if len(candidates) == 1:
            return candidates[0]
        if candidates:
            return candidates[0]
        return None

    def abs_path(self, session: StaticAnalysisSession, rel_path: str) -> str:
        base = Path(self.codebase_path(session)).resolve()
        target = (base / rel_path).resolve()
        if base not in target.parents and target != base:
            raise FixServiceError('非法的文件路径（越出代码库目录）')
        return str(target)

    def read_source(self, session: StaticAnalysisSession, rel_path: str) -> Tuple[str, str]:
        abs_path = self.abs_path(session, rel_path)
        if not os.path.exists(abs_path):
            raise FixServiceError(f'文件不存在: {rel_path}')
        content, encoding = read_file_with_multiple_encodings(abs_path)
        if content is None:
            raise FixServiceError(f'文件读取失败: {rel_path}')
        return content, encoding

    def write_source(self, session: StaticAnalysisSession, rel_path: str, content: str, encoding: str):
        abs_path = self.abs_path(session, rel_path)
        with _get_file_lock(abs_path):
            with open(abs_path, 'w', encoding=encoding or 'utf-8', newline='') as f:
                f.write(content)

    @staticmethod
    def _parse_line_no(issue_line: Any) -> int:
        try:
            match = re.search(r'\d+', str(issue_line or ''))
            return int(match.group(0)) if match else 0
        except Exception:  # noqa: BLE001
            return 0

    def get_rule_info(self, db, issue: StaticAnalysisIssue) -> Dict[str, str]:
        """查询规则库获取规则名称 / 规范要求 / 影响 / 官方改进建议"""
        info = {
            'rule_code': issue.rule_code or '',
            'rule_name': '',
            'requirement': '',
            'impact': '',
            'suggestion': '',
        }
        if not issue.rule_code:
            return info
        try:
            from app.staticAnalysis.filter.database.postgresql_models import GJB8114Rule, CWERule

            db_rule_code = issue.rule_code
            if issue.rule_type == 'gjb' and str(issue.rule_code).startswith('GJB_R_'):
                parts = str(issue.rule_code).split('_')
                if len(parts) == 5:
                    db_rule_code = f"R-{int(parts[2])}-{int(parts[3])}-{int(parts[4])}"

            rule = None
            if issue.rule_type == 'gjb':
                rule = db.query(GJB8114Rule).filter(GJB8114Rule.rule_code == db_rule_code).first()
                if rule is None:
                    rule = db.query(GJB8114Rule).filter(GJB8114Rule.rule_code == issue.rule_code).first()
            else:
                rule = db.query(CWERule).filter(CWERule.rule_code == db_rule_code).first()
                if rule is None:
                    rule = db.query(CWERule).filter(CWERule.rule_code == issue.rule_code).first()
            if rule is not None:
                info['rule_name'] = getattr(rule, 'problem_name', '') or ''
                info['requirement'] = getattr(rule, 'requirement_description', '') or ''
                info['impact'] = getattr(rule, 'impact_analysis', '') or ''
                info['suggestion'] = getattr(rule, 'improvement_suggestion', '') or ''
        except Exception as exc:  # noqa: BLE001
            self._log('warning', f'查询规则信息失败: {exc}')
        return info

    # ---------- 生成 ----------

    async def generate_single_fix(
        self,
        db,
        issue: StaticAnalysisIssue,
        user_prompt: str = '',
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        为单条问题生成修复补丁。

        Returns:
            dict: {status, original_snippet, fixed_snippet, diff_text, ai_explanation,
                   confidence, line_no, file_path, error_message, can_fix, raw_response}
        """
        result: Dict[str, Any] = {
            'status': 'generated',
            'file_path': None,
            'line_no': None,
            'original_snippet': None,
            'fixed_snippet': None,
            'diff_text': None,
            'ai_explanation': None,
            'confidence': None,
            'can_fix': False,
            'error_message': None,
            'raw_response': None,
        }

        session = self.resolve_session(db)
        rel_path = self.resolve_rel_path(session, issue.issue_file)
        if not rel_path:
            result.update({
                'status': 'failed',
                'error_message': f'在代码库中找不到问题所在文件: {issue.issue_file}',
            })
            return result
        result['file_path'] = rel_path

        try:
            content, _encoding = self.read_source(session, rel_path)
        except FixServiceError as exc:
            result.update({'status': 'failed', 'error_message': str(exc)})
            return result

        line_no = self._parse_line_no(issue.issue_line)
        code_context = build_function_aware_source_snippet(content, line_no, context=8)
        rule_info = self.get_rule_info(db, issue)

        prompt = build_user_prompt(
            rule_code=rule_info['rule_code'],
            rule_name=rule_info['rule_name'],
            requirement=rule_info['requirement'],
            impact=rule_info['impact'],
            suggestion=rule_info['suggestion'],
            file_path=rel_path,
            line_no=issue.issue_line,
            issue_desc=issue.issue_description or issue.issue_name or '',
            code_context=code_context,
            user_prompt=user_prompt,
            options=options,
        )
        messages = [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': prompt},
        ]

        try:
            response = await self.get_ai_client().chat_completion(messages, temperature=0.2, max_tokens=4000)
            raw = response.get('content', '')
            result['raw_response'] = raw
            parsed = parse_fix_response(raw)
        except Exception as exc:  # noqa: BLE001
            result.update({'status': 'failed', 'error_message': f'AI 调用失败: {exc}'})
            return result

        result['ai_explanation'] = parsed.get('explanation') or parsed.get('reason') or ''
        result['confidence'] = parsed.get('confidence')

        if not parsed.get('can_fix') or not parsed.get('edits'):
            result.update({
                'status': 'failed',
                'can_fix': False,
                'error_message': parsed.get('reason') or 'AI 判断该问题无法自动修复',
            })
            return result

        try:
            new_content, merged_original, merged_fixed, start_line = _apply_edits(content, parsed['edits'])
        except FixConflictError as exc:
            result.update({'status': 'conflict', 'error_message': str(exc), 'can_fix': True})
            return result
        except Exception as exc:  # noqa: BLE001
            result.update({'status': 'failed', 'error_message': str(exc)})
            return result

        result.update({
            'status': 'generated',
            'can_fix': True,
            'line_no': start_line,
            'original_snippet': merged_original,
            'fixed_snippet': merged_fixed,
            'diff_text': build_unified_diff(content, new_content, rel_path),
        })
        return result

    async def generate_batch_fixes(
        self,
        fix_task_id: int,
        issues: List[StaticAnalysisIssue],
        user_prompt: str = '',
        options: Optional[Dict[str, Any]] = None,
        db=None,
    ):
        """
        批量生成：按文件分组，每文件一次 AI 调用；Semaphore 限流。
        逐条落库并更新任务计数。
        """
        from app.staticAnalysis.filter.database.database import get_db_session

        options = options or {}
        concurrency = int(options.get('concurrency') or FIX_MAX_CONCURRENCY)
        semaphore = asyncio.Semaphore(max(1, concurrency))

        owned_db = db is None
        if owned_db:
            db = get_db_session()

        try:
            task = db.query(StaticAnalysisFixTask).filter(StaticAnalysisFixTask.id == fix_task_id).first()
            if task is None:
                self._log('error', f'修复任务不存在: {fix_task_id}')
                return

            session = self.resolve_session(db)

            # 按文件分组
            groups: Dict[str, List[StaticAnalysisIssue]] = {}
            unresolved: List[StaticAnalysisIssue] = []
            for issue in issues:
                rel = self.resolve_rel_path(session, issue.issue_file)
                if not rel:
                    unresolved.append(issue)
                    continue
                groups.setdefault(rel, []).append(issue)

            # 无法定位文件的直接标记失败
            for issue in unresolved:
                self._save_fix_row(
                    db, fix_task_id, issue,
                    file_path=None, line_no=None,
                    status='failed',
                    error_message=f'代码库中找不到文件: {issue.issue_file}',
                )

            task.status = 'generating'
            task.total = len(issues)
            task.succeeded = 0
            task.failed = len(unresolved)
            task.conflicted = 0
            db.commit()

            lock = asyncio.Lock()

            async def run_group(rel_path: str, group_issues: List[StaticAnalysisIssue]):
                async with semaphore:
                    try:
                        results = await self._generate_for_file(
                            db, session, rel_path, group_issues, user_prompt, options
                        )
                    except Exception as exc:  # noqa: BLE001
                        self._log('error', f'生成失败 {rel_path}: {exc}')
                        results = [
                            {'issue': issue, 'status': 'failed', 'error_message': str(exc)}
                            for issue in group_issues
                        ]

                    async with lock:
                        for item in results:
                            self._save_fix_row(
                                db, fix_task_id, item['issue'],
                                file_path=rel_path,
                                line_no=item.get('line_no'),
                                original_snippet=item.get('original_snippet'),
                                fixed_snippet=item.get('fixed_snippet'),
                                diff_text=item.get('diff_text'),
                                ai_explanation=item.get('ai_explanation'),
                                confidence=item.get('confidence'),
                                can_fix=item.get('can_fix', False),
                                status=item.get('status', 'failed'),
                                error_message=item.get('error_message'),
                                raw_response=item.get('raw_response'),
                            )
                            if item.get('status') == 'generated':
                                task.succeeded += 1
                            elif item.get('status') == 'conflict':
                                task.conflicted += 1
                            else:
                                task.failed += 1
                        db.commit()

            await asyncio.gather(*[run_group(rel, grp) for rel, grp in groups.items()])

            # 汇总任务状态
            if task.succeeded == task.total and task.total > 0:
                task.status = 'done'
            elif task.succeeded > 0:
                task.status = 'partial'
            else:
                task.status = 'error'
            db.commit()
            self._log('info', f'批量修复生成完成: total={task.total}, ok={task.succeeded}, '
                              f'conflict={task.conflicted}, failed={task.failed}')
        finally:
            if owned_db:
                db.close()

    async def _generate_for_file(
        self,
        db,
        session: StaticAnalysisSession,
        rel_path: str,
        issues: List[StaticAnalysisIssue],
        user_prompt: str,
        options: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """对单个文件的所有问题做一次 AI 调用（超阈值则分批）"""
        content, _encoding = self.read_source(session, rel_path)
        results: List[Dict[str, Any]] = []

        batches = [
            issues[i:i + FIX_MAX_PROBLEMS_PER_FILE]
            for i in range(0, len(issues), FIX_MAX_PROBLEMS_PER_FILE)
        ] or [[]]

        for batch in batches:
            results.extend(await self._generate_for_file_batch(db, rel_path, content, batch, user_prompt, options))
        return results

    async def _generate_for_file_batch(
        self,
        db,
        rel_path: str,
        content: str,
        issues: List[StaticAnalysisIssue],
        user_prompt: str,
        options: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        if not issues:
            return []

        # 为每个问题准备上下文
        issue_blocks = []
        for idx, issue in enumerate(issues, start=1):
            line_no = self._parse_line_no(issue.issue_line)
            rule_info = self.get_rule_info(db, issue)
            context = build_function_aware_source_snippet(content, line_no, context=6)
            issue_blocks.append(
                f"### 问题 {idx}（id={issue.id}）\n"
                f"- 规则：{rule_info['rule_code']} {rule_info['rule_name']}\n"
                f"- 规范要求：{rule_info['requirement']}\n"
                f"- 位置：{rel_path}:{issue.issue_line}\n"
                f"- 描述：{issue.issue_description or issue.issue_name or ''}\n"
                f"- 官方改进建议：{rule_info['suggestion']}\n"
                f"- 代码上下文：\n```c\n{context}\n```"
            )

        constraints = [
            '只允许改动问题行附近，不做无关改动',
            '保持原有缩进与换行风格',
        ]
        if options.get('keep_style', True):
            constraints.append('严格保持原有代码风格')
        constraints.append('在修复处补充一行中文注释说明修复原因' if options.get('add_comment') else '不要添加多余注释')

        prompt = (
            f"文件：{rel_path}\n"
            f"请针对下列每一个问题分别给出修复补丁。同一次回复中返回全部问题的修复。\n\n"
            + '\n\n'.join(issue_blocks)
            + f"\n\n[修复约束] {'；'.join(constraints)}。\n"
            + f"[额外要求（用户提供，可为空）] {user_prompt or '（无）'}\n\n"
            + "请输出严格的 JSON（edits 为数组，每个元素对应一个问题）：\n"
            + "{\n"
            + '  "fixes": [\n'
            + "    {\n"
            + '      "problem_id": 对应问题的 id,\n'
            + '      "can_fix": true,\n'
            + '      "reason": "不可修复时说明原因",\n'
            + '      "explanation": "修复说明（中文，1-3 句）",\n'
            + '      "confidence": 0.0,\n'
            + '      "edits": [\n'
            + '        {"needle": "定位片段", "original_snippet": "被替换的原文", '
              '"fixed_snippet": "替换后文本", "note": "说明"}\n'
            + "      ]\n"
            + "    }\n"
            + "  ]\n"
            + "}"
        )

        messages = [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': prompt},
        ]

        raw = ''
        parsed: Dict[str, Any] = {}
        last_error = None
        for attempt in range(FIX_AI_RETRY + 1):
            try:
                response = await self.get_ai_client().chat_completion(messages, temperature=0.2, max_tokens=8000)
                raw = response.get('content', '')
                parsed = json.loads(_clean_json_string(raw))
                break
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if attempt >= FIX_AI_RETRY:
                    break
                await asyncio.sleep(1)

        if not isinstance(parsed, dict) or not isinstance(parsed.get('fixes'), list):
            return [
                {
                    'issue': issue, 'status': 'failed',
                    'error_message': f'AI 响应解析失败: {last_error or "未返回 fixes 数组"}',
                    'raw_response': raw,
                }
                for issue in issues
            ]

        by_id = {int(f.get('problem_id')): f for f in parsed['fixes'] if str(f.get('problem_id', '')).isdigit()}
        results = []
        for issue in issues:
            item = by_id.get(issue.id)
            if item is None:
                # 退化：按顺序取
                idx = issues.index(issue)
                if idx < len(parsed['fixes']):
                    item = parsed['fixes'][idx]
            if item is None:
                results.append({'issue': issue, 'status': 'failed',
                                'error_message': 'AI 未返回该问题的修复结果', 'raw_response': raw})
                continue

            entry = {
                'issue': issue,
                'raw_response': raw,
                'ai_explanation': item.get('explanation') or item.get('reason') or '',
                'confidence': item.get('confidence'),
                'can_fix': bool(item.get('can_fix')),
            }
            edits = item.get('edits') or []
            if not item.get('can_fix') or not edits:
                entry.update({'status': 'failed',
                              'error_message': item.get('reason') or 'AI 判断无法自动修复'})
                results.append(entry)
                continue
            try:
                new_content, merged_original, merged_fixed, start_line = _apply_edits(content, edits)
                entry.update({
                    'status': 'generated',
                    'line_no': start_line,
                    'original_snippet': merged_original,
                    'fixed_snippet': merged_fixed,
                    'diff_text': build_unified_diff(content, new_content, rel_path),
                })
            except FixConflictError as exc:
                entry.update({'status': 'conflict', 'error_message': str(exc)})
            except Exception as exc:  # noqa: BLE001
                entry.update({'status': 'failed', 'error_message': str(exc)})
            results.append(entry)
        return results

    def _save_fix_row(self, db, fix_task_id: int, issue: StaticAnalysisIssue, **kwargs) -> StaticAnalysisFix:
        row = StaticAnalysisFix(
            fix_task_id=fix_task_id,
            problem_id=issue.id,
            file_path=kwargs.get('file_path'),
            line_no=kwargs.get('line_no'),
            rule_code=issue.rule_code,
            rule_type=issue.rule_type,
            original_snippet=kwargs.get('original_snippet'),
            fixed_snippet=kwargs.get('fixed_snippet'),
            diff_text=kwargs.get('diff_text'),
            ai_explanation=kwargs.get('ai_explanation'),
            can_fix=kwargs.get('can_fix', False),
            confidence=kwargs.get('confidence'),
            status=kwargs.get('status', 'failed'),
            error_message=kwargs.get('error_message'),
            raw_response=kwargs.get('raw_response'),
        )
        db.add(row)
        db.flush()

        fix_status = 2 if row.status == 'applied' else (1 if row.status == 'generated' else 0)
        issue.fix_id = row.id
        if row.status in ('generated', 'conflict', 'failed'):
            issue.fix_status = fix_status
        return row

    # ---------- 应用 / 回滚 ----------

    def apply_fixes(self, db, fix_ids: List[int]) -> Dict[str, Any]:
        """把指定修复条目写回副本代码库"""
        session = self.resolve_session(db)
        rows = db.query(StaticAnalysisFix).filter(StaticAnalysisFix.id.in_(fix_ids)).all()
        if not rows:
            raise FixServiceError('未找到待应用的修复记录')

        report = {'applied': [], 'conflicted': [], 'failed': []}

        grouped: Dict[str, List[StaticAnalysisFix]] = {}
        for row in rows:
            if row.status not in ('generated', 'conflict'):
                continue
            if not row.file_path:
                report['failed'].append({'fix_id': row.id, 'reason': '缺少文件路径'})
                continue
            grouped.setdefault(row.file_path, []).append(row)

        for rel_path, file_rows in grouped.items():
            try:
                self._apply_file(db, session, rel_path, file_rows, report)
            except Exception as exc:  # noqa: BLE001
                db.rollback()
                self._log('error', f'应用修复失败 {rel_path}: {exc}')
                for row in file_rows:
                    row.status = 'failed'
                    row.error_message = str(exc)
                    report['failed'].append({'fix_id': row.id, 'reason': str(exc)})
                db.commit()

        return report

    def _apply_file(self, db, session, rel_path: str, rows: List[StaticAnalysisFix], report: Dict[str, Any]):
        content, encoding = self.read_source(session, rel_path)
        original_content = content
        working = content

        # 按行号倒序，规避行号漂移
        ordered = sorted(rows, key=lambda r: (r.line_no or 0), reverse=True)
        applied_rows: List[StaticAnalysisFix] = []
        conflicts: List[Tuple[StaticAnalysisFix, str]] = []

        for row in ordered:
            if not row.original_snippet:
                conflicts.append((row, '缺少原文片段，无法定位'))
                continue
            try:
                start, end, _line = _locate_once(working, row.original_snippet, None)
            except FixConflictError as exc:
                conflicts.append((row, str(exc)))
                continue
            new_working = working[:start] + (row.fixed_snippet or '') + working[end:]
            if new_working == working:
                conflicts.append((row, '补丁内容与原文一致，无实际改动'))
                continue
            working = new_working
            applied_rows.append(row)

        # 任一 hunk 冲突 → 整文件回退
        if conflicts:
            for row, reason in conflicts:
                row.status = 'conflict'
                row.error_message = reason
                report['conflicted'].append({'fix_id': row.id, 'reason': reason})
            for row in applied_rows:
                row.status = 'generated'
                row.error_message = '同文件存在冲突，本次未应用'
            db.commit()
            return

        if not applied_rows:
            db.commit()
            return

        # 备份 + 写盘
        backup_path = self._backup_file(session, rel_path, rows[0].fix_task_id, original_content, encoding)
        try:
            self.write_source(session, rel_path, working, encoding)
        except Exception as exc:  # noqa: BLE001
            raise FixServiceError(f'写入文件失败: {exc}') from exc

        now = datetime.utcnow()
        for row in applied_rows:
            row.status = 'applied'
            row.backup_path = backup_path
            row.applied_at = now
            row.error_message = None
            if row.problem_id:
                issue = db.query(StaticAnalysisIssue).filter(StaticAnalysisIssue.id == row.problem_id).first()
                if issue:
                    issue.fix_status = 2
                    issue.fix_id = row.id
            report['applied'].append({
                'fix_id': row.id,
                'file_path': rel_path,
                'line_no': row.line_no,
                'applied_lines': list(range(
                    (row.line_no or 1),
                    (row.line_no or 1) + max(1, len((row.fixed_snippet or '').split('\n')))
                )),
            })
        db.commit()
        self._log('info', f'已应用修复: {rel_path}, 条目数={len(applied_rows)}')

    def _backup_file(self, session, rel_path: str, fix_task_id: int, content: str, encoding: str) -> str:
        """备份原文件；同一次修复任务对同一文件只备份一次（保留最初版本）"""
        target_dir = Path(FIX_BACKUP_DIR) / str(fix_task_id) / Path(rel_path).parent
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / Path(rel_path).name
        if not target.exists():
            with open(target, 'w', encoding=encoding or 'utf-8', newline='') as f:
                f.write(content)
        try:
            return str(target.relative_to(Path(FIX_BACKUP_DIR)))
        except ValueError:
            return str(target)

    def rollback_fixes(self, db, fix_ids: List[int]) -> Dict[str, Any]:
        """回滚已应用的修复（优先反向替换，失败则用备份还原）"""
        session = self.resolve_session(db)
        rows = db.query(StaticAnalysisFix).filter(StaticAnalysisFix.id.in_(fix_ids)).all()
        report = {'rolled_back': [], 'failed': []}

        grouped: Dict[str, List[StaticAnalysisFix]] = {}
        for row in rows:
            if row.status != 'applied' or not row.file_path:
                report['failed'].append({'fix_id': row.id, 'reason': '该记录不是已应用状态'})
                continue
            grouped.setdefault(row.file_path, []).append(row)

        for rel_path, file_rows in grouped.items():
            content, encoding = self.read_source(session, rel_path)
            working = content
            reverted: List[StaticAnalysisFix] = []
            ok = True
            for row in sorted(file_rows, key=lambda r: (r.line_no or 0), reverse=True):
                if not row.fixed_snippet:
                    ok = False
                    break
                try:
                    start, end, _ = _locate_once(working, row.fixed_snippet, None)
                except FixConflictError:
                    ok = False
                    break
                working = working[:start] + (row.original_snippet or '') + working[end:]
                reverted.append(row)

            if not ok:
                # 退化：用备份整体还原
                row0 = file_rows[0]
                backup_abs = None
                if row0.backup_path:
                    candidate = Path(FIX_BACKUP_DIR) / row0.backup_path
                    if candidate.exists():
                        backup_abs = candidate
                    elif Path(row0.backup_path).exists():
                        backup_abs = Path(row0.backup_path)
                if backup_abs is None:
                    for row in file_rows:
                        report['failed'].append({'fix_id': row.id, 'reason': '无法定位且无备份，回滚失败'})
                    continue
                content_bak, encoding_bak = read_file_with_multiple_encodings(str(backup_abs))
                self.write_source(session, rel_path, content_bak, encoding_bak)
                reverted = list(file_rows)
            else:
                self.write_source(session, rel_path, working, encoding)

            for row in reverted:
                row.status = 'rolled_back'
                row.applied_at = None
                if row.problem_id:
                    issue = db.query(StaticAnalysisIssue).filter(StaticAnalysisIssue.id == row.problem_id).first()
                    if issue and issue.fix_id == row.id:
                        issue.fix_status = 1  # 已生成待确认
                report['rolled_back'].append({'fix_id': row.id, 'file_path': rel_path})
            db.commit()

        return report

    # ---------- 导出 ----------

    def export_current_file(self, db, rel_path: str) -> Tuple[bytes, str]:
        """导出单个文件（多编码读取），返回 (内容字节, 下载文件名)"""
        session = self.resolve_session(db)
        normalized = self.resolve_rel_path(session, rel_path) or rel_path
        content, encoding = self.read_source(session, normalized)
        return content.encode(encoding or 'utf-8', errors='replace'), os.path.basename(normalized)

    def list_fixed_files(self, db) -> List[Dict[str, Any]]:
        """已应用修复的文件列表"""
        session = self.resolve_session(db)
        rows = db.query(StaticAnalysisFix).filter(
            StaticAnalysisFix.status == 'applied'
        ).all()
        counter: Dict[str, int] = {}
        for row in rows:
            if row.file_path:
                counter[row.file_path] = counter.get(row.file_path, 0) + 1
        return [
            {'file_path': path, 'fixed_count': count}
            for path, count in sorted(counter.items())
        ]

    def export_fixed_package(self, db) -> Tuple[io.BytesIO, str, int, int]:
        """打包整个副本代码库（含已应用修复），返回 (BytesIO, 文件名, 文件数, 修复数)"""
        session = self.resolve_session(db)
        base = Path(self.codebase_path(session))

        fixed_rows = db.query(StaticAnalysisFix).filter(StaticAnalysisFix.status == 'applied').all()
        fixed_files = {row.file_path for row in fixed_rows if row.file_path}

        buffer = io.BytesIO()
        file_count = 0
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for path in base.rglob('*'):
                if not path.is_file():
                    continue
                rel = path.relative_to(base).as_posix()
                try:
                    with open(path, 'rb') as f:
                        zf.writestr(rel, f.read())
                    file_count += 1
                except Exception as exc:  # noqa: BLE001
                    self._log('warning', f'打包跳过文件 {rel}: {exc}')

            readme = (
                '修复代码说明\n'
                '================\n'
                f'任务ID：{session.id}（session_id={session.session_id}）\n'
                f'导出时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n'
                f'代码文件数：{file_count}\n'
                f'已应用修复的问题数：{len(fixed_rows)}\n'
                f'涉及文件数：{len(fixed_files)}\n\n'
                '说明：本压缩包为静态分析自动修复后的代码库副本，已包含所有"已应用"的修复。\n'
                '如发现修复有误，可在代码视图中执行"撤销"，或使用修复前备份（fix_backups）还原。\n'
            )
            zf.writestr('修复代码说明.txt', readme.encode('utf-8'))

        buffer.seek(0)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{session.session_id or session.id}_{timestamp}_fixed.zip"
        return buffer, filename, file_count, len(fixed_rows)
