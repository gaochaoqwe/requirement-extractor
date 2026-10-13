from fastapi import APIRouter
from ....service.business_review.runner.business_runner import get_progress

router = APIRouter()


@router.get("/progress")
def business_progress(task_id: int):
	return get_progress(task_id) 