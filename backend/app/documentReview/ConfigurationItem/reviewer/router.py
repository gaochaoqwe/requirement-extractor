from fastapi import APIRouter, Body, Query, BackgroundTasks, Form, Depends
from fastapi.responses import JSONResponse
import os
import sqlite3
import logging
import traceback
from datetime import datetime
from pathlib import Path
from .prompt.compose_taskbook_prompt import compose_taskbook_prompt
from .prompt.compose_requirementspec_prompt import compose_requirementspec_prompt
from .openai.openai_api import ModelCaller
from .analysis.analysis_taskbook import parse_taskbook_model_output
from .analysis.analysis_requirementspec import parse_violation_rules_model_output
from .utils.document_splitter import split_document, merge_issues
import json

# 导入日志系统
from ..utils.logger import (
    set_current_session, clear_current_session, log_debug, log_info,
    log_warning, log_error
)

# 导入配置
try:
    from ..config import AI_CONCURRENT_REQUESTS
    ENABLE_CONCURRENT_REVIEW = True
    log_info(f"[配置] 并发审查功能已启用，并发数: {AI_CONCURRENT_REQUESTS}", "router_init")
except ImportError:
    ENABLE_CONCURRENT_REVIEW = False
    AI_CONCURRENT_REQUESTS = 1
    log_warning("[配置] 未找到配置文件，使用顺序审查模式", "router_init")

# 设置日志
logger = logging.getLogger(__name__)

# 修正 BASE_DIR 计算 - 指向新的数据库位置
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = str(BASE_DIR / 'db' / 'documentReview.db')

log_dir = BASE_DIR.parent.parent.parent / 'logs'
os.makedirs(log_dir, exist_ok=True)

# 防止日志重复
# 先检查是否已有处理器，如果有则清除相关处理器防止重复
if logger.hasHandlers():
    for handler in logger.handlers[:]: # 使用副本进行遍历，在删除过程中不会影响遍历
        if isinstance(handler, logging.FileHandler):
            logger.removeHandler(handler)

file_handler = logging.FileHandler(str(log_dir / 'router.log'))
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# 设置日志级别
logger.setLevel(logging.INFO)

def estimate_tokens(text: str) -> int:
    """
    使用简单快速的方法估算文本的token数量
    基于经验：1个token约等于3个字符（对于中英文混合文本）
    这个方法虽然不如tiktoken精确，但速度快且稳定
    """
    if not text:
        return 0
    return len(text) // 3

def trim_taskbook_content(taskbook_content: str, max_tokens: int = 15000, other_content: str = "") -> str:
    """
    裁剪研制任务书内容，确保总token数不超过限制
    
    Args:
        taskbook_content: 研制任务书内容
        max_tokens: 最大token限制
        other_content: 其他固定内容（已包含需求规格说明块的临时提示词）
    
    Returns:
        裁剪后的研制任务书内容
    """
    # 计算其他部分的token数
    other_tokens = estimate_tokens(other_content)
    
    # 如果其他部分已经超过限制，返回空字符串
    if other_tokens >= max_tokens:
        logger.warning(f"其他内容已超过token限制，研制任务书将被完全移除")
        return ""
    
    # 计算研制任务书可用的token数
    available_tokens = max_tokens - other_tokens
    taskbook_tokens = estimate_tokens(taskbook_content)
    
    # 如果研制任务书token数在限制内，直接返回
    if taskbook_tokens <= available_tokens:
        logger.info(f"研制任务书token数({taskbook_tokens})在限制内，无需裁剪")
        return taskbook_content
    
    # 需要裁剪，从末尾开始删除字符
    logger.info(f"需要裁剪研制任务书，当前token数: {taskbook_tokens}, 可用token数: {available_tokens}")
    
    # 二分查找最合适的裁剪长度
    left, right = 0, len(taskbook_content)
    best_length = 0
    
    while left <= right:
        mid = (left + right) // 2
        trimmed_content = taskbook_content[:mid]
        trimmed_tokens = estimate_tokens(trimmed_content)
        
        if trimmed_tokens <= available_tokens:
            best_length = mid
            left = mid + 1
        else:
            right = mid - 1
    
    trimmed_taskbook = taskbook_content[:best_length]
    final_tokens = estimate_tokens(trimmed_taskbook)
    
    logger.info(f"研制任务书裁剪完成，原长度: {len(taskbook_content)}, 裁剪后长度: {len(trimmed_taskbook)}, token数: {final_tokens}")
    
    return trimmed_taskbook

