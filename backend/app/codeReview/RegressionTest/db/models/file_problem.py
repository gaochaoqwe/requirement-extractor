"""
文件审查问题模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from ..database import Base

class FileReviewProblem(Base):
    """文件审查问题模型 - 专门用于文件级业务审查结果"""
    __tablename__ = 'regression_test_file_problems'
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey('regression_test_tasks.id', ondelete='CASCADE'), nullable=False)
    
    # 文件信息
    file_name = Column(String(255), nullable=False)  # 文件名
    file_path = Column(String(500), nullable=True)  # 文件路径
    
    # 问题核心信息
    issue_name = Column(String(255), nullable=False)  # 问题名称
    issue_level = Column(String(50), nullable=False, default='建议')  # 严重|一般|建议
    issue_location = Column(String(255), nullable=True)  # 问题位置
    
    # 问题详细描述
    source_code = Column(Text, nullable=True)  # 相关源代码
    problem_reason = Column(Text, nullable=True)  # 问题原因
    description_requirement = Column(Text, nullable=True)  # 需求描述
    description_issue = Column(Text, nullable=True)  # 问题描述
    description_location = Column(Text, nullable=True)  # 问题位置描述
    description_impact = Column(Text, nullable=True)  # 影响描述
    
    # 业务相关信息
    business_rule = Column(Text, nullable=True)  # 违反的业务规则
    suggestion = Column(Text, nullable=True)  # 改进建议
    
    # 分类信息
    software_type = Column(String(255), nullable=True)  # 软件类型
    domain = Column(String(255), nullable=True)  # 领域
    
    created_at = Column(DateTime, default=datetime.now)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'file_name': self.file_name,
            'file_path': self.file_path,
            'issue_name': self.issue_name,
            'issue_level': self.issue_level,
            'issue_location': self.issue_location,
            'source_code': self.source_code,
            'problem_reason': self.problem_reason,
            'description_requirement': self.description_requirement,
            'description_issue': self.description_issue,
            'description_location': self.description_location,
            'description_impact': self.description_impact,
            'business_rule': self.business_rule,
            'suggestion': self.suggestion,
            'software_type': self.software_type,
            'domain': self.domain,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    def to_excel_dict(self):
        """转换为Excel导出格式"""
        return {
            '文件名': self.file_name,
            '文件路径': self.file_path,
            '问题名称': self.issue_name,
            '严重程度': self.issue_level,
            '问题位置': self.issue_location,
            '问题原因': self.problem_reason,
            '需求描述': self.description_requirement,
            '问题描述': self.description_issue,
            '位置描述': self.description_location,
            '影响分析': self.description_impact,
            '业务规则': self.business_rule,
            '改进建议': self.suggestion,
            '软件类型': self.software_type,
            '领域': self.domain,
            '创建时间': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
        } 