# 回归测试AI审查主路由
from fastapi import APIRouter, HTTPException, Body, Query, BackgroundTasks
from fastapi.responses import JSONResponse
import uuid
import json
import os
import sqlite3
import logging
import traceback
import sys
import time
from datetime import datetime
from app.utils.log_utils import log_once, log_with_interval
from .prompt.compose_impactreport_prompt import compose_impactreport_prompt
from .openai.openai_api import ModelCaller
from .analysis.analysis_impactreport import parse_impact_report_model_output

# 导入日志系统
from ..utils.logger import (
    set_current_session, clear_current_session, log_debug, log_info,
    log_warning, log_error
)

# 设置日志
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# 添加文件处理器
log_dir = os.path.join(os.path.dirname(__file__), '../../../../logs')
os.makedirs(log_dir, exist_ok=True)

# 防止日志重复
# 先检查是否已有处理器，如果有则清除所有处理器防止重复
if logger.hasHandlers():
    for handler in logger.handlers[:]: # 使用副本进行遍历，在删除过程中不会影响遍历
        if isinstance(handler, logging.FileHandler):
            logger.removeHandler(handler)

file_handler = logging.FileHandler(os.path.join(log_dir, 'regression_router.log'))
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

router = APIRouter()
from pathlib import Path

# 修正 BASE_DIR 计算 - 指向新的数据库位置
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = str(BASE_DIR / 'db' / 'regressionReview.db')

# 提示词文件路径
prompt_dir = os.path.join(os.path.dirname(__file__), 'prompt')
PROMPT_IMPACTREPORT = os.path.join(prompt_dir, 'impactreport_prompt.txt')

# 全局进度字典
regression_progress_dict = {}  # {session_id: {"stage": str, "percent": int, "desc": str}}

# 回归测试审查入口
@router.post("/api/regression/review")
async def review(background_tasks: BackgroundTasks, data: dict = Body(...)):
    """
    提交回归测试审查任务，立即返回session_id，任务后台异步执行。
    data: {
        "impact_report_file_id": "..."
    }
    """
    try:
        log_info("===== 开始处理回归测试审查请求 =====", "review_router")
        
        # 记录接收到的参数
        impact_report_file_id = data.get('impact_report_file_id')
        log_info(f"接收到的文件ID - impact_report_file_id: {impact_report_file_id}", "review_router")
        
        # 创建审查会话
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("INSERT INTO review_sessions (project_id, created_at) VALUES (?, ?)", (None, datetime.now()))
        session_id = cur.lastrowid
        conn.commit()
        conn.close()
        
        # 设置当前会话日志
        set_current_session(str(session_id))
        
        log_info(f"创建了新的审查会话 - session_id: {session_id}", "review_router")
        
        # 初始化进度
        regression_progress_dict[session_id] = {"stage": "init", "percent": 5, "desc": "任务已提交，等待处理..."}
        
        # 使用 FastAPI BackgroundTasks 执行审查任务
        background_tasks.add_task(background_review_task, session_id, impact_report_file_id)
        
        return {"session_id": session_id}
    except Exception as e:
        log_error(f"提交审查任务失败", "review_router", e)
        raise HTTPException(status_code=500, detail=f"提交审查任务失败: {str(e)}")