router = APIRouter()

# 全局进度字典（仅适合单机/测试环境，生产建议用Redis等持久化方案）
review_progress_dict = {}  # {session_id: {"stage": str, "percent": int, "desc": str}}

# 规则、模板和规则文件路径
template_dir = os.path.join(os.path.dirname(__file__), 'template')
prompt_dir = os.path.join(os.path.dirname(__file__), 'prompt')
rules_dir = os.path.join(os.path.dirname(__file__), 'rules')

RULES_TASKBOOK = os.path.join(rules_dir, 'taskbook_rules.json')
RULES_REQUIREMENTSPEC = os.path.join(rules_dir, 'requirementspec_rules.json')
TEMPLATE_TASKBOOK = os.path.join(template_dir, '软件研制任务书文档模板.docx')
TEMPLATE_REQUIREMENTSPEC = os.path.join(template_dir, '软件需求规格说明文档模板.docx')
PROMPT_TASKBOOK = os.path.join(prompt_dir, 'taskbook_prompt.txt')
PROMPT_REQUIREMENTSPEC = os.path.join(prompt_dir, 'requirementspec_prompt.txt')

# 真实AI审查逻辑
async def ai_review_taskbook(taskbook_content):
    """
    对研制任务书进行AI审查
    """
    log_info("开始审查研制任务书...", "ai_review_taskbook")

    # 1. 按标题分块
    chunks = split_document(taskbook_content, chunk_size=2000)
    log_info(f"总块数: {len(chunks)}", "ai_review_taskbook")

    # 2. 对每个块进行审查
    all_issues = []
    for i, chunk in enumerate(chunks, 1):
        log_info(f"\n{'='*50}", "ai_review_taskbook")
        log_info(f"处理第 {i}/{len(chunks)} 块", "ai_review_taskbook")
        log_info(f"块长度: {len(chunk)} 字符", "ai_review_taskbook")
        
        # 显示文档内容（用于调试和验证）
        if len(chunk) > 500:
            log_info(f"块内容预览:\n{chunk[:500]}...", "ai_review_taskbook")
            log_debug(f"完整内容:\n{chunk}", "ai_review_taskbook")
        else:
            log_info(f"块内容:\n{chunk}", "ai_review_taskbook")

        # 构建提示词
        prompt = compose_taskbook_prompt(
            chunk, 
            RULES_TASKBOOK, 
            TEMPLATE_TASKBOOK, 
            PROMPT_TASKBOOK, 
            chunk_index=i-1, 
            total_chunks=len(chunks)
        )

        # 调用AI进行审查
        try:
            model_output = ModelCaller.call_model(prompt=prompt)
            msg = model_output.choices[0].message

            # 优先使用 _process_model_response 解析后的结果
            if getattr(msg, 'json_content', None):
                data = msg.json_content
            else:
                raw_content = msg.content or ''
                try:
                    # 直接尝试解析 JSON 字符串
                    data = json.loads(raw_content)
                except Exception:
                    # 回退到专用解析器，获得 problems 列表
                    try:
                        problems_list = parse_taskbook_model_output(raw_content)
                        data = {"problems": problems_list}
                    except Exception as e:
                        # 最终解析失败，抛出以便外层捕获
                        raise e

            issues = data.get("problems", [])
            all_issues.extend(issues)
            log_info(f"发现 {len(issues)} 个问题", "ai_review_taskbook")
        except Exception as e:
            log_error(f"处理块 {i} 时发生错误: {str(e)}", "ai_review_taskbook", e)
            continue

    # 3. 合并和去重问题
    final_issues = merge_issues(all_issues)
    log_info(f"\n审查完成，共发现 {len(final_issues)} 个问题", "ai_review_taskbook")
    return final_issues

