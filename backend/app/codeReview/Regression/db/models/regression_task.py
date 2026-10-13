"""
回归测试任务模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON
from datetime import datetime
from ..database import Base

class RegressionTask(Base):
    """回归测试任务模型"""
    __tablename__ = "regression_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_task_id = Column(String(50), nullable=False, index=True)  # 分析任务ID
    task_id = Column(String(50), nullable=False, index=True)  # 任务编号（如：1, 2, 3）
    task_name = Column(String(200), nullable=False)
    task_description = Column(Text)
    change_type = Column(String(50))  # requirement, design, code, combined
    
    # 新增字段：影响域分析报告中对应此任务的原始内容
    original_report_content = Column(Text, nullable=True)  # 影响域分析报告中对应此任务的原始内容
    
    # 任务状态和进度
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    progress = Column(Float, default=0.0)
    
    # 任务结果
    result = Column(Text)  # 审查结果的JSON字符串
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 