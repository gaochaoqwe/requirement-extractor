from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from ...db.deps import get_db
from ...db.models.function import AnalysisFunction
from ...db.models.function_pair import RegressionFunctionPair

router = APIRouter()


def _func_detail(db: Session, func_id: Optional[int]):
    if not func_id:
        return None
    f = db.query(AnalysisFunction).filter(AnalysisFunction.id == func_id).first()
    if not f:
        return None
    return {
        "id": f.id,
        "file_id": f.file_id,
        "function_name": f.function_name,
        "file_path": f.file_path,
        "start_line": f.start_line,
        "end_line": f.end_line,
        "version": f.version,
        "change_type": f.change_type,
        "paired_function_id": f.paired_function_id,
        "source_code": f.source_code,
        "function_description": f.function_description,
        "commented_code": f.commented_code,
        "code_diff": f.code_diff,
    }


@router.get("/regression/pair/{pair_id}")
def get_pair_detail(pair_id: int, db: Session = Depends(get_db)):
    try:
        pair = db.query(RegressionFunctionPair).filter(RegressionFunctionPair.id == pair_id).first()
        if not pair:
            raise HTTPException(status_code=404, detail="pair不存在")

        old_detail = _func_detail(db, pair.old_function_id)
        new_detail = _func_detail(db, pair.new_function_id)

        # 约定：diff只存新版本函数上（stage3写入new_func.code_diff）
        diff_text = None
        if new_detail and new_detail.get("code_diff"):
            diff_text = new_detail.get("code_diff")

        return {
            "pair_id": pair.id,
            "task_id": pair.task_id,
            "change_type": pair.change_type,
            "similarity_score": pair.similarity_score,
            "should_review": pair.should_review,
            "old": old_detail,
            "new": new_detail,
            "diff": diff_text,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
