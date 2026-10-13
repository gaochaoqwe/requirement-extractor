"""
开始分析的API端点
"""
import os
import asyncio
from urllib.parse import urlsplit
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from ...config_database import get_db  # 使用智能数据库切换模块
from ...db.repository.file_repo import FileRepository
from ...db.repository.task_repo import TaskRepository
from ...service.ai.analysis_runner import run_code_review
from ...db.models.task import AnalysisTask
from ...db.models.file import AnalysisFile
from ...config import MAX_FUNCTION_REVIEW_CONCURRENT_TASKS
from datetime import datetime

from app.auth.db.database import UserModel
from app.auth.routes import verify_token

# 导入统一的日志系统
from ...utils.logger import log_info, log_error

router = APIRouter()

class StartAnalysisRequest(BaseModel):
    file_id: int
    review_mode: str = "function"  # 审查模式: "function" | "chain" | "feature"
    entry_function: Optional[str] = "main"  # 入口函数
    # tester_name 不再需要从前端传入，改为从session获取
    software_type: Optional[str] = None  # 软件类型（chain模式需要）
    options: Optional[Dict[str, Any]] = None  # 其他选项
    requirement_text: Optional[str] = None  # 链路审查：用户上传的需求文档文本


def build_frontend_url(request: Request, path: str) -> str:
    """根据当前请求动态构建前端访问地址，避免硬编码部署机器 IP。"""
    configured_base_url = os.getenv("FRONTEND_BASE_URL", "").strip().rstrip("/")
    if configured_base_url:
        return f"{configured_base_url}{path}"

    forwarded_proto = request.headers.get("x-forwarded-proto")
    forwarded_host = request.headers.get("x-forwarded-host")
    if forwarded_host:
        proto = (forwarded_proto or request.url.scheme or "http").split(",")[0].strip()
        host = forwarded_host.split(",")[0].strip()
        return f"{proto}://{host}{path}"

    referer = request.headers.get("referer") or request.headers.get("origin")
    if referer:
        parsed = urlsplit(referer)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}{path}"

    host = request.headers.get("host") or request.url.netloc
    proto = forwarded_proto.split(",")[0].strip() if forwarded_proto else request.url.scheme
    return f"{proto}://{host}{path}"


