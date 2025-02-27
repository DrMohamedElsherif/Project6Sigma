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

@router.post("/onewayanova")
async def generate_onewayanova(request: dict):
    from .one_way_anova import OneWayAnova
    return await generate_chart(request, OneWayAnova, "error_processing", extension="pdf")

@router.post("/ftest")
async def generate_ftest(request: dict):
    from .ftest import Ftest
    return await generate_chart(request, Ftest, "error_processing", extension="pdf")

@router.post("/twoftest")
async def generate_twoftest(request: dict):
    from .twoftest import TwoFtest
    return await generate_chart(request, TwoFtest, "error_processing", extension="pdf")