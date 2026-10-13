"""
函数仓库
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from ..models.function import AnalysisFunction
from ..models.problem import AnalysisProblem
from ..models.file import AnalysisFile

class FunctionRepository:
    """函数仓库类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_function(self, function_data: Dict[str, Any]) -> AnalysisFunction:
        """创建函数记录"""
        func = AnalysisFunction(**function_data)
        self.db.add(func)
        self.db.commit()
        self.db.refresh(func)
        return func

    def get_or_create_function(self, function_data: Dict[str, Any]) -> AnalysisFunction:
        """按 file_id + file_path + function_name + 行号 获取或创建函数记录。"""
        existing = self.db.query(AnalysisFunction).filter(
            AnalysisFunction.file_id == function_data.get("file_id"),
            AnalysisFunction.file_path == function_data.get("file_path"),
            AnalysisFunction.function_name == function_data.get("function_name"),
            AnalysisFunction.start_line == function_data.get("start_line"),
            AnalysisFunction.end_line == function_data.get("end_line"),
        ).first()
        if existing:
            return existing

        func = AnalysisFunction(**function_data)
        self.db.add(func)
        self.db.commit()
        self.db.refresh(func)
        return func
    
    def batch_create_functions(self, functions_data: List[Dict[str, Any]]) -> List[AnalysisFunction]:
        """批量创建函数记录"""
        functions = [AnalysisFunction(**data) for data in functions_data]
        self.db.bulk_save_objects(functions)
        self.db.commit()
        return functions
    
    def get_function(self, function_id: int) -> Optional[AnalysisFunction]:
        """获取函数详情"""
        return self.db.query(AnalysisFunction).filter(
            AnalysisFunction.id == function_id
        ).first()
    
    def update_function_analyzed(self, function_id: int, analyzed: bool = True) -> bool:
        """更新函数分析状态"""
        func = self.get_function(function_id)
        if not func:
            return False
            
        func.analyzed = analyzed
        self.db.commit()
        return True
    
    def update_function_info(self, function_id: int, function_description: str = None, commented_code: str = None) -> bool:
        """更新函数信息（描述和注释后代码）"""
        func = self.get_function(function_id)
        if not func:
            return False
            
        if function_description is not None:
            func.function_description = function_description
        if commented_code is not None:
            func.commented_code = commented_code
            
        self.db.commit()
        return True
    
    def get_functions_by_file(self, file_id: int, analyzed: bool = None) -> List[AnalysisFunction]:
        """获取文件下的所有函数，可选按分析状态过滤"""
        query = self.db.query(AnalysisFunction).filter(
            AnalysisFunction.file_id == file_id
        )
        
        if analyzed is not None:
            query = query.filter(AnalysisFunction.analyzed == analyzed)
            
        return query.all()
    
    def get_function_by_file_and_name(self, file_id: int, function_name: str) -> Optional[AnalysisFunction]:
        """根据文件ID和函数名称获取函数"""
        return self.db.query(AnalysisFunction).filter(
            AnalysisFunction.file_id == file_id,
            AnalysisFunction.function_name == function_name
        ).first()
    
    def get_function_with_problems(self, function_id: int) -> Optional[Dict[str, Any]]:
        """获取函数及其问题"""
        func = self.db.query(AnalysisFunction).options(
            joinedload(AnalysisFunction.problems)
        ).filter(
            AnalysisFunction.id == function_id
        ).first()
        
        if not func:
            return None
            
        result = func.to_dict()
        result['problems'] = [p.to_dict() for p in func.problems]
        return result

    def get_functions_by_task(self, task_id: int) -> List[AnalysisFunction]:
        """按任务ID获取该任务下的所有函数记录

        供任务恢复逻辑使用，用于判断哪些函数已经处理过。
        """
        # 通过文件表的 task_id 进行关联查询
        return (
            self.db.query(AnalysisFunction)
            .join(AnalysisFile, AnalysisFunction.file_id == AnalysisFile.id)
            .filter(AnalysisFile.task_id == task_id)
            .all()
        )
