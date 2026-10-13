from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class DashboardConfig(Base):
    """仪表板顶层配置（测评类型，如配置项测试、鉴定测评）"""
    __tablename__ = "dashboard_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="配置名称，如：配置项测试、鉴定测评")
    description = Column(Text, nullable=True, comment="描述")
    is_active = Column(Boolean, default=True, comment="是否激活")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    phases = relationship("PhaseConfig", back_populates="dashboard", cascade="all, delete-orphan", order_by="PhaseConfig.order_index")


class PhaseConfig(Base):
    """阶段配置（文档审查、静态分析、代码审查、动态测试、报告编写）"""
    __tablename__ = "phase_configs"

    id = Column(Integer, primary_key=True, index=True)
    dashboard_id = Column(Integer, ForeignKey("dashboard_configs.id"), nullable=False)
    name = Column(String(100), nullable=False, comment="阶段名称")
    order_index = Column(Integer, nullable=False, default=0, comment="排序")
    weight = Column(Float, nullable=False, default=20.0, comment="工作量权重百分比")
    automation_level = Column(Float, nullable=False, default=0.0, comment="自动化程度 0~100")
    icon = Column(String(50), nullable=True, comment="图标标识")
    color = Column(String(20), nullable=True, comment="主题色")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    dashboard = relationship("DashboardConfig", back_populates="phases")
    sub_steps = relationship("SubStepConfig", back_populates="phase", cascade="all, delete-orphan", order_by="SubStepConfig.order_index")


class SubStepConfig(Base):
    """子步骤配置（如问题发现、编写问题单）"""
    __tablename__ = "sub_step_configs"

    id = Column(Integer, primary_key=True, index=True)
    phase_id = Column(Integer, ForeignKey("phase_configs.id"), nullable=False)
    name = Column(String(200), nullable=False, comment="子步骤名称")
    order_index = Column(Integer, nullable=False, default=0, comment="排序")
    weight = Column(Float, nullable=False, default=50.0, comment="在本阶段内的权重百分比")
    automation_level = Column(Float, nullable=False, default=0.0, comment="自动化程度 0~100")
    description = Column(Text, nullable=True, comment="步骤描述")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    phase = relationship("PhaseConfig", back_populates="sub_steps")
