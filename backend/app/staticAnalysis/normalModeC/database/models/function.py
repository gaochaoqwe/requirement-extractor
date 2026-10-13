"""
分析函数模型
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from ..base import Base

class AnalysisFunction(Base):
    """分析函数模型"""
    __tablename__ = 'nm_analysis_functions'
    
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey('nm_analysis_files.id', ondelete='CASCADE'), nullable=False)
    function_name = Column(String(255), nullable=False)
    start_line = Column(Integer, nullable=False)
    end_line = Column(Integer, nullable=False)
    source_code = Column(Text, nullable=False)
    analyzed = Column(Boolean, default=False)
    file_path = Column(String(512), nullable=True)  # 在ZIP包中的相对路径
    
    # AI生成的附加信息字段
    function_description = Column(Text, nullable=True)  # AI生成的函数功能描述
    commented_code = Column(Text, nullable=True)  # AI生成的注释后代码
    
    # 关联关系
    file = relationship("AnalysisFile", back_populates="functions")
    problems = relationship("AnalysisProblem", back_populates="function", cascade="all, delete-orphan")
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'file_id': self.file_id,
            'function_name': self.function_name,
            'start_line': self.start_line,
            'end_line': self.end_line,
            'analyzed': self.analyzed,
            'file_path': self.file_path,
            'function_description': self.function_description,
            'commented_code': self.commented_code,
            'source_code': self.source_code[:200] + '...' if self.source_code and len(self.source_code) > 200 else self.source_code
        }
