from .start import router as start_router
from .progress import router as progress_router
from .codemap import router as codemap_router
from .download import router as download_router
from .problems import router as problems_router

router = APIRouter()
router.include_router(start_router, prefix="/chain", tags=["chain_review"])
router.include_router(progress_router, prefix="/chain", tags=["chain_review"])
router.include_router(codemap_router, prefix="/chain", tags=["chain_review"])
router.include_router(download_router, prefix="/chain", tags=["chain_review"])
router.include_router(problems_router, prefix="/chain", tags=["chain_review"])
