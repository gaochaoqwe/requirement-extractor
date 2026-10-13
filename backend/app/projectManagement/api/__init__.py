from fastapi import APIRouter
from . import projects

router = APIRouter()

# Include project-related routes
router.include_router(projects.router, tags=["Projects"])

__all__ = ["router"]
