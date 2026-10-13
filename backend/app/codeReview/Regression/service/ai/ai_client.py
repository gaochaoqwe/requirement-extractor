"""
AI静态分析统一入口

注意：此模块已过时，请直接导入 analysis_runner 中的内容。
"""
import warnings
from .analysis_runner import AIClient, run_static_analysis

warnings.warn(
    "ai_client 模块已过时，请直接导入 analysis_runner 中的内容。",
    DeprecationWarning,
    stacklevel=2
)

__all__ = ["AIClient", "run_static_analysis"]
