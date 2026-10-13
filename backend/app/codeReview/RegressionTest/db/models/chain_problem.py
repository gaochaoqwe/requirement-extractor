"""
链路审查问题模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from ..database import Base

class ChainReviewProblem(Base):
    """链路审查问题模型 - 专门用于链路级业务审查结果"""
    __tablename__ = 'regression_test_chain_problems'
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey('regression_test_tasks.id', ondelete='CASCADE'), nullable=False)
    
    # 链路信息
    chain_name = Column(String(255), nullable=False)  # 链路名称（简短英文名称）
    chain_function_description = Column(Text, nullable=True)  # 链路功能描述（详细英文描述）
    entry_function = Column(String(255), nullable=True)  # 入口函数
    affected_functions = Column(Text, nullable=True)  # 影响的函数列表（JSON格式）
    call_chain = Column(Text, nullable=True)  # 调用链路顺序（例如："funcA → funcB → funcC"）
    implementation_description = Column(Text, nullable=True)  # 功能实现说明
    related_files = Column(Text, nullable=True)  # 相关文件
    related_functions = Column(Text, nullable=True)  # 相关函数
    code_locations = Column(Text, nullable=True)  # 代码位置信息
    
    # 问题核心信息
    issue_name = Column(String(255), nullable=False)  # 问题名称
    issue_level = Column(String(50), nullable=False, default='建议')  # 严重|一般|建议
    issue_location = Column(String(255), nullable=True)  # 问题位置
    
    # 问题详细描述
    file_name = Column(String(255), nullable=True)  # 主要文件名
    function_name = Column(String(255), nullable=True)  # 主要函数名
    line = Column(Integer, nullable=True)  # 问题所在行号（用于代码定位）
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
            'chain_name': self.chain_name,
            'chain_function_description': self.chain_function_description,
            'entry_function': self.entry_function,
            'affected_functions': self.affected_functions,
            'call_chain': self.call_chain,
            'implementation_description': self.implementation_description,
            'related_files': self.related_files,
            'related_functions': self.related_functions,
            'code_locations': self.code_locations,
            'issue_name': self.issue_name,
            'issue_level': self.issue_level,
            'issue_location': self.issue_location,
            'file_name': self.file_name,
            'function_name': self.function_name,
            'line': self.line,
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
            '链路名称': self.chain_name,
            '链路功能': self.chain_function_description,
            '入口函数': self.entry_function,
            '问题名称': self.issue_name,
            '严重程度': self.issue_level,
            '问题位置': self.issue_location,
            '文件名': self.file_name,
            '问题原因': self.problem_reason,
            '需求描述': self.description_requirement,
            '问题描述': self.description_issue,
            '位置描述': self.description_location,
            '影响分析': self.description_impact,
            '业务规则': self.business_rule,
            '改进建议': self.suggestion,
            '软件类型': self.software_type,
            '领域': self.domain,
            '影响函数': self.affected_functions,
            '创建时间': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
        } 