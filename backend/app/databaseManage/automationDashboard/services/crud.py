from sqlalchemy.orm import Session
from typing import List, Optional
from ..db.models import DashboardConfig, PhaseConfig, SubStepConfig
from ..schemas.schemas import (
    DashboardConfigCreate, DashboardConfigUpdate,
    PhaseCreate, PhaseUpdate,
    SubStepCreate, SubStepUpdate,
)


# ─── DashboardConfig CRUD ───────────────────────────────────────────────────

def get_all_configs(db: Session) -> List[DashboardConfig]:
    return db.query(DashboardConfig).order_by(DashboardConfig.id).all()


def get_config(db: Session, config_id: int) -> Optional[DashboardConfig]:
    return db.query(DashboardConfig).filter(DashboardConfig.id == config_id).first()


def create_config(db: Session, data: DashboardConfigCreate) -> DashboardConfig:
    cfg = DashboardConfig(name=data.name, description=data.description, is_active=data.is_active)
    db.add(cfg)
    db.flush()
    for ph_data in data.phases:
        _create_phase(db, cfg.id, ph_data)
    db.commit()
    db.refresh(cfg)
    return cfg


def update_config(db: Session, config_id: int, data: DashboardConfigUpdate) -> Optional[DashboardConfig]:
    cfg = get_config(db, config_id)
    if not cfg:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(cfg, field, value)
    db.commit()
    db.refresh(cfg)
    return cfg


def delete_config(db: Session, config_id: int) -> bool:
    cfg = get_config(db, config_id)
    if not cfg:
        return False
    db.delete(cfg)
    db.commit()
    return True


# ─── PhaseConfig CRUD ───────────────────────────────────────────────────────

def get_phases(db: Session, config_id: int) -> List[PhaseConfig]:
    return (
        db.query(PhaseConfig)
        .filter(PhaseConfig.dashboard_id == config_id)
        .order_by(PhaseConfig.order_index)
        .all()
    )


def get_phase(db: Session, phase_id: int) -> Optional[PhaseConfig]:
    return db.query(PhaseConfig).filter(PhaseConfig.id == phase_id).first()


def _calc_phase_automation(sub_steps) -> float:
    """根据子步骤的权重和自动化程度加权计算阶段自动化程度。
    权重之和不为100时按比例归一化；无子步骤时返回None（由调用方决定用原值）。
    """
    if not sub_steps:
        return None
    total_weight = sum(ss.weight for ss in sub_steps)
    if total_weight <= 0:
        return 0.0
    return sum(ss.automation_level * (ss.weight / total_weight) for ss in sub_steps)


def _create_phase(db: Session, config_id: int, data: PhaseCreate) -> PhaseConfig:
    # 先计算子步骤的自动化程度，再决定阶段的值
    calculated = _calc_phase_automation(data.sub_steps) if data.sub_steps else None
    ph = PhaseConfig(
        dashboard_id=config_id,
        name=data.name,
        order_index=data.order_index,
        weight=data.weight,
        automation_level=calculated if calculated is not None else data.automation_level,
        icon=data.icon,
        color=data.color,
    )
    db.add(ph)
    db.flush()
    for ss_data in data.sub_steps:
        _create_sub_step(db, ph.id, ss_data)
    return ph


def add_phase(db: Session, config_id: int, data: PhaseCreate) -> PhaseConfig:
    ph = _create_phase(db, config_id, data)
    db.commit()
    db.refresh(ph)
    return ph


def update_phase(db: Session, phase_id: int, data: PhaseUpdate) -> Optional[PhaseConfig]:
    ph = get_phase(db, phase_id)
    if not ph:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(ph, field, value)
    db.commit()
    db.refresh(ph)
    return ph


def delete_phase(db: Session, phase_id: int) -> bool:
    ph = get_phase(db, phase_id)
    if not ph:
        return False
    db.delete(ph)
    db.commit()
    return True


def bulk_replace_phases(db: Session, config_id: int, phases_data: List[PhaseCreate]) -> DashboardConfig:
    """清空原有阶段并重新写入"""
    cfg = get_config(db, config_id)
    if not cfg:
        raise ValueError(f"Config {config_id} not found")
    for ph in list(cfg.phases):
        db.delete(ph)
    db.flush()
    for ph_data in phases_data:
        _create_phase(db, config_id, ph_data)
    db.commit()
    db.refresh(cfg)
    return cfg


# ─── SubStepConfig CRUD ─────────────────────────────────────────────────────

def get_sub_steps(db: Session, phase_id: int) -> List[SubStepConfig]:
    return (
        db.query(SubStepConfig)
        .filter(SubStepConfig.phase_id == phase_id)
        .order_by(SubStepConfig.order_index)
        .all()
    )


def get_sub_step(db: Session, sub_step_id: int) -> Optional[SubStepConfig]:
    return db.query(SubStepConfig).filter(SubStepConfig.id == sub_step_id).first()


def _create_sub_step(db: Session, phase_id: int, data: SubStepCreate) -> SubStepConfig:
    ss = SubStepConfig(
        phase_id=phase_id,
        name=data.name,
        order_index=data.order_index,
        weight=data.weight,
        automation_level=data.automation_level,
        description=data.description,
    )
    db.add(ss)
    return ss


def add_sub_step(db: Session, phase_id: int, data: SubStepCreate) -> SubStepConfig:
    ss = _create_sub_step(db, phase_id, data)
    db.commit()
    db.refresh(ss)
    return ss


def update_sub_step(db: Session, sub_step_id: int, data: SubStepUpdate) -> Optional[SubStepConfig]:
    ss = get_sub_step(db, sub_step_id)
    if not ss:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(ss, field, value)
    db.commit()
    db.refresh(ss)
    return ss


def delete_sub_step(db: Session, sub_step_id: int) -> bool:
    ss = get_sub_step(db, sub_step_id)
    if not ss:
        return False
    db.delete(ss)
    db.commit()
    return True


def bulk_replace_sub_steps(db: Session, phase_id: int, steps_data: List[SubStepCreate]) -> PhaseConfig:
    """清空原有子步骤并重新写入"""
    ph = get_phase(db, phase_id)
    if not ph:
        raise ValueError(f"Phase {phase_id} not found")
    for ss in list(ph.sub_steps):
        db.delete(ss)
    db.flush()
    for ss_data in steps_data:
        _create_sub_step(db, phase_id, ss_data)
    db.commit()
    db.refresh(ph)
    return ph
