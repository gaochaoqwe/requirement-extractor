from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class TestEnvironmentSession(Base):
    __tablename__ = "test_environment_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(50), unique=True, index=True, nullable=False)
    软件名称 = Column(String(255), nullable=False)
    检测仪名称 = Column(String(255), nullable=False)
    软件运行设备 = Column(String(255), nullable=False)
    接口1 = Column(String(255), nullable=False)
    接口2 = Column(String(255), nullable=False)
    目标模拟器 = Column(String(255), nullable=True)  # 可选字段
    主控软件名称 = Column(String(255), nullable=True)  # 分系统模式下使用
    主控与被测软件接口类型 = Column(String(255), nullable=True)  # 分系统模式下使用
    status = Column(String(20), default="pending")  # pending, processing, completed, error
    diagram_data = Column(Text, nullable=True)  # JSON格式的图表数据
    description = Column(Text, nullable=True)  # 生成的环境描述
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 