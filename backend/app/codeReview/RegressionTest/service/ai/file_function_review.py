"""
文件+函数集成审查模块

自动识别项目类型（C/C++或FPGA）并调用相应的审查流程
"""
from typing import Dict, Any
from pathlib import Path

from .analysis_runner import run_code_review
from ...utils.logger import log_info


class FileFunctionReviewer:
    """文件+函数集成审查器（自动识别项目类型：C/C++或FPGA）"""
    
    def __init__(self, task_id: int, project_root: str, file_id: int, entry_function: str = 'main', tester_name: str = None):
        """
        初始化审查器
        
        Args:
            task_id: 任务ID
            project_root: 项目根目录
            file_id: 文件ID
            entry_function: 入口函数名称（暂时不使用，未来可用于优化）
            tester_name: 测试人员姓名
        """
        self.task_id = task_id
        self.file_id = file_id
        self.project_root = Path(project_root)
        self.entry_function = entry_function
        self.tester_name = tester_name
        
    def run_review(self) -> Dict[str, Any]:
        """
        运行文件+函数集成审查
        
        自动识别项目类型（C/C++、FPGA或混合），并调用相应的审查流程
        
        Returns:
            审查结果统计
        """
        log_info(f"[函数审查] 开始，任务ID: {self.task_id}", "file_function_review")
        log_info(f"[函数审查] 自动识别项目类型（支持C/C++和FPGA）", "file_function_review")
        
        # 获取数据库会话（使用智能切换模块）
        from ...config_database import get_db
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            # 调用主审查流程（会自动识别项目类型并调用相应的审查函数）
            # - 如果是C/C++项目：调用 run_c_cpp_code_review
            # - 如果是FPGA项目：调用 run_fpga_code_review
            # - 如果是混合项目：优先处理C/C++
            run_code_review(self.file_id, self.task_id, db, tester_name=self.tester_name)
            
            log_info(f"[函数审查] 审查完成，任务ID: {self.task_id}", "file_function_review")
            
            return {
                "status": "completed",
                "message": "函数审查已完成"
            }
        
        finally:
            try:
                db.close()
            except:
                pass