async def ai_review_requirementspec(requirementspec_content, taskbook_content):
    """
    对需求规格说明进行AI审查
    """
    log_info("开始审查需求规格说明...", "ai_review_requirementspec")

    # 1. 按标题分块
    chunks = split_document(requirementspec_content, chunk_size=2000)
    log_info(f"总块数: {len(chunks)}", "ai_review_requirementspec")

    # 2. 对每个块进行审查
    all_issues = []
    for i, chunk in enumerate(chunks, 1):
        log_info(f"\n{'='*50}", "ai_review_requirementspec")
        log_info(f"处理第 {i}/{len(chunks)} 块", "ai_review_requirementspec")
        log_info(f"块长度: {len(chunk)} 字符", "ai_review_requirementspec")
        
        # 显示文档内容（用于调试和验证）
        if len(chunk) > 500:
            log_info(f"块内容预览:\n{chunk[:500]}...", "ai_review_requirementspec")
            log_debug(f"完整内容:\n{chunk}", "ai_review_requirementspec")
        else:
            log_info(f"块内容:\n{chunk}", "ai_review_requirementspec")

        # 构建不包含研制任务书的临时提示词，用于计算其他部分的token数
        temp_prompt = compose_requirementspec_prompt(
            chunk, 
            "", # 暂时不包含研制任务书
            RULES_REQUIREMENTSPEC, 
            TEMPLATE_REQUIREMENTSPEC, 
            PROMPT_REQUIREMENTSPEC, 
            chunk_index=i-1, 
            total_chunks=len(chunks)
        )
        
        # 计算其他部分的token数，并裁剪研制任务书
        other_content = temp_prompt
        trimmed_taskbook = trim_taskbook_content(
            taskbook_content, 
            max_tokens=15000, 
            other_content=other_content
        )
        
        # 使用裁剪后的研制任务书构建最终提示词
        prompt = compose_requirementspec_prompt(
            chunk, 
            trimmed_taskbook, 
            RULES_REQUIREMENTSPEC, 
            TEMPLATE_REQUIREMENTSPEC, 
            PROMPT_REQUIREMENTSPEC, 
            chunk_index=i-1, 
            total_chunks=len(chunks)
        )
        
        # 记录最终提示词的token数
        final_tokens = estimate_tokens(prompt)
        log_info(f"最终提示词token数: {final_tokens}", "ai_review_requirementspec")

        # 调用AI进行审查
        try:
            model_output = ModelCaller.call_model(prompt=prompt)
            msg = model_output.choices[0].message

            # 优先使用 _process_model_response 解析后的结果
            if getattr(msg, 'json_content', None):
                data = msg.json_content
            else:
                raw_content = msg.content or ''
                try:
                    data = json.loads(raw_content)
                except Exception:
                    try:
                        problems_list = parse_violation_rules_model_output(raw_content)
                        data = {"problems": problems_list}
                    except Exception as e:
                        raise e

            issues = data.get("problems", [])
            all_issues.extend(issues)
            log_info(f"发现 {len(issues)} 个问题", "ai_review_requirementspec")
        except Exception as e:
            log_error(f"处理块 {i} 时发生错误: {str(e)}", "ai_review_requirementspec", e)
            continue

    # 3. 合并和去重问题
    final_issues = merge_issues(all_issues)
    log_info(f"\n审查完成，共发现 {len(final_issues)} 个问题", "ai_review_requirementspec")
    return final_issues

