from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any

from ....config_database import get_db  # 使用智能数据库切换模块
from ....db.repository.task_repo import TaskRepository
from ....utils.logger import log_info, log_warning
from ....service.business_review.runner.business_runner import run_in_background

router = APIRouter()


class StartBusinessReviewRequest(BaseModel):
	task_id: int
	project_root: str
	software_type: str
	entry_function: Optional[str] = "main"
	options: Optional[Dict[str, Any]] = None


@router.post("/start")
def start_business_review(req: StartBusinessReviewRequest, db=Depends(get_db)):
	# 检查任务是否存在
	task_repo = TaskRepository(db)
	task = task_repo.get_task(req.task_id)
	if not task:
		log_warning(f"任务不存在: {req.task_id}", "business_api")
		return {"status": "error", "message": "任务不存在"}

	log_info(f"启动业务审查 | task={req.task_id} type={req.software_type} entry={req.entry_function}", "business_api")
	run_in_background(req.task_id, req.project_root, req.software_type, req.entry_function or "main", req.options or {})
	return {"status": "started", "task_id": req.task_id} 