# 真实AI审查逻辑
async def ai_review_impactreport(impact_report_content):
    """实际进行影响域分析报告AI审查"""
    try:
        # 组合提示词
        prompt = compose_impactreport_prompt(
            impact_report_content,
            PROMPT_IMPACTREPORT
        )
        
        # 调用模型
        log_info("开始调用AI模型进行影响域分析报告审查", "ai_review")
        model_output = ModelCaller.call_model(prompt=prompt)
        
        # 记录模型返回对象的完整信息
        log_info(f"模型返回对象类型: {type(model_output).__name__}", "ai_review")
        if hasattr(model_output, '__dict__'):
            log_info(f"模型返回对象属性: {model_output.__dict__.keys()}", "ai_review")
        
        # 特别检查 choices 字段
        has_choices = hasattr(model_output, 'choices')
        log_info(f"是否包含 choices 字段: {has_choices}", "ai_review")
        
        if has_choices and model_output.choices:
            log_info(f"choices 长度: {len(model_output.choices)}", "ai_review")
            log_info(f"choices[0] 类型: {type(model_output.choices[0]).__name__}", "ai_review")
            
            if hasattr(model_output.choices[0], 'message'):
                log_info(f"message 类型: {type(model_output.choices[0].message).__name__}", "ai_review")
                message_attrs = [attr for attr in dir(model_output.choices[0].message) if not attr.startswith('_')]
                log_info(f"message 属性: {message_attrs}", "ai_review")
                
                if hasattr(model_output.choices[0].message, 'content'):
                    content_preview = model_output.choices[0].message.content[:100] + '...' if len(model_output.choices[0].message.content) > 100 else model_output.choices[0].message.content
                    log_info(f"message.content 预览: {content_preview}", "ai_review")
        
        # 检查返回结果
        if not hasattr(model_output, 'choices') or not model_output.choices:
            log_error("模型返回结果格式异常: 缺少 choices 字段", "ai_review")
            raise HTTPException(status_code=500, detail="模型返回结果格式异常")
            
        if not hasattr(model_output.choices[0], 'message') or not hasattr(model_output.choices[0].message, 'json_content'):
            log_error("模型返回结果格式异常: 缺失必要字段", "ai_review")
            # 试图处理缺少json_content的情况
            if hasattr(model_output.choices[0], 'message') and hasattr(model_output.choices[0].message, 'content'):
                try:
                    content = model_output.choices[0].message.content
                    log_info(f"尝试从 message.content 解析JSON: {content[:100]}...", "ai_review")
                    json_content = json.loads(content)
                    # 手动添加json_content属性
                    model_output.choices[0].message.json_content = json_content
                    log_info("成功从 message.content 解析JSON", "ai_review")
                except Exception as json_err:
                    log_error(f"无法从 message.content 解析JSON: {json_err}", "ai_review")
                    raise HTTPException(status_code=500, detail="模型返回结果格式异常")
            else:
                raise HTTPException(status_code=500, detail="模型返回结果格式异常")
        
        # 返回解析后的结果
        return parse_impact_report_model_output(model_output.choices[0].message.json_content)
    except Exception as e:
        log_error(f"AI审查过程中出错", "ai_review", e)
        return {"problems": [{
            "doc_type": "regression",
            "doc_name": "影响域分析报告",
            "requirement_content": "",
            "violation_rules": "",
            "issue_name": "AI审查失败",
            "issue_location": "",
            "description_requirement": "",
            "description_issue": f"审查过程中出错: {str(e)}",
            "description_location": "",
            "description_impact": "无法完成审查"
        }]}