@router.post("/api/review")
async def review(background_tasks: BackgroundTasks, data: dict = Body(...)):
    """
    提交审查任务，立即返回session_id，任务后台异步执行。
    data: {
        "task_book_file_id": "...",
        "requirement_spec_file_id": "..."
    }
    """
    try:
        log_info("===== 开始处理文档审查请求 =====", "review_router")
        
        # 记录接收到的参数
        task_book_file_id = data.get('task_book_file_id')
        requirement_spec_file_id = data.get('requirement_spec_file_id')
        log_info(f"[1] 接收到的文件ID - task_book_file_id: {task_book_file_id}, requirement_spec_file_id: {requirement_spec_file_id}", "review_router")
        
        # 创建审查会话
        session_data = {"project_id": 1}  # 暂时使用固定项目ID
        # session_id = session_repo.create_session(session_data).id # 假设 session_repo 已定义
        session_id = None # 暂时不使用 session_repo
        if not session_id:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("INSERT INTO review_sessions (project_id, created_at) VALUES (?, ?)", (None, datetime.now()))
            session_id = cur.lastrowid
            conn.commit()
            conn.close()
            log_info(f"[2] 创建了新的审查会话 - session_id: {session_id}", "review_router")
        
        # 设置当前会话日志
        set_current_session(str(session_id))
        
        # 初始化进度
        review_progress_dict[session_id] = {"stage": "init", "percent": 5, "desc": "任务已提交，等待处理..."}
        # 使用 FastAPI BackgroundTasks 执行审查任务
        background_tasks.add_task(background_review_task, session_id, task_book_file_id, requirement_spec_file_id)
        log_info(f"[后台任务] 已提交 BackgroundTask，会话 ID: {session_id}", "review_router")
        
        return {"session_id": session_id}
    except Exception as e:
        log_error(f"[ERROR] 提交审查任务失败: {e}\n{traceback.format_exc()}", "review_router", e)
        raise

