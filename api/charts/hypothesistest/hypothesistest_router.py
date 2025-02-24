from fastapi import APIRouter

from .ttest import Ttest
from ...utils.file_utils import generate_chart

router = APIRouter()


# Boxplot endpoints
@router.post("/ttest")
async def generate_ttest(request: dict):
    from .ttest import Ttest
    return await generate_chart(request, Ttest, "error_processing", extension="pdf")

@router.post("/twottest")
async def generate_twottest(request: dict):
    from .twottest import TwoTtest
    return await generate_chart(request, TwoTtest, "error_processing", extension="pdf")