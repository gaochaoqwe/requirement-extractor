from fastapi import APIRouter

from .endpoints.graph import router as graph_router
from .endpoints.node import router as node_router
from .endpoints.edge import router as edge_router
from .endpoints.asset import router as asset_router


router = APIRouter(prefix="/opto-knowledge", tags=["Opto Knowledge"])

router.include_router(graph_router, prefix="")
router.include_router(node_router, prefix="")
router.include_router(edge_router, prefix="")
router.include_router(asset_router, prefix="")
