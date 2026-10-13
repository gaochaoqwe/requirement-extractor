from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..db import get_db
from ..schemas.schemas import (
    DashboardConfigCreate, DashboardConfigUpdate,
    DashboardConfigOut, DashboardConfigSummary,
    PhaseCreate, PhaseUpdate, PhaseOut,
    SubStepCreate, SubStepUpdate, SubStepOut,
    BulkUpdatePhases, BulkUpdateSubSteps,
)
from ..services import crud

router = APIRouter(prefix="/automation-dashboard", tags=["Automation Dashboard"])


# ─── Dashboard Configs ───────────────────────────────────────────────────────

@router.get("/configs", response_model=List[DashboardConfigSummary])
def list_configs(db: Session = Depends(get_db)):
    return crud.get_all_configs(db)


@router.get("/configs/{config_id}", response_model=DashboardConfigOut)
def get_config(config_id: int, db: Session = Depends(get_db)):
    cfg = crud.get_config(db, config_id)
    if not cfg:
        raise HTTPException(status_code=404, detail="配置不存在")
    return cfg


@router.post("/configs", response_model=DashboardConfigOut)
def create_config(data: DashboardConfigCreate, db: Session = Depends(get_db)):
    return crud.create_config(db, data)


@router.put("/configs/{config_id}", response_model=DashboardConfigOut)
def update_config(config_id: int, data: DashboardConfigUpdate, db: Session = Depends(get_db)):
    cfg = crud.update_config(db, config_id, data)
    if not cfg:
        raise HTTPException(status_code=404, detail="配置不存在")
    return cfg


@router.delete("/configs/{config_id}")
def delete_config(config_id: int, db: Session = Depends(get_db)):
    if not crud.delete_config(db, config_id):
        raise HTTPException(status_code=404, detail="配置不存在")
    return {"success": True}


# ─── Phase bulk replace ───────────────────────────────────────────────────────

@router.put("/configs/{config_id}/phases", response_model=DashboardConfigOut)
def bulk_replace_phases(config_id: int, data: BulkUpdatePhases, db: Session = Depends(get_db)):
    try:
        return crud.bulk_replace_phases(db, config_id, data.phases)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ─── Phases ──────────────────────────────────────────────────────────────────

@router.post("/configs/{config_id}/phases", response_model=PhaseOut)
def add_phase(config_id: int, data: PhaseCreate, db: Session = Depends(get_db)):
    cfg = crud.get_config(db, config_id)
    if not cfg:
        raise HTTPException(status_code=404, detail="配置不存在")
    return crud.add_phase(db, config_id, data)


@router.put("/phases/{phase_id}", response_model=PhaseOut)
def update_phase(phase_id: int, data: PhaseUpdate, db: Session = Depends(get_db)):
    ph = crud.update_phase(db, phase_id, data)
    if not ph:
        raise HTTPException(status_code=404, detail="阶段不存在")
    return ph


@router.delete("/phases/{phase_id}")
def delete_phase(phase_id: int, db: Session = Depends(get_db)):
    if not crud.delete_phase(db, phase_id):
        raise HTTPException(status_code=404, detail="阶段不存在")
    return {"success": True}


# ─── SubStep bulk replace ────────────────────────────────────────────────────

@router.put("/phases/{phase_id}/sub-steps", response_model=PhaseOut)
def bulk_replace_sub_steps(phase_id: int, data: BulkUpdateSubSteps, db: Session = Depends(get_db)):
    try:
        return crud.bulk_replace_sub_steps(db, phase_id, data.sub_steps)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ─── SubSteps ────────────────────────────────────────────────────────────────

@router.post("/phases/{phase_id}/sub-steps", response_model=SubStepOut)
def add_sub_step(phase_id: int, data: SubStepCreate, db: Session = Depends(get_db)):
    ph = crud.get_phase(db, phase_id)
    if not ph:
        raise HTTPException(status_code=404, detail="阶段不存在")
    return crud.add_sub_step(db, phase_id, data)


@router.put("/sub-steps/{sub_step_id}", response_model=SubStepOut)
def update_sub_step(sub_step_id: int, data: SubStepUpdate, db: Session = Depends(get_db)):
    ss = crud.update_sub_step(db, sub_step_id, data)
    if not ss:
        raise HTTPException(status_code=404, detail="子步骤不存在")
    return ss


@router.delete("/sub-steps/{sub_step_id}")
def delete_sub_step(sub_step_id: int, db: Session = Depends(get_db)):
    if not crud.delete_sub_step(db, sub_step_id):
        raise HTTPException(status_code=404, detail="子步骤不存在")
    return {"success": True}
