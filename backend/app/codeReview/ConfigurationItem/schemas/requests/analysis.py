"""
静态分析API的请求和响应模型
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class AnalysisResult(BaseModel):
    """
    分析结果模型
    """
    file_id: int
    task_id: int
    problems: List[Dict[str, Any]]
    summary: Dict[str, int]  # 例如: {"critical": 1, "high": 2, "medium": 3, "low": 4}
