"""
用例设计（testCaseAssistant）数据库模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class CaseDesignTask(Base):
    """用例设计任务表：用于绑定 Excel / 代码库 / AI生成过程"""

    __tablename__ = "case_design_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    status = Column(String(32), default="created")

    product_type = Column(String(128), nullable=True)
    software_type = Column(String(128), nullable=True)

    excel_filename = Column(String(255), nullable=True)
    extra = Column(Text, nullable=True)  # 预留：存JSON字符串

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class CaseDesignRepo(Base):
    """代码库记录：zip上传与解压结果"""

    __tablename__ = "case_design_repos"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(64), index=True, nullable=False)

    zip_path = Column(Text, nullable=False)
    extract_path = Column(Text, nullable=False)

    file_count = Column(Integer, default=0)
    total_size = Column(Integer, default=0)
    index_status = Column(String(32), default="not_indexed")

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())