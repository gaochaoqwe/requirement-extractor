"""
函数仓库
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from ..models.function import AnalysisFunction
from ..models.problem import AnalysisProblem

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
        """更新函数的AI生成信息"""
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
