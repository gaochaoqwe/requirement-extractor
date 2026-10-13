"""
代码差异映射模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON
from datetime import datetime
from ..database import Base

class DiffMapping(Base):
    """代码差异映射模型"""
    __tablename__ = "diff_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_task_id = Column(String(50), nullable=False, index=True)  # 分析任务ID
    task_id = Column(String(50), nullable=False, index=True)  # 关联的任务ID
    
    # 文件和函数信息
    file_path = Column(String(500), nullable=False)
    function_name = Column(String(200))
    change_type = Column(String(50))  # added, modified, deleted
    
    # 差异内容
    old_code = Column(Text)  # 旧版本代码
    new_code = Column(Text)  # 新版本代码
    diff_summary = Column(Text)  # 差异摘要
    
    # 映射信息
    mapping_confidence = Column(String(20))  # high, medium, low
    mapping_reason = Column(Text)  # 映射原因说明
    mapping_score = Column(Float, default=0.0)  # 映射置信度分数
    
    # 是否在影响域分析报告中提及
    mentioned_in_report = Column(String(10), default="no")  # yes, no, partial
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow) 