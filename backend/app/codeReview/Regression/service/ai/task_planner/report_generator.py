"""
回归测试审查报告生成器
"""
import os
from datetime import datetime
from typing import Dict, Any
from sqlalchemy.orm import Session


def log_debug(msg):
    """记录调试日志"""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.abspath(os.path.join(base_dir, '..', '..', '..', '..', '..', '..'))
        log_dir = os.path.join(backend_dir, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, 'bg_debug.txt')
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass


def generate_regression_report(
    db: Session,
    analysis_task_id: str,
    task_id: int,
    file_id: int,
    impact_report_content: str
) -> Dict[str, Any]:
    """
    生成回归测试审查报告
    
    注意：现在报告直接从数据库生成Excel，不再需要预生成文件
    
    Args:
        db: 数据库会话
        analysis_task_id: 分析任务ID
        task_id: 任务ID
        file_id: 文件ID
        impact_report_content: 影响域分析报告内容
        
    Returns:
        Dict[str, Any]: 生成结果
    """
    result = {
        "success": True,
        "message": "报告数据已保存到数据库，可通过下载接口获取Excel报告",
        "report_path": None
    }
    
    try:
        log_debug(f"[ReportGenerator] 报告数据已准备完成，task_id={task_id}")
        log_debug(f"[ReportGenerator] 用户可通过 /download_report/{task_id} 接口下载Excel报告")
        
        return result
        
    except Exception as e:
        log_debug(f"[ERROR] 报告生成时出错: {e}")
        result["success"] = False
        result["message"] = f"报告生成时出错: {str(e)}"
        return result 