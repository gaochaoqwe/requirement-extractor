"""
数据库基类

所有模型都应该从这里导入 Base，确保使用同一个 Base 实例
"""
from sqlalchemy.ext.declarative import declarative_base

# 创建统一的 Base 类
Base = declarative_base()