def background_review_task(session_id, impact_report_file_id):
    """后台审查任务"""
    # 设置当前会话日志
    set_current_session(str(session_id))
    
    try:
        from ..utils.file_utils import read_uploaded_file
        
        # 记录任务开始
        log_info(f"后台审查任务开始执行 - 会话 ID: {session_id}", "background_task")
        
        # 更新进度
        regression_progress_dict[session_id] = {"stage": "reading", "percent": 10, "desc": "正在读取影响域分析报告..."}
        log_info(f"开始读取文件 - impact_report_file_id: {impact_report_file_id}", "background_task")
        
        # 文档标准化和读取
        report_content = ''
        try:
            # 1. 获取原始文档路径
            from ..utils.file_utils import UPLOAD_ROOT
            import glob
            pattern = os.path.join(UPLOAD_ROOT, f"{impact_report_file_id}_*")
            matching_files = glob.glob(pattern)
            
            if matching_files:
                original_report_path = matching_files[0]
                log_info(f"[文档标准化] 找到原始影响域分析报告: {original_report_path}", "background_task")
                
                # 2. 生成标准化文档
                try:
                    from ..utils.spire_doc import create_standardized_document_from_single_file
                    standardized_report_path = create_standardized_document_from_single_file(
                        original_report_path,
                        debug_mode=True
                    )
                    log_info(f"[文档标准化] 影响域分析报告标准化完成: {standardized_report_path}", "background_task")
                    
                    # 3. 读取标准化后的文档内容
                    from ..utils.file_utils import read_word_document
                    report_content = read_word_document(standardized_report_path)
                    log_info(f"[文件读取] 影响域分析报告标准化版本读取成功，长度: {len(report_content)}", "background_task")
                    
                except Exception as std_err:
                    log_warning(f"[文档标准化] 影响域分析报告标准化失败，使用原始文档: {std_err}", "background_task")
                    # 标准化失败时，回退到原始文档
                    report_content = read_uploaded_file(impact_report_file_id)
                    log_info(f"[文件读取] 影响域分析报告原始版本读取成功，长度: {len(report_content)}", "background_task")
            else:
                log_warning(f"[文档标准化] 未找到影响域分析报告原始文件，使用传统读取方式", "background_task")
                report_content = read_uploaded_file(impact_report_file_id)
                log_info(f"[文件读取] 影响域分析报告读取成功，长度: {len(report_content)}", "background_task")
            
            # 记录内容摘要便于调试
            content_preview = report_content[:200] + '...' if len(report_content) > 200 else report_content
            log_info(f"文件内容预览: {content_preview}", "background_task")
        except Exception as e:
            error_msg = f"读取文件时出错: {str(e)}"
            log_error(error_msg, "background_task", e)
            regression_progress_dict[session_id] = {"stage": "error", "percent": 100, "desc": error_msg}
            return
        
        # 更新进度
        regression_progress_dict[session_id] = {"stage": "reviewing", "percent": 30, "desc": "AI正在分析影响域报告..."}
        
        # 调用AI进行审查
        import asyncio
        review_result = asyncio.run(ai_review_impactreport(report_content))
        
        # 获取审查结果中的问题
        problems = review_result.get("problems", [])
        # 更新进度
        regression_progress_dict[session_id] = {"stage": "integrating", "percent": 90, "desc": "正在整合分析结果..."}
        
        # 记录找到的问题数
        problem_count = len(problems)
        log_info(f"影响域分析报告审查发现 {problem_count} 个问题", "background_task")
        
        # 写入数据库
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            
            # 先检查是否已存在该session_id的结果
            cur.execute("SELECT COUNT(*) FROM regression_results WHERE session_id = ?", (session_id,))
            if cur.fetchone()[0] > 0:
                # 如果存在，先删除旧结果
                cur.execute("DELETE FROM regression_results WHERE session_id = ?", (session_id,))
                log_info(f"已清除session_id={session_id}的旧结果", "background_task")
            
            # 插入新结果
            for item in problems:
                cur.execute("""
                    INSERT INTO regression_results (
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
            
            # ===== 生成批注版Word文档 =====
            try:
                log_info(f"开始生成批注版影响域分析报告，会话 ID: {session_id}", "background_task")
                
                # 准备临时输出目录
                temp_dir = os.path.join(BASE_DIR.parent.parent.parent.parent, 'temp', 'annotated_documents')
                os.makedirs(temp_dir, exist_ok=True)
                
                # 生成影响域分析报告批注版文档
                if impact_report_file_id and problems:
                    try:
                        import glob
                        
                        # 找到原始文档路径
                        from ..utils.file_utils import UPLOAD_ROOT
                        pattern = os.path.join(UPLOAD_ROOT, f"{impact_report_file_id}_*")
                        matching_files = glob.glob(pattern)
                        
                        if matching_files:
                            original_impactreport_path = matching_files[0]
                            
                            # 使用 Spire.Doc 添加批注
                            try:
                                from ..annotator.spire_commenter import add_comments_to_document_spire
                                annotated_path = add_comments_to_document_spire(
                                    original_impactreport_path, 
                                    problems, 
                                    temp_dir, 
                                    session_id,
                                    'impactReport'
                                )
                                log_info(f"使用Spire.Doc生成影响域分析报告批注版: {annotated_path}", "background_task")
                                
                                # 将批注文件路径存储到数据库中
                                conn = sqlite3.connect(DB_PATH)
                                cur = conn.cursor()
                                
                                # 检查表是否有annotated_impactreport_path字段，如果没有则添加
                                cur.execute("PRAGMA table_info(review_sessions)")
                                columns = [column[1] for column in cur.fetchall()]
                                if 'annotated_impactreport_path' not in columns:
                                    cur.execute("ALTER TABLE review_sessions ADD COLUMN annotated_impactreport_path TEXT")
                                
                                # 更新批注文件路径
                                cur.execute("""
                                    UPDATE review_sessions 
                                    SET annotated_impactreport_path = ? 
                                    WHERE id = ?
                                """, (annotated_path, session_id))
                                conn.commit()
                                conn.close()
                                log_info(f"批注文件路径已存储到数据库", "background_task")
                                
                            except Exception as spire_err:
                                log_error(f"Spire.Doc批注失败", "background_task", spire_err)
                        else:
                            log_warning(f"未找到影响域分析报告原始文件: {impact_report_file_id}", "background_task")
                            log_warning(f"查找模式: {pattern}", "background_task")
                    except Exception as ir_err:
                        log_error(f"生成影响域分析报告批注版失败", "background_task", ir_err)
                
            except Exception as ann_err:
                log_error(f"生成批注版Word文档失败", "background_task", ann_err)
            
            # 更新最终状态
            completion_message = "AI审查完成" if problem_count > 0 else "AI审查完成，未发现问题"
            regression_progress_dict[session_id] = {"stage": "done", "percent": 100, "desc": completion_message}
            log_info(f"Session {session_id} 审查完成: {completion_message}", "background_task")
        except Exception as e:
            log_error(f"写入数据库失败", "background_task", e)
            regression_progress_dict[session_id] = {"stage": "error", "percent": 100, "desc": f"写入数据库失败: {str(e)}"}
            return
    except Exception as e:
        regression_progress_dict[session_id] = {"stage": "error", "percent": 100, "desc": f"任务执行异常: {str(e)}"}
        return

# 进度查询接口
# 使用全局日志工具提供的log_with_interval函数控制进度查询日志

@router.get("/api/regression/review/progress")
def get_review_progress(session_id: int = Query(...)):
    progress = regression_progress_dict.get(session_id)
    
    if not progress:
        # 使用全局日志工具提供的log_with_interval函数控制日志频率
        log_with_interval(logger.warning, f"[进度查询] 未找到 session_id: {session_id} 的进度信息", f"progress_not_found_{session_id}", 30)
        return JSONResponse(content={"stage": "not_found", "percent": 0, "desc": "未找到该session_id的进度"})
    
    return JSONResponse(content=progress)
