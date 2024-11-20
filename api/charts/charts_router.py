from fastapi import APIRouter
from .msa.msa_router import router as msa_router

router = APIRouter()

# Einbinden der Sub-Router
router.include_router(
    msa_router,
    prefix="/msa",
    tags=["charts-msa"]
)
