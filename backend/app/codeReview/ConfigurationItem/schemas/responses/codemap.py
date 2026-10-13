"""
代码地图响应模型
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class BaseResponse(BaseModel):
    """基础响应模型"""
    success: bool
    message: str


class CodeMapResponse(BaseResponse):
    """代码地图响应模型"""
    data: Dict[str, Any]


class NodeDetailResponse(BaseResponse):
    """节点详情响应模型"""
    data: Dict[str, Any]


class ProblemsResponse(BaseResponse):
    """问题列表响应模型"""
    data: List[Dict[str, Any]]


class SearchResponse(BaseResponse):
    """搜索结果响应模型"""
    data: List[Dict[str, Any]]


class StatisticsResponse(BaseResponse):
    """统计信息响应模型"""
    data: Dict[str, Any] 