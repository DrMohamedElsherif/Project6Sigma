from fastapi import APIRouter

from api.charts.charts_router import router as charts_router
from api.status.status_router import router as status_router
from api.uploads.uploads_router import router as uploads_router
from api.AI.ai_router import router as ai_router

api_router = APIRouter(prefix="/api/v1")

# INTEGRATE ROUTERS / Per folder one router
api_router.include_router(
    charts_router,
    prefix="/charts",
    tags=["charts"]
)

api_router.include_router(
    uploads_router,
    prefix="/upload",
    tags=["upload"]
)

api_router.include_router(
    status_router,
    prefix="/status",
    tags=["status"]
)

api_router.include_router(
    ai_router,
    prefix="/ai",
    tags=["ai"]
)