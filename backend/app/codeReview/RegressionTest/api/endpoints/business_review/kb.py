from fastapi import APIRouter
from ....service.business_review.kb.loader import list_kb_types

router = APIRouter()


@router.get("/kb/types")
def list_types():
	return {"types": list_kb_types()} 