from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...db.deps import get_db
from ...config_database import SessionLocal
from ...service.regression.review_runner import run_regression_review
from ...service.regression.change_detector import refresh_task_change_detection

router = APIRouter()


def _run_in_background(task_id: int, refresh_changes: bool = False):
    db = SessionLocal()
    try:
        if refresh_changes:
            refresh_task_change_detection(db, task_id)
        run_regression_review(task_id)
    finally:
        try:
            db.close()
        except Exception:
            pass


@router.post("/regression/review/{task_id}")
def start_regression_review(
    task_id: int,
    background_tasks: BackgroundTasks,
    refresh_changes: bool = Query(True),
    db: Session = Depends(get_db),
):
    try:
        background_tasks.add_task(_run_in_background, task_id, refresh_changes)
        return {
            "task_id": task_id,
            "status": "started",
            "refresh_changes": refresh_changes,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
