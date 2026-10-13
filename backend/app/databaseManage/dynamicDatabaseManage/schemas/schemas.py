from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime


class OptoelectronicRequirementBase(BaseModel):
    """光电需求分析基础模式"""
    software_category: str = Field(..., description="软件类别")
    test_item_name: str = Field(..., description="测试项名称")
    test_item_description: Optional[str] = Field(None, description="测试项描述")
    test_method: Optional[str] = Field(None, description="测试方法")


class OptoelectronicRequirementCreate(OptoelectronicRequirementBase):
    """创建光电需求分析记录的模式"""
    pass


class OptoelectronicRequirementUpdate(BaseModel):
    """更新光电需求分析记录的模式"""
    software_category: Optional[str] = Field(None, description="软件类别")
    test_item_name: Optional[str] = Field(None, description="测试项名称")
    test_item_description: Optional[str] = Field(None, description="测试项描述")
    test_method: Optional[str] = Field(None, description="测试方法")


class OptoelectronicRequirement(OptoelectronicRequirementBase):
    """光电需求分析记录完整模式"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OptoelectronicRequirementBatch(BaseModel):
    """批量导入的模式"""
    requirements: List[OptoelectronicRequirementCreate]


class RequirementBatchUpdateItem(BaseModel):
    """批量更新条目：指定 id 与要更新的字段"""
    id: int
    update: OptoelectronicRequirementUpdate


class RequirementBatchUpdate(BaseModel):
    """批量更新请求体"""
    items: List[RequirementBatchUpdateItem]


class RequirementBatchDelete(BaseModel):
    """批量删除请求体"""
    ids: List[int]


class CellUpdate(BaseModel):
    """单元格更新：指定字段和值"""
    field: str = Field(..., description="要更新的字段名，如 test_item_name")
    value: Optional[str] = Field(None, description="更新后的值")


# ================= 智能导入相关模型 =================
class IntelligentImportSuggestion(BaseModel):
    """智能导入：后端给前端的建议项"""
    index: int = Field(..., description="导入表的原始行序(从0开始)")
    incoming: OptoelectronicRequirementCreate
    suggestion_type: Literal["append_columns", "create_new"]
    matched_id: Optional[int] = None
    matched_name: Optional[str] = None
    matched_category: Optional[str] = None
    confidence: float = Field(ge=0, le=1)
    rationale: Optional[str] = None


class IntelligentImportDecision(BaseModel):
    """前端确认后的决策项，用于最终提交入库"""
    suggestion_type: Literal["append_columns", "create_new"]
    matched_id: Optional[int] = Field(None, description="若是追加列，需提供匹配到的现有记录ID")
    incoming: OptoelectronicRequirementCreate


# ================= 多Sheet七列表通用 Schema =================
class SevenColRequirementBase(BaseModel):
    """通用七列表基础模式（适用于转塔/对抗告警/光雷/吊舱四表）"""
    software_category: str = Field(..., description="软件类别")
    test_item_name: str = Field(..., description="测试项名称")
    test_content: Optional[str] = Field(None, description="测试内容")
    test_method: Optional[str] = Field(None, description="测试方法")
    case_template_name: Optional[str] = Field(None, description="用例模板（用例名称）")
    case_template_input: Optional[str] = Field(None, description="用例模板（输入条件）")
    case_template_expected: Optional[str] = Field(None, description="用例模板（预期结果）")
    submitter: Optional[str] = Field(None, description="提交人")


class SevenColRequirementCreate(SevenColRequirementBase):
    """创建七列表记录"""
    pass


class SevenColRequirementUpdate(BaseModel):
    """更新七列表记录"""
    software_category: Optional[str] = None
    test_item_name: Optional[str] = None
    test_content: Optional[str] = None
    test_method: Optional[str] = None
    case_template_name: Optional[str] = None
    case_template_input: Optional[str] = None
    case_template_expected: Optional[str] = None
    submitter: Optional[str] = None


class SevenColRequirementOut(SevenColRequirementBase):
    """七列表输出模式（含通用元字段）"""
    id: int
    category_order: Optional[int] = None
    item_order: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True