from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...db.deps import get_db
from ...service.regression.file_viewer import build_file_tree, get_file_content, get_file_diff

router = APIRouter()


@router.get("/regression/tree/{task_id}")
def regression_tree(task_id: int, version: str = Query("new"), db: Session = Depends(get_db)):
    try:
        return build_file_tree(db, task_id=task_id, version=version)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/regression/file/{task_id}")
def regression_file(task_id: int, version: str = Query("new"), path: str = Query(""), db: Session = Depends(get_db)):
    try:
        return get_file_content(db, task_id=task_id, version=version, path=path)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/regression/diff/{task_id}")
def regression_diff(task_id: int, path: str = Query(""), db: Session = Depends(get_db)):
    try:
        return get_file_diff(db, task_id=task_id, path=path)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
