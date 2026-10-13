from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...db.deps import get_db
from ...service.regression.change_detector import get_task_changes

router = APIRouter()


@router.get("/regression/changes/{task_id}")
def regression_changes(
    task_id: int,
    refresh: bool = Query(False),
    db: Session = Depends(get_db),
):
    try:
        return get_task_changes(db, task_id=task_id, refresh=refresh)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