def run_analysis_task(
    file_id: int, 
    task_id: int, 
    review_mode: str = "function",
    software_type: Optional[str] = None, 
    entry_function: Optional[str] = None, 
    tester_name: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None
):
    print(
        f"[run_analysis_task][entry] file_id={file_id}, task_id={task_id}, "
        f"review_mode={review_mode}, entry_function={entry_function}, tester_name={tester_name}"
    )
    """
    后台分析任务
    
    Args:
        file_id: 文件ID
        task_id: 任务ID
        review_mode: 审查模式 ("function" | "chain" | "feature")
        software_type: 软件类型
        entry_function: 入口函数
        options: 其他选项
    """
    import sys
    import os
    
    # 添加项目根目录到 Python 路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(current_dir, '../../../../..')
    sys.path.insert(0, project_root)
    
    try:
        log_info(
            f"后台任务开始执行: file_id={file_id}, task_id={task_id}, "
            f"review_mode={review_mode}, entry_function={entry_function}, software_type={software_type}",
            "analysis_task"
        )
        log_info(f"当前工作目录: {os.getcwd()}", "analysis_task")
        log_info(f"Python路径: {sys.path[:3]}...", "analysis_task")
        
        # 正确获取数据库会话
        db_gen = get_db()
        db = next(db_gen)
        print(f"[run_analysis_task][db] session acquired, task_id={task_id}")
        
        try:
            log_info(f"数据库会话获取成功，审查模式: {review_mode}", "analysis_task")

            task_repo = TaskRepository(db)
            task = task_repo.get_task(task_id)
            if task and task.status == "pending":
                task_repo.update_task_status(task_id, "processing")
                log_info(f"任务状态已更新为processing: task_id={task_id}", "analysis_task")
            
            # 获取项目根目录路径
            file_repo = FileRepository(db)
            file_record = file_repo.get_file(file_id)
            print(f"[run_analysis_task][file] file_exists={file_record is not None}, file_id={file_id}, task_id={task_id}")
            if not file_record:
                raise Exception(f"文件不存在: {file_id}")
            
            extract_path = file_record.extract_path
            print(f"[run_analysis_task][path] extract_path={extract_path}, exists={os.path.exists(extract_path) if extract_path else False}, task_id={task_id}")
            if not extract_path or not os.path.exists(extract_path):
                raise Exception(f"解压目录不存在: {extract_path}")
            
            log_info(f"使用解压目录: {extract_path}", "analysis_task")
            
            # 根据审查模式执行不同的逻辑
            if review_mode == "function":
                # 函数审查模式（文件+函数集成）
                log_info(f"[函数审查模式] 开始执行", "analysis_task")
                print(f"[run_analysis_task][function] about to import FileFunctionReviewer, task_id={task_id}")
                
                from ...service.ai.file_function_review import FileFunctionReviewer
                print(f"[run_analysis_task][function] FileFunctionReviewer imported, task_id={task_id}")
                
                reviewer = FileFunctionReviewer(
                    task_id=task_id,
                    project_root=extract_path,
                    file_id=file_id,
                    entry_function=entry_function or "main",
                    tester_name=tester_name
                )
                print(f"[run_analysis_task][function] reviewer created, task_id={task_id}")
                
                result = reviewer.run_review()
                print(f"[run_analysis_task][function] reviewer finished, task_id={task_id}, result={result}")
                log_info(f"[函数审查模式] 执行完成: {result}", "analysis_task")
                
            elif review_mode == "chain":
                # 链路审查模式（渐进式功能发现）
                log_info(f"[链路审查模式] 开始执行", "analysis_task")
                
                from ...service.business_review.chain_review_smart import run_smart_chain_review
                
                # 获取通用知识库（不依赖软件类型）
                def get_kb():
                    """获取通用知识库"""
                    return {
                        "kb_text": """
【业务逻辑审查重点】
你的任务是审查功能实现和业务逻辑，而不是编码规范。重点关注：

1. 功能完整性：功能是否完整实现了预期的业务需求？是否有遗漏的关键步骤？
2. 逻辑正确性：业务流程是否合理？状态转换是否正确？条件判断是否完备？
3. 错误处理：异常情况是否被正确处理？错误是否会导致业务流程中断？
4. 数据流：数据在各模块间传递是否正确？是否有数据丢失或错误转换？
5. 调用关系：函数调用顺序是否合理？是否有循环依赖或不合理的调用？
6. 状态管理：状态变化是否一致？是否有状态不一致导致的问题？
7. 边界情况：边界条件和特殊情况是否被考虑？（如空输入、极端值等）
8. 并发逻辑：多线程/多进程环境下，业务逻辑是否正确？

**不要关注**：代码风格、命名规范、注释格式等编码规范问题。
""",
                        "defect_text": """
【典型业务逻辑问题】
1. 功能缺失：应该实现的功能没有实现
2. 逻辑错误：条件判断错误、循环逻辑错误、状态转换错误
3. 错误处理不当：错误被忽略、错误处理不完整、异常未传播
4. 数据不一致：数据更新不同步、状态不一致、缓存不一致
5. 调用顺序错误：初始化顺序错误、依赖关系错误、资源使用顺序错误
6. 边界处理缺失：未处理空值、未处理极端情况、未处理异常输入
7. 并发问题：竞态条件、死锁、数据不一致（业务层面）
8. 功能冗余或重复：相同功能多次实现、逻辑重复、不必要的复杂性
9. 接口使用错误：API使用不当、参数传递错误、返回值理解错误
10. 性能逻辑问题：不合理的循环、重复计算、不必要的等待

**示例**：
- ❌ 初始化函数在使用之前没有被调用
- ❌ 状态机的某些状态转换路径缺失
- ❌ 错误发生后，系统状态没有回滚
- ❌ 多个线程同时修改业务数据，导致结果不确定
- ❌ 函数返回错误码，但调用者没有检查就继续执行
""",
                        "typical_defects_text": """
【审查问题示例】

✅ 正确的问题描述：
"配置加载失败后，系统继续使用未初始化的配置，导致业务功能异常"
"状态机缺少从ERROR到IDLE的恢复路径，系统无法从错误中恢复"
"数据采集线程和分析线程没有同步机制，可能导致数据不一致"
"日志初始化失败时没有fallback机制，后续日志全部丢失"

❌ 不要报告的问题：
"变量命名不规范" （这是编码规范问题）
"缺少注释" （这是文档问题）
"指针未检查NULL" （这是代码规范问题，除非导致业务逻辑错误）

【如何判断是否是业务逻辑问题】
问自己：这个问题会导致功能无法正常工作吗？
- 如果是 → 这是业务逻辑问题，应该报告
- 如果不是，只是代码不够优雅 → 不要报告
"""
                    }
                
                result = run_smart_chain_review(
                    task_id=task_id,
                    project_root=extract_path,
                    file_id=file_id,
                    entry_function=entry_function or "main",
                    kb=get_kb(),
                    requirement_text=options.get("requirement_text") if options else None
                )
                
                log_info(f"[链路审查模式] 执行完成: {result}", "analysis_task")
                
            elif review_mode == "feature":
                # 功能审查模式（保持原有逻辑）
                log_info(f"[功能审查模式] 开始执行", "analysis_task")
                
                from ...service.business_review.runner.business_runner import run_in_background
                
                run_in_background(
                    task_id, 
                    extract_path, 
                    software_type or "", 
                    entry_function or "main", 
                    options or {}
                )
                
                log_info(f"[功能审查模式] 执行完成", "analysis_task")
                
            else:
                raise ValueError(f"未知的审查模式: {review_mode}")
            
        except ImportError as ie:
            print(f"[run_analysis_task][import_error] task_id={task_id}, error={ie}")
            log_error(f"导入错误: {ie}", "analysis_task")
            raise
        except Exception as e:
            print(f"[run_analysis_task][inner_error] task_id={task_id}, error={e}")
            log_error(f"审查执行异常: {e}", "analysis_task")
            raise
        finally:
            try:
                db.close()
                log_info(f"数据库会话已关闭", "analysis_task")
            except Exception as e:
                log_error(f"关闭数据库会话时出错: {e}", "analysis_task")
            
    except Exception as e:
        print(f"[run_analysis_task][outer_error] file_id={file_id}, task_id={task_id}, error={e}")
        log_error(f"后台任务执行出错: file_id={file_id}, task_id={task_id}", "analysis_task", e)
        import traceback
        print(traceback.format_exc())
        log_error(f"详细错误信息: {traceback.format_exc()}", "analysis_task")
        
        # 尝试更新任务状态为失败
        try:
            db_gen = get_db()
            db = next(db_gen)
            try:
                task_repo = TaskRepository(db)
                task_repo.update_task_status(task_id, "failed")
                db.commit()
                log_info(f"任务状态已更新为失败: task_id={task_id}", "analysis_task")
            finally:
                db.close()
        except Exception as update_error:
            log_error(f"更新任务状态失败: {update_error}", "analysis_task")
        
        # 从取消管理器中移除任务
        try:
            from ...utils.task_cancel_manager import task_cancel_manager
            task_cancel_manager.unregister_task(task_id)
        except Exception:
            pass

@router.post("/start_analysis", summary="Start code review analysis")
def start_analysis(
    req: StartAnalysisRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    print(
        f"[start_analysis][entry] file_id={getattr(req, 'file_id', None)}, "
        f"review_mode={getattr(req, 'review_mode', None)}, entry_function={getattr(req, 'entry_function', None)}"
    )
    """
    开始代码分析
    
    Args:
        req: 包含file_id和可选参数的请求
        request: FastAPI Request对象，用于获取session
        background_tasks: 后台任务管理器
        db: 数据库会话
        
    Returns:
        dict: 包含任务ID的响应
    """
    try:
        # 从session/token中获取当前登录用户信息（统一走 auth 独立数据库）
        user = None
        user_id = request.session.get('user_id')
        if user_id:
            user = UserModel.get_user_by_id(int(user_id))

        if not user:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ', 1)[1]
                payload = verify_token(token)
                if payload and payload.get('user_id'):
                    user = UserModel.get_user_by_id(int(payload.get('user_id')))

        tester_name = None
        if user:
            tester_name = user.get('display_name') or user.get('username')
        if not tester_name:
            tester_name = '未知用户'
        
        log_info(f"当前登录用户: {tester_name}", "start_analysis")
        print(f"[start_analysis][user] tester_name={tester_name}, user_found={user is not None}")
        
        file_repo = FileRepository(db)
        task_repo = TaskRepository(db)
        
        log_info(f"开始处理分析请求: file_id={req.file_id}, software_type={req.software_type}, entry_function={req.entry_function}, tester={tester_name}", "start_analysis")
        
        # 检查文件是否存在
        file_record = file_repo.get_file(req.file_id)
        print(f"[start_analysis][file] file_exists={file_record is not None}, file_id={req.file_id}")
        log_info(f"文件查询结果: {file_record is not None}", "start_analysis")
        
        if not file_record:
            log_error(f"文件不存在: file_id={req.file_id}", "start_analysis")
            raise HTTPException(status_code=404, detail="文件不存在")
        
        log_info(f"找到文件记录: id={file_record.id}, name={file_record.file_name}, status={file_record.status}", "start_analysis")

        # 重复任务检测：仅对函数审查生效
        if req.review_mode == "function":
            duplicate_count = db.query(AnalysisFile).join(
                AnalysisTask, AnalysisTask.id == AnalysisFile.task_id
            ).filter(
                AnalysisTask.status.in_(["pending", "processing"]),
                AnalysisTask.analysis_type.in_(["function", "code_review"]),
                AnalysisFile.file_name == file_record.file_name,
                AnalysisFile.file_size == file_record.file_size
            ).count()
            if duplicate_count > 0:
                raise HTTPException(
                    status_code=409,
                    detail="检测到重复任务：同名且同大小的代码库正在进行审查，请稍后再试"
                )

        # 并发限制：仅对函数审查生效
        if req.review_mode == "function":
            running_count = db.query(AnalysisTask).filter(
                AnalysisTask.status.in_(["pending", "processing"]),
                AnalysisTask.analysis_type.in_(["function", "code_review"])  # 兼容历史默认值
            ).count()
            if running_count >= MAX_FUNCTION_REVIEW_CONCURRENT_TASKS:
                # 返回429以便前端弹窗提示
                raise HTTPException(
                    status_code=429,
                    detail="当前受模型并发限制，使用人数已达上限，请稍后再试"
                )

        # 根据审查模式创建不同的任务描述
        review_mode_names = {
            "function": "函数审查",
            "chain": "链路审查",
            "feature": "功能审查"
        }
        mode_name = review_mode_names.get(req.review_mode, "代码审查")
        
        task_name = f"{mode_name}-{file_record.file_name}"
        task_description = f"对项目 {file_record.file_name} 进行{mode_name}"
        
        if req.review_mode == "chain" and req.software_type:
            task_description += f" (软件类型: {req.software_type})"
        if req.entry_function:
            task_description += f" (入口函数: {req.entry_function})"
        
        # 并发限制：仅对函数审查生效
        if req.review_mode == "function":
            running_count = db.query(AnalysisTask).filter(
                AnalysisTask.status.in_(["pending", "processing"]),
                AnalysisTask.analysis_type.in_(["function", "code_review"])  # 兼容历史默认值
            ).count()
            if running_count >= MAX_FUNCTION_REVIEW_CONCURRENT_TASKS:
                # 返回429以便前端弹窗提示
                raise HTTPException(
                    status_code=429,
                    detail="当前受模型并发限制，使用人数已达上限，请稍后再试"
                )

        # 创建分析任务
        task_data = {
            "task_name": task_name,
            "task_description": task_description,
            "code_file_id": req.file_id,  # 使用正确的字段名
            "status": "pending",
            "progress": 0,
            "tester_name": tester_name,  # 保存测试人员姓名到数据库
            # 根据模式标记任务类型，便于并发统计
            "analysis_type": (
                "function" if req.review_mode == "function" else (
                    "chain_review" if req.review_mode == "chain" else "code_review"
                )
            )
        }
        
        log_info(f"创建任务数据: {task_data}", "start_analysis")
        
        task = task_repo.create_task(task_data)
        print(f"[start_analysis][task] created task_id={task.id}, analysis_type={task.analysis_type}, status={task.status}")
        
        # 更新文件记录，建立双向关联
        file_record.task_id = task.id
        db.add(file_record)
        
        db.commit()
        
        log_info(f"任务创建成功: task_id={task.id}, file_id={req.file_id}，文件关联已更新", "start_analysis")
        
        # 注册任务到取消管理器
        from ...utils.task_cancel_manager import task_cancel_manager
        task_cancel_manager.register_task(task.id)
        log_info(f"任务 {task.id} 已注册到取消管理器", "start_analysis")
        
        # 链路审查：把需求文本合并进 options
        merged_options = dict(req.options or {})
        if req.review_mode == "chain" and req.requirement_text:
            merged_options["requirement_text"] = req.requirement_text
        
        # 启动后台分析任务（使用从session获取的tester_name）
        background_tasks.add_task(
            run_analysis_task, 
            req.file_id, 
            task.id, 
            req.review_mode,
            req.software_type, 
            req.entry_function, 
            tester_name,  # 使用从session获取的用户名
            merged_options
        )
        print(f"[start_analysis][bg] background task scheduled, task_id={task.id}, review_mode={req.review_mode}")
        
        # 构建代码视图地址：优先使用 FRONTEND_BASE_URL，否则根据当前请求动态推导访问地址
        codemap_url = build_frontend_url(request, f"/codemap/{task.id}")
        
        log_info(f"代码视图地址: {codemap_url}", "start_analysis")
        
        return {
            "task_id": task.id,
            "status": "started",
            "message": "分析任务已启动",
            "review_mode": req.review_mode,
            "analysis_mode": mode_name,
            "codemap_url": codemap_url,  # 添加代码视图地址
            "codemap_message": f"您的代码视图地址为：{codemap_url}"  # 友好提示信息
        }
        
    except HTTPException as he:
        # 已经是HTTP异常（如409重复任务、429并发限制等），直接透传给前端
        log_error(f"启动分析任务失败: file_id={req.file_id}", "start_analysis", he)
        raise he
    except Exception as e:
        # 其他未知异常统一视为500内部错误
        log_error(f"启动分析任务失败: file_id={req.file_id}", "start_analysis", e)
        raise HTTPException(status_code=500, detail=f"启动分析失败: {str(e)}")

# 保持向后兼容性，保留原来的路径参数版本
@router.post("/start/{file_id}")
async def start_analysis_legacy(file_id: int, db: Session = Depends(get_db)):
    """
    开始代码分析（兼容性端点）
    
    Args:
        file_id: 文件ID
        db: 数据库会话
        
    Returns:
        dict: 包含任务ID的响应
    """
    # 转换为新的请求格式
    req = StartAnalysisRequest(file_id=file_id)
    background_tasks = BackgroundTasks()
    return start_analysis(req, background_tasks, db)

@router.get("/software_types", summary="Get available software types")
def get_software_types():
    """
    获取可用的软件类型列表
    
    Returns:
        dict: 包含软件类型列表的响应
    """
    try:
        from ...service.business_review.kb.loader import list_kb_types
        types = list_kb_types()
        log_info(f"返回软件类型列表: {len(types)}个类型", "get_software_types")
        return {
            "software_types": types,
            "count": len(types)
        }
    except Exception as e:
        log_error(f"获取软件类型列表失败", "get_software_types", e)
        return {
            "software_types": [],
            "count": 0,
            "error": str(e)
        }

@router.get("/domains", summary="Get available domains")
def get_domains():
    """
    获取可用的领域列表
    
    Returns:
        dict: 包含领域列表的响应
    """
    try:
        from ...service.business_review.kb.loader import list_domains
        domains = list_domains()
        log_info(f"返回领域列表: {len(domains)}个领域", "get_domains")
        return {
            "domains": domains,
            "count": len(domains)
        }
    except Exception as e:
        log_error(f"获取领域列表失败", "get_domains", e)
        return {
            "domains": [],
            "count": 0,
            "error": str(e)
        }

@router.get("/domains/{domain}/software_types", summary="Get software types by domain")
def get_software_types_by_domain(domain: str):
    """
    获取指定领域下的软件类型列表
    
    Args:
        domain: 领域名称
        
    Returns:
        dict: 包含软件类型列表的响应
    """
    try:
        from ...service.business_review.kb.loader import list_software_types_by_domain
        software_types = list_software_types_by_domain(domain)
        log_info(f"返回领域 {domain} 的软件类型列表: {len(software_types)}个类型", "get_software_types_by_domain")
        return {
            "domain": domain,
            "software_types": software_types,
            "count": len(software_types)
        }
    except Exception as e:
        log_error(f"获取领域 {domain} 的软件类型列表失败", "get_software_types_by_domain", e)
        return {
            "domain": domain,
            "software_types": [],
            "count": 0,
            "error": str(e)
        }

@router.get("/domain_structure", summary="Get complete domain-software structure")
def get_domain_structure():
    """
    获取完整的领域-软件类型结构
    
    Returns:
        dict: 包含完整结构的响应
    """
    try:
        from ...service.business_review.kb.loader import get_domain_software_structure
        structure = get_domain_software_structure()
        total_types = sum(len(types) for types in structure.values())
        log_info(f"返回完整领域结构: {len(structure)}个领域, 共{total_types}个软件类型", "get_domain_structure")
        return {
            "structure": structure,
            "domain_count": len(structure),
            "total_software_types": total_types
        }
    except Exception as e:
        log_error(f"获取领域结构失败", "get_domain_structure", e)
        return {
            "structure": {},
            "domain_count": 0,
            "total_software_types": 0,
            "error": str(e)
        }


@router.get("/running_tasks_queue", summary="Get running tasks queue with estimated completion time")
def get_running_tasks_queue(db: Session = Depends(get_db)):
    """
    获取运行中的任务队列（含预计完成时间）
    
    Returns:
        dict: 包含运行中任务列表和预计完成时间
    """
    try:
        # 查询所有运行中的函数审查任务
        running_tasks = db.query(AnalysisTask).filter(
            AnalysisTask.status.in_(["pending", "processing"]),
            AnalysisTask.analysis_type.in_(["function", "code_review"])
        ).order_by(AnalysisTask.created_at).all()
        
        task_list = []
        now = datetime.utcnow()
        
        for task in running_tasks:
            # 计算已运行时间（分钟）
            elapsed_time = (now - task.created_at).total_seconds() / 60
            
            # 预估剩余时间
            progress = max(task.progress, 1)  # 避免除以0
            if progress > 0:
                # 根据当前进度估算总时间
                estimated_total_time = elapsed_time / (progress / 100)
                estimated_remaining_time = estimated_total_time - elapsed_time
                
                # 预计完成时间
                estimated_completion = now.timestamp() + (estimated_remaining_time * 60)
            else:
                estimated_remaining_time = 0
                estimated_completion = now.timestamp()
            
            task_info = {
                "id": task.id,
                "task_name": task.task_name,
                "status": task.status,
                "progress": task.progress,
                "created_at": task.created_at.isoformat(),
                "elapsed_minutes": round(elapsed_time, 1),
                "estimated_remaining_minutes": round(max(estimated_remaining_time, 0), 1),
                "estimated_completion_timestamp": estimated_completion
            }
            task_list.append(task_info)
        
        log_info(f"返回运行中任务队列: {len(task_list)}个任务", "get_running_tasks_queue")
        
        return {
            "running_count": len(task_list),
            "max_concurrent": MAX_FUNCTION_REVIEW_CONCURRENT_TASKS,
            "tasks": task_list
        }
        
    except Exception as e:
        log_error(f"获取运行中任务队列失败", "get_running_tasks_queue", e)
        return {
            "running_count": 0,
            "max_concurrent": MAX_FUNCTION_REVIEW_CONCURRENT_TASKS,
            "tasks": [],
            "error": str(e)
        }
