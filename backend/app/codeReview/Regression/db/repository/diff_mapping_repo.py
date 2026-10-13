"""
代码差异映射Repository
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.diff_mapping import DiffMapping


class DiffMappingRepository:
    """代码差异映射Repository"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_mapping(self, mapping_data: Dict[str, Any]) -> DiffMapping:
        """
        创建新的差异映射
        
        Args:
            mapping_data: 映射数据
            
        Returns:
            DiffMapping: 创建的映射对象
        """
        mapping = DiffMapping(
            analysis_task_id=mapping_data["analysis_task_id"],
            task_id=mapping_data["task_id"],
            file_path=mapping_data["file_path"],
            function_name=mapping_data.get("function_name"),
            change_type=mapping_data.get("change_type"),
            old_code=mapping_data.get("old_code"),
            new_code=mapping_data.get("new_code"),
            diff_summary=mapping_data.get("diff_summary"),
            mapping_confidence=mapping_data.get("mapping_confidence", "low"),
            mapping_reason=mapping_data.get("mapping_reason", ""),
            mapping_score=mapping_data.get("mapping_score", 0.0),
            mentioned_in_report=mapping_data.get("mentioned_in_report", "no")
        )
        
        self.db.add(mapping)
        self.db.flush()
        return mapping
    
    def batch_create_mappings(self, mappings_data: List[Dict[str, Any]]) -> List[DiffMapping]:
        """
        批量创建差异映射
        
        Args:
            mappings_data: 映射数据列表
            
        Returns:
            List[DiffMapping]: 创建的映射对象列表
        """
        mappings = []
        for mapping_data in mappings_data:
            mapping = DiffMapping(
                analysis_task_id=mapping_data["analysis_task_id"],
                task_id=mapping_data["task_id"],
                file_path=mapping_data["file_path"],
                function_name=mapping_data.get("function_name"),
                change_type=mapping_data.get("change_type"),
                old_code=mapping_data.get("old_code"),
                new_code=mapping_data.get("new_code"),
                diff_summary=mapping_data.get("diff_summary"),
                mapping_confidence=mapping_data.get("mapping_confidence", "low"),
                mapping_reason=mapping_data.get("mapping_reason", ""),
                mapping_score=mapping_data.get("mapping_score", 0.0),
                mentioned_in_report=mapping_data.get("mentioned_in_report", "no")
            )
            mappings.append(mapping)
        
        self.db.add_all(mappings)
        self.db.flush()
        return mappings
    
    def get_mappings_by_analysis_id(self, analysis_task_id: str) -> List[DiffMapping]:
        """
        根据分析任务ID获取所有映射
        
        Args:
            analysis_task_id: 分析任务ID
            
        Returns:
            List[DiffMapping]: 映射列表
        """
        return self.db.query(DiffMapping).filter(
            DiffMapping.analysis_task_id == analysis_task_id
        ).all()
    
    def get_mappings_by_task_id(self, analysis_task_id: str, task_id: str) -> List[DiffMapping]:
        """
        根据分析任务ID和任务ID获取映射
        
        Args:
            analysis_task_id: 分析任务ID
            task_id: 任务ID
            
        Returns:
            List[DiffMapping]: 映射列表
        """
        return self.db.query(DiffMapping).filter(
            and_(
                DiffMapping.analysis_task_id == analysis_task_id,
                DiffMapping.task_id == task_id
            )
        ).all()
    
    def get_mappings_by_file(self, analysis_task_id: str, file_path: str) -> List[DiffMapping]:
        """
        根据分析任务ID和文件路径获取映射
        
        Args:
            analysis_task_id: 分析任务ID
            file_path: 文件路径
            
        Returns:
            List[DiffMapping]: 映射列表
        """
        return self.db.query(DiffMapping).filter(
            and_(
                DiffMapping.analysis_task_id == analysis_task_id,
                DiffMapping.file_path == file_path
            )
        ).all()
    
    def delete_mappings_by_analysis_id(self, analysis_task_id: str) -> int:
        """
        删除指定分析任务的所有映射
        
        Args:
            analysis_task_id: 分析任务ID
            
        Returns:
            int: 删除的记录数
        """
        count = self.db.query(DiffMapping).filter(
            DiffMapping.analysis_task_id == analysis_task_id
        ).count()
        
        self.db.query(DiffMapping).filter(
            DiffMapping.analysis_task_id == analysis_task_id
        ).delete()
        
        return count 