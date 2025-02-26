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

@router.post("/pairedttest")
async def generate_pairedttest(request: dict):
    from .paired_ttest import PairedTtest
    return await generate_chart(request, PairedTtest, "error_processing", extension="pdf")

# Anova

@router.post("/ftest")
async def generate_ftest(request: dict):
    from .ftest import Ftest
    return await generate_chart(request, Ftest, "error_processing", extension="pdf")