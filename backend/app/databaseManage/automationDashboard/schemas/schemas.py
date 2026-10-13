from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class SubStepBase(BaseModel):
    name: str
    order_index: int = 0
    weight: float = Field(50.0, ge=0, le=100)
    automation_level: float = Field(0.0, ge=0, le=100)
    description: Optional[str] = None


class SubStepCreate(SubStepBase):
    pass


class SubStepUpdate(BaseModel):
    name: Optional[str] = None
    order_index: Optional[int] = None
    weight: Optional[float] = Field(None, ge=0, le=100)
    automation_level: Optional[float] = Field(None, ge=0, le=100)
    description: Optional[str] = None


class SubStepOut(SubStepBase):
    id: int
    phase_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PhaseBase(BaseModel):
    name: str
    order_index: int = 0
    weight: float = Field(20.0, ge=0, le=100)
    automation_level: float = Field(0.0, ge=0, le=100)
    icon: Optional[str] = None
    color: Optional[str] = None


class PhaseCreate(PhaseBase):
    sub_steps: List[SubStepCreate] = []


class PhaseUpdate(BaseModel):
    name: Optional[str] = None
    order_index: Optional[int] = None
    weight: Optional[float] = Field(None, ge=0, le=100)
    automation_level: Optional[float] = Field(None, ge=0, le=100)
    icon: Optional[str] = None
    color: Optional[str] = None


class PhaseOut(PhaseBase):
    id: int
    dashboard_id: int
    sub_steps: List[SubStepOut] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DashboardConfigBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True


class DashboardConfigCreate(DashboardConfigBase):
    phases: List[PhaseCreate] = []


class DashboardConfigUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class DashboardConfigOut(DashboardConfigBase):
    id: int
    phases: List[PhaseOut] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DashboardConfigSummary(DashboardConfigBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BulkUpdatePhases(BaseModel):
    """批量更新阶段配置（含子步骤完整替换）"""
    phases: List[PhaseCreate]


class BulkUpdateSubSteps(BaseModel):
    """批量替换某阶段的子步骤"""
    sub_steps: List[SubStepCreate]