def background_review_task(session_id: int, task_book_file_id: int, requirement_spec_file_id: int):
    """后台审查任务"""
    # 设置当前会话日志
    set_current_session(str(session_id))
    
    try:
        log_info(f"后台审查任务开始执行，会话 ID: {session_id}", "background_task")
        review_progress_dict[session_id] = {"stage": "reading", "percent": 10, "desc": "正在读取上传文件..."}
        taskbook_content = ''
        requirementspec_content = ''
        try:
            if task_book_file_id:
                log_info(f"[文件读取] 开始读取任务书 ID: {task_book_file_id}", "background_task")
                from ..utils.file_utils import read_uploaded_file, TASK_BOOK_DIR
                
                # 1. 获取原始文档路径
                import glob
                pattern = os.path.join(TASK_BOOK_DIR, f"{task_book_file_id}_*")
                matching_files = glob.glob(pattern)
                
                if matching_files:
                    original_taskbook_path = matching_files[0]
                    log_info(f"[文档标准化] 找到原始任务书文档: {original_taskbook_path}", "background_task")
                    
                    # 2. 生成标准化文档
                    try:
                        from ..utils.spire_doc import create_standardized_document_from_single_file
                        standardized_taskbook_path = create_standardized_document_from_single_file(
                            original_taskbook_path,
                            debug_mode=True
                        )
                        log_info(f"[文档标准化] 任务书标准化完成: {standardized_taskbook_path}", "background_task")
                        
                        # 3. 读取标准化后的文档内容
                        from ..utils.file_utils import read_word_document
                        taskbook_content = read_word_document(standardized_taskbook_path)
                        log_info(f"[文件读取] 任务书标准化版本读取成功，长度: {len(taskbook_content)}", "background_task")
                        
                    except Exception as std_err:
                        log_warning(f"[文档标准化] 任务书标准化失败，使用原始文档: {std_err}", "background_task")
                        # 标准化失败时，回退到原始文档
                        taskbook_content = read_uploaded_file(task_book_file_id, 'taskBook')
                        log_info(f"[文件读取] 任务书原始版本读取成功，长度: {len(taskbook_content)}", "background_task")
                else:
                    log_warning(f"[文档标准化] 未找到任务书原始文件，使用传统读取方式", "background_task")
                    taskbook_content = read_uploaded_file(task_book_file_id, 'taskBook')
                    log_info(f"[文件读取] 任务书读取成功，长度: {len(taskbook_content)}", "background_task")
                    
            if requirement_spec_file_id:
                log_info(f"[文件读取] 开始读取需求规格说明 ID: {requirement_spec_file_id}", "background_task")
                from ..utils.file_utils import read_uploaded_file, REQUIREMENT_SPEC_DIR
                
                # 1. 获取原始文档路径
                import glob
                pattern = os.path.join(REQUIREMENT_SPEC_DIR, f"{requirement_spec_file_id}_*")
                matching_files = glob.glob(pattern)
                
                if matching_files:
                    original_reqspec_path = matching_files[0]
                    log_info(f"[文档标准化] 找到原始需求规格说明文档: {original_reqspec_path}", "background_task")
                    
                    # 2. 生成标准化文档
                    try:
                        from ..utils.spire_doc import create_standardized_document_from_single_file
                        standardized_reqspec_path = create_standardized_document_from_single_file(
                            original_reqspec_path,
                            debug_mode=True
                        )
                        log_info(f"[文档标准化] 需求规格说明标准化完成: {standardized_reqspec_path}", "background_task")
                        
                        # 3. 读取标准化后的文档内容
                        from ..utils.file_utils import read_word_document
                        requirementspec_content = read_word_document(standardized_reqspec_path)
                        log_info(f"[文件读取] 需求规格说明标准化版本读取成功，长度: {len(requirementspec_content)}", "background_task")
                        
                    except Exception as std_err:
                        log_warning(f"[文档标准化] 需求规格说明标准化失败，使用原始文档: {std_err}", "background_task")
                        # 标准化失败时，回退到原始文档
                        requirementspec_content = read_uploaded_file(requirement_spec_file_id, 'requirementSpec')
                        log_info(f"[文件读取] 需求规格说明原始版本读取成功，长度: {len(requirementspec_content)}", "background_task")
                else:
                    log_warning(f"[文档标准化] 未找到需求规格说明原始文件，使用传统读取方式", "background_task")
                    requirementspec_content = read_uploaded_file(requirement_spec_file_id, 'requirementSpec')
                    log_info(f"[文件读取] 需求规格说明读取成功，长度: {len(requirementspec_content)}", "background_task")
        except Exception as e:
            error_msg = f"读取文件失败: {str(e)}"
            log_error(f"[错误] {error_msg}\n{traceback.format_exc()}", "background_task", e)
            review_progress_dict[session_id] = {"stage": "error", "percent": 100, "desc": error_msg}
            return
        problems = []
        
        # 选择审查模式：并发或顺序
        if ENABLE_CONCURRENT_REVIEW and (taskbook_content or requirementspec_content):
            # 使用并发审查模式
            log_info(f"[并发审查] 使用并发模式进行文档审查，会话 ID: {session_id}，并发数: {AI_CONCURRENT_REQUESTS}", "background_task")
            try:
                import asyncio
                from .concurrent_review import ai_review_documents_concurrent
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                all_problems = loop.run_until_complete(ai_review_documents_concurrent(
                    taskbook_content=taskbook_content,
                    requirementspec_content=requirementspec_content,
                    session_id=session_id
                ))
                
                problems.extend(all_problems)
                log_info(f"[并发审查] 审查完成，总共发现 {len(all_problems)} 个问题", "background_task")
                
            except Exception as e:
                error_msg = f"并发审查失败: {str(e)}"
                log_error(f"[错误] {error_msg}\n{traceback.format_exc()}", "background_task", e)
                review_progress_dict[session_id] = {"stage": "error", "percent": 100, "desc": error_msg}
                return
        else:
            # 使用原有的顺序审查模式
            log_info(f"[顺序审查] 使用顺序模式进行文档审查，会话 ID: {session_id}", "background_task")
            
            # 先审查任务书
            if taskbook_content:
                review_progress_dict[session_id] = {"stage": "taskbook", "percent": 20, "desc": "正在审查研制任务书..."}
                try:
                    import asyncio
                    log_info(f"[审查任务书] 开始审查任务书，会话 ID: {session_id}", "background_task")
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    taskbook_problems = loop.run_until_complete(ai_review_taskbook(taskbook_content))
                    log_info(f"[审查任务书] 审查完成，发现 {len(taskbook_problems)} 个问题", "background_task")
                    review_progress_dict[session_id] = {"stage": "taskbook", "percent": 40, "desc": "研制任务书审查完成"}
                    problems.extend(taskbook_problems)
                except Exception as e:
                    error_msg = f"任务书审查失败: {str(e)}"
                    log_error(f"[错误] {error_msg}\n{traceback.format_exc()}", "background_task", e)
                    review_progress_dict[session_id] = {"stage": "error", "percent": 100, "desc": error_msg}
                    return
            # 再审查需求规格说明
            if requirementspec_content:
                review_progress_dict[session_id] = {"stage": "requirementspec", "percent": 50, "desc": "正在审查需求规格说明..."}
                try:
                    import asyncio
                    log_info(f"[审查需求规格] 开始审查需求规格说明，会话 ID: {session_id}", "background_task")
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    requirementspec_problems = loop.run_until_complete(ai_review_requirementspec(requirementspec_content, taskbook_content))
                    log_info(f"[审查需求规格] 审查完成，发现 {len(requirementspec_problems)} 个问题", "background_task")
                    review_progress_dict[session_id] = {"stage": "requirementspec", "percent": 80, "desc": "需求规格说明审查完成"}
                    problems.extend(requirementspec_problems)
                except Exception as e:
                    error_msg = f"需求规格说明审查失败: {str(e)}"
                    log_error(f"[错误] {error_msg}\n{traceback.format_exc()}", "background_task", e)
                    review_progress_dict[session_id] = {"stage": "error", "percent": 100, "desc": error_msg}
                    return
        # 写入数据库
        try:
            review_progress_dict[session_id] = {"stage": "integrating", "percent": 90, "desc": "正在整合分析结果..."}
            log_info(f"[数据库写入] 开始将 {len(problems)} 个问题写入数据库，会话 ID: {session_id}", "background_task")
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            for item in problems:
                cur.execute("""
                    INSERT INTO review_results (
                      session_id, doc_type, doc_name, requirement_content, violation_rules, issue_level, issue_name, issue_location,
                      description_requirement, description_issue, description_location, description_impact
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_id, item.get('doc_type',''), item.get('doc_name',''), item.get('requirement_content',''), item.get('violation_rules',''),
                    item.get('issue_level', '一般问题'), item.get('issue_name',''), item.get('issue_location',''),
                    item.get('description_requirement',''), item.get('description_issue',''),
                    item.get('description_location',''), item.get('description_impact','')
                ))
            conn.commit()
            conn.close()
            log_info(f"[数据库写入] 所有问题已成功写入数据库，会话 ID: {session_id}", "background_task")
            
            # ===== 生成批注版Word文档 =====
            try:
                log_info(f"[批注生成] 开始生成批注版文档，会话 ID: {session_id}", "background_task")
                
                # 准备临时输出目录
                temp_dir = os.path.join(BASE_DIR.parent.parent.parent.parent, 'temp', 'annotated_documents')
                os.makedirs(temp_dir, exist_ok=True)
                
                # 分别为研制任务书和需求规格说明生成批注版文档
                annotated_paths = {}
                
                # 分类问题
                taskbook_issues = [item for item in problems if item.get('doc_type') == 'taskBook']
                requirementspec_issues = [item for item in problems if item.get('doc_type') == 'requirementSpec']
                
                # 生成研制任务书批注版文档
                if task_book_file_id and taskbook_issues:
                    try:
                        from ..utils.file_utils import TASK_BOOK_DIR
                        import glob
                        
                        # 找到原始文档路径
                        pattern = os.path.join(TASK_BOOK_DIR, f"{task_book_file_id}_*")
                        matching_files = glob.glob(pattern)
                        
                        if matching_files:
                            original_taskbook_path = matching_files[0]
                            
                            # 使用 Spire.Doc 添加批注
                            try:
                                from ..annotator.spire_commenter import add_comments_to_document_spire
                                annotated_path = add_comments_to_document_spire(
                                    original_taskbook_path, 
                                    taskbook_issues, 
                                    temp_dir, 
                                    session_id,
                                    'taskBook'
                                )
                                annotated_paths['taskBook'] = annotated_path
                                log_info(f"[批注生成] 使用Spire.Doc生成研制任务书批注版: {annotated_path}", "background_task")
                            except Exception as spire_err:
                                log_error(f"[批注生成] Spire.Doc批注失败: {spire_err}", "background_task", exc_info=True)
                        else:
                            log_warning(f"[批注生成] 未找到研制任务书原始文件: {task_book_file_id}", "background_task")
                    except Exception as tb_err:
                        log_error(f"[批注生成] 生成研制任务书批注版失败: {tb_err}", "background_task", exc_info=True)
                
                # 生成需求规格说明批注版文档
                if requirement_spec_file_id and requirementspec_issues:
                    try:
                        from ..utils.file_utils import REQUIREMENT_SPEC_DIR
                        import glob
                        
                        # 找到原始文档路径
                        pattern = os.path.join(REQUIREMENT_SPEC_DIR, f"{requirement_spec_file_id}_*")
                        matching_files = glob.glob(pattern)
                        
                        if matching_files:
                            original_requirementspec_path = matching_files[0]
                            
                            # 使用 Spire.Doc 添加批注
                            try:
                                from ..annotator.spire_commenter import add_comments_to_document_spire
                                annotated_path = add_comments_to_document_spire(
                                    original_requirementspec_path, 
                                    requirementspec_issues, 
                                    temp_dir, 
                                    session_id,
                                    'requirementSpec'
                                )
                                annotated_paths['requirementSpec'] = annotated_path
                                log_info(f"[批注生成] 使用Spire.Doc生成需求规格说明批注版: {annotated_path}", "background_task")
                            except Exception as spire_err:
                                log_error(f"[批注生成] Spire.Doc批注失败: {spire_err}", "background_task", exc_info=True)
                        else:
                            log_warning(f"[批注生成] 未找到需求规格说明原始文件: {requirement_spec_file_id}", "background_task")
                    except Exception as rs_err:
                        log_error(f"[批注生成] 生成需求规格说明批注版失败: {rs_err}", "background_task", exc_info=True)
                
                # 将批注文件路径存储到数据库中，方便后续下载
                # 不管是否生成了批注文件，都需要更新数据库
                conn = sqlite3.connect(DB_PATH)
                cur = conn.cursor()
                
                # 检查表是否有annotated_paths字段，如果没有则添加
                cur.execute("PRAGMA table_info(review_sessions)")
                columns = [column[1] for column in cur.fetchall()]
                if 'annotated_taskbook_path' not in columns:
                    cur.execute("ALTER TABLE review_sessions ADD COLUMN annotated_taskbook_path TEXT")
                if 'annotated_requirementspec_path' not in columns:
                    cur.execute("ALTER TABLE review_sessions ADD COLUMN annotated_requirementspec_path TEXT")
                
                # 更新批注文件路径
                taskbook_path = annotated_paths.get('taskBook', "")
                requirementspec_path = annotated_paths.get('requirementSpec', "")
                cur.execute("""
                    UPDATE review_sessions 
                    SET annotated_taskbook_path = ?, annotated_requirementspec_path = ? 
                    WHERE id = ?
                """, (taskbook_path, requirementspec_path, session_id))
                conn.commit()
                conn.close()
                log_info(f"[批注生成] 批注文件路径已存储到数据库 - 研制任务书: {taskbook_path}, 需求规格说明: {requirementspec_path}", "background_task")
                
            except Exception as ann_err:
                log_error(f"[批注生成] 生成批注版Word文档失败: {ann_err}", "background_task", exc_info=True)
            
            review_progress_dict[session_id] = {"stage": "done", "percent": 100, "desc": "AI审查完成"}
            log_info(f"[AI审查] 整个审查流程完成，会话 ID: {session_id}", "background_task")
        except Exception as e:
            error_msg = f"写入数据库失败: {str(e)}"
            log_error(f"[错误] {error_msg}\n{traceback.format_exc()}", "background_task", e)
            review_progress_dict[session_id] = {"stage": "error", "percent": 100, "desc": error_msg}
            return
    except Exception as e:
        error_msg = f"任务执行异常: {str(e)}"
        log_error(f"[错误] {error_msg}\n{traceback.format_exc()}", "background_task", e)
        review_progress_dict[session_id] = {"stage": "error", "percent": 100, "desc": error_msg}
        return


# 新增：进度查询接口
@router.get("/api/review/progress")
def get_review_progress(session_id: int = Query(...)):
    progress = review_progress_dict.get(session_id)
    if not progress:
        return JSONResponse(content={"stage": "not_found", "percent": 0, "desc": "未找到该session_id的进度"})
    return JSONResponse(content=progress)
