from fastapi import APIRouter

from .capability.capability_router import router as capability_router
from .evaluation.evaluation_router import router as evaluation_router
from .msa.msa_router import router as msa_router
from .controlcard.controlcard_router import router as controlcard_router
from .hypothesistest.hypothesistest_router import router as hypothesistest_router
from .ai_analysis_router import router as ai_analysis_router

router = APIRouter()

# Einbinden der Sub-Router
router.include_router(
    capability_router,
    prefix="/capability",
    tags=["charts-capability"]
)

router.include_router(
    msa_router,
    prefix="/msa",
    tags=["charts-msa"]
)

router.include_router(
    controlcard_router,
    prefix="/controlcard",
    tags=["charts-controlcard"]
)

router.include_router(
    evaluation_router,
    prefix="/evaluation",
    tags=["charts-evaluation"]
)

router.include_router(
    hypothesistest_router,
    prefix="/hypothesistest",
    tags=["charts-hypothesistest"]
)

router.include_router(
    ai_analysis_router,
    prefix="/ai-analysis",
    tags=["charts-ai-analysis"]
)
