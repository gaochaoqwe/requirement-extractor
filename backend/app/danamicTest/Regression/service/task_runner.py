"""
动态测试-回归测试任务执行器
负责异步执行回归测试任务并记录详细日志
"""
import uuid
import asyncio
import time
from typing import Dict, Any
from pathlib import Path

from ..utils.logging_utils.logger import set_current_task, log_info, log_error, log_warning, finalize_task_log
from ..utils.logging_utils.performance_monitor import start_task_monitoring, end_task_monitoring, monitor_step, RegressionTestSteps
from ..main import RegressionTestManager

# 全局任务状态存储
task_status = {}

def clear_all_tasks():
    """清理所有任务状态（服务重启时调用）"""
    global task_status
    task_status.clear()
    from ..utils.logging_utils.logger import log_info
    log_info("已清理所有任务状态", "task_manager")

def generate_task_id() -> str:
    """生成唯一的任务ID"""
    return str(uuid.uuid4())

async def run_regression_test_task(
    session_id: str,
    basic_info: Dict[str, Any],
    ai_analysis: bool = True,
    deep_analysis: bool = True,
    task_id: str = None
) -> str:
    """
    执行回归测试任务（后台任务）
    
    Args:
        session_id: 会话ID
        basic_info: 基本信息
        ai_analysis: 是否启用AI分析
        deep_analysis: 是否启用深度分析
        task_id: 任务ID（如果未提供则生成新的）
        
    Returns:
        str: 任务ID
    """
    # 使用提供的任务ID或生成新的任务ID
    if task_id is None:
        task_id = generate_task_id()
    
    # 初始化任务状态
    task_status[task_id] = {
        "status": "running",
        "progress": 0,
        "message": "任务初始化中...",
        "session_id": session_id,
        "start_time": None,
        "end_time": None,
        "generated_files": [],
        "error": None
    }
    
    try:
        # 设置当前任务日志
        set_current_task(task_id, session_id)
        log_info(f"开始执行回归测试任务", "task_manager")
        log_info(f"任务参数: session_id={session_id}, ai_analysis={ai_analysis}, deep_analysis={deep_analysis}", "task_manager")
        
        # 启动性能监控
        start_task_monitoring("回归测试任务")
        
        # 更新任务状态
        task_status[task_id]["start_time"] = str(time.time())
        task_status[task_id]["progress"] = 10
        task_status[task_id]["message"] = "正在初始化回归测试管理器..."
        
        # 创建回归测试管理器
        with monitor_step(RegressionTestSteps.INIT, "创建回归测试管理器"):
            log_info("创建回归测试管理器", "task_manager")
            regression_manager = RegressionTestManager()
        
        # 更新进度
        task_status[task_id]["progress"] = 20
        task_status[task_id]["message"] = "正在验证会话和文件..."
        
        # 验证会话目录是否存在
        with monitor_step(RegressionTestSteps.VALIDATE_INPUT, "验证会话目录和输入文件"):
            session_dir = Path(f"uploads/dynamic/regression/{session_id}")
            if not session_dir.exists():
                raise FileNotFoundError(f"会话目录不存在: {session_dir}")
            
            log_info(f"会话目录验证通过: {session_dir}", "task_manager")
            
            # 查找影响域分析报告
            impact_files = list(session_dir.glob("impact_*"))
            if not impact_files:
                raise FileNotFoundError("未找到影响域分析报告")
            
            impact_file_path = str(impact_files[0])
            log_info(f"影响域分析报告路径: {impact_file_path}", "task_manager")
            
            # 查找上传的代码文件（支持zip或其他代码文件）
            code_files = []
            code_files.extend(list(session_dir.glob("*.zip")))  # zip文件
            code_files.extend(list(session_dir.glob("*.py")))   # Python文件
            code_files.extend(list(session_dir.glob("*.c")))    # C文件
            code_files.extend(list(session_dir.glob("*.cpp")))  # C++文件
            code_files.extend(list(session_dir.glob("*.h")))    # 头文件
            
            code_file_path = None
            if code_files:
                code_file_path = str(code_files[0])  # 使用第一个找到的代码文件
                log_info(f"找到代码文件: {code_file_path}", "task_manager")
            else:
                log_info("未找到上传的代码文件，将使用传入的代码行数", "task_manager")
        
        # 更新进度
        task_status[task_id]["progress"] = 30
        task_status[task_id]["message"] = "正在分析影响域文档..."
        
        # 调用回归测试生成
        with monitor_step(RegressionTestSteps.BUILD_FORMS, "执行完整回归测试表单生成流程"):
            log_info("开始调用回归测试管理器生成表单", "task_manager")
            
            # 构建用户软件信息
            user_software_info = {
                'software_name': basic_info.get('software_name', ''),
                'software_version': basic_info.get('software_version', ''),
                'software_id': basic_info.get('software_id', ''),
                'domain': basic_info.get('domain', ''),
                'detector_flag': basic_info.get('detector_flag', '有检测仪'),
                # 添加可选信息
                'aircraft_model': basic_info.get('aircraft_model', ''),
                'project_director': basic_info.get('project_director', ''),
                'development_department': basic_info.get('development_department', ''),
                'chief_designer': basic_info.get('chief_designer', '')
            }
            log_info(f"用户软件信息: {user_software_info}", "task_manager")
            
            result = await regression_manager.generate_complete_forms(
                input_path=impact_file_path,
                test_manager=basic_info.get('test_manager', ''),
                test_personnel=basic_info.get('test_personnel', ''),
                developer=basic_info.get('developer', ''),
                domain=basic_info.get('domain', ''),
                ai_analysis=ai_analysis,
                deep_analysis=deep_analysis,
                user_software_info=user_software_info,
                code_file_path=code_file_path,
                code_lines=basic_info.get('code_lines')
            )
        
        # 更新进度
        task_status[task_id]["progress"] = 90
        task_status[task_id]["message"] = "正在整理生成结果..."
        
        with monitor_step(RegressionTestSteps.SAVE_RESULTS, "整理和保存生成结果"):
            log_info(f"回归测试表单生成完成，结果: {result}", "task_manager")
        
        # 更新最终状态
        task_status[task_id]["status"] = "completed"
        task_status[task_id]["progress"] = 100
        task_status[task_id]["message"] = "任务完成"
        task_status[task_id]["end_time"] = str(time.time())
        task_status[task_id]["generated_files"] = result.get("generated_files", [])
        
        log_info("回归测试任务完成", "task_manager")
        
        # 结束性能监控
        end_task_monitoring("回归测试任务")
        
    except Exception as e:
        log_error(f"回归测试任务失败", "task_manager", e)
        
        # 更新错误状态
        task_status[task_id]["status"] = "failed"
        task_status[task_id]["progress"] = 0
        task_status[task_id]["message"] = f"任务失败: {str(e)}"
        task_status[task_id]["error"] = str(e)
        task_status[task_id]["end_time"] = str(time.time())
        
    finally:
        # 完成日志记录
        finalize_task_log()
    
    return task_id

def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    获取任务状态
    
    Args:
        task_id: 任务ID
        
    Returns:
        Dict[str, Any]: 任务状态信息
    """
    return task_status.get(task_id, {
        "status": "not_found",
        "progress": 0,
        "message": "任务不存在",
        "error": "Task not found"
    })

def cleanup_completed_tasks():
    """
    清理已完成的任务状态（可选，用于内存管理）
    """
    completed_tasks = [
        task_id for task_id, status in task_status.items()
        if status["status"] in ["completed", "failed"]
    ]
    
    # 保留最近100个任务，清理更早的任务
    if len(completed_tasks) > 100:
        tasks_to_remove = completed_tasks[:-100]
        for task_id in tasks_to_remove:
            del task_status[task_id]
            log_info(f"清理任务状态: {task_id}", "task_manager") 