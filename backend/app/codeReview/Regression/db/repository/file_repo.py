"""
文件仓库
"""
from typing import List, Optional, Dict, Any
import os
from sqlalchemy.orm import Session
from ..models.file import AnalysisFile
from ..models.function import AnalysisFunction
from ..models.problem import AnalysisProblem
from ...utils.logger import log_error

class FileRepository:
    """文件仓库类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_file(self, file_data: Dict[str, Any]) -> AnalysisFile:
        """创建文件记录"""
        # 添加文件大小和类型信息
        if 'file_path' in file_data and os.path.exists(file_data['file_path']):
            file_data['file_size'] = os.path.getsize(file_data['file_path'])
            # 若调用方未显式指定 file_type，则根据后缀推断；否则保留调用方的逻辑类型（old/new/report/merged）
            if 'file_type' not in file_data or not file_data['file_type']:
                file_data['file_type'] = os.path.splitext(file_data['file_path'])[1].lower()
        
        file = AnalysisFile(**file_data)
        self.db.add(file)
        self.db.commit()
        self.db.refresh(file)
        return file
    
    def get_file(self, file_id: int) -> Optional[AnalysisFile]:
        """获取文件详情"""
        return self.db.query(AnalysisFile).filter(AnalysisFile.id == file_id).first()
    
    def update_file_status(self, file_id: int, status: str, **kwargs) -> Optional[AnalysisFile]:
        """更新文件状态"""
        file = self.get_file(file_id)
        if not file:
            return None
            
        file.status = status
        for key, value in kwargs.items():
            if hasattr(file, key):
                setattr(file, key, value)
                
        self.db.commit()
        self.db.refresh(file)
        return file
    
    def delete_file(self, file_id: int) -> bool:
        """删除文件（级联删除相关函数和问题）"""
        file = self.get_file(file_id)
        if not file:
            return False
            
        # 删除实际文件和解压目录
        try:
            if file.file_path and os.path.exists(file.file_path):
                os.remove(file.file_path)
            if file.extract_path and os.path.exists(file.extract_path):
                import shutil
                shutil.rmtree(file.extract_path, ignore_errors=True)
        except Exception as e:
            log_error(f"删除文件时出错", "file_repo", e)
            
        self.db.delete(file)
        self.db.commit()
        return True
    
    def list_files_by_task(self, task_id: int) -> List[AnalysisFile]:
        """获取任务下的所有文件"""
        return self.db.query(AnalysisFile).filter(AnalysisFile.task_id == task_id).all()
    
    def get_file_functions(self, file_id: int) -> List[AnalysisFunction]:
        """获取文件中的所有函数"""
        return self.db.query(AnalysisFunction).filter(
            AnalysisFunction.file_id == file_id
        ).all()
    
    def get_file_problems(self, file_id: int) -> List[Dict[str, Any]]:
        """获取文件的所有问题"""
        problems = self.db.query(
            AnalysisProblem,
            AnalysisFunction.function_name
        ).join(
            AnalysisFunction, AnalysisFunction.id == AnalysisProblem.function_id
        ).filter(
            AnalysisProblem.file_id == file_id
        ).all()
        
        result = []
        for problem, func_name in problems:
            problem_dict = problem.to_dict()
            problem_dict['function_name'] = func_name
            result.append(problem_dict)
            
        return result
