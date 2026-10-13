"""
AI静态分析统一入口

提供AIClient的导出，用于其他模块导入。
"""
from .openai.client import AIClient

__all__ = ["AIClient"]
