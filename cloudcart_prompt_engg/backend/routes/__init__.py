from fastapi import APIRouter

from backend.routes.health import router as health_router
from backend.routes.validation import router as validation_router
from backend.routes.analysis import router as analysis_router
from backend.routes.invocation import router as invocation_router
from backend.routes.version import router as version_router

router = APIRouter()
router.include_router(health_router, prefix="", tags=["health"])
router.include_router(validation_router, prefix="", tags=["validation"])
router.include_router(analysis_router, prefix="", tags=["analysis"])
router.include_router(invocation_router, prefix="", tags=["invoke"])
router.include_router(version_router, prefix="", tags=["version"])
