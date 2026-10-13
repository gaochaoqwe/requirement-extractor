"""
链路审查问题接口
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ....config_database_chain import get_chain_db  # 使用链路审查数据库切换模块
from ....db.repository.chain_review_repo import ChainReviewProblemRepository

router = APIRouter()

@router.get("/chain/problems/{task_id}")
async def get_chain_problems(task_id: int, db: Session = Depends(get_chain_db)):
    problem_repo = ChainReviewProblemRepository(db)
    problems = problem_repo.get_problems_by_task(task_id)
    return {
        "problems": [problem.to_dict() for problem in problems]
    }
