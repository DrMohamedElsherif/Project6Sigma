from fastapi import APIRouter

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

@router.post("/ftestmultiple")
async def generate_ftestmultiple(request: dict):
    from .ftest_multiple import FtestMultiple
    return await generate_chart(request, FtestMultiple, "error_processing", extension="pdf")

@router.post("/defectivetest")
async def generate_defectivetest(request: dict):
    from .defectivetest import Defectivetest
    return await generate_chart(request, Defectivetest, "error_processing", extension="pdf")

@router.post("/twodefectivetest")
async def generate_twodefectivetest(request: dict):
    from .twodefectivetest import TwoDefectivetest
    return await generate_chart(request, TwoDefectivetest, "error_processing", extension="pdf")

@router.post("/multipledefectivetest")
async def generate_multipledefectivetest(request: dict):
    from .multipledefectivetest import MultipleDefectiveTest
    return await generate_chart(request, MultipleDefectiveTest, "error_processing", extension="pdf")

@router.post("/chisquared")
async def generate_chisquared(request: dict):
    from .chi_squared import ChiSquared
    return await generate_chart(request, ChiSquared, "error_processing", extension="pdf")

@router.post("/twochisquared")
async def generate_twochisquared(request: dict):
    from .twochi_squared import TwoChiSquared
    return await generate_chart(request, TwoChiSquared, "error_processing", extension="pdf")

@router.post("/multiplechisquared")
async def generate_multiplechisquared(request: dict):
    from .multiple_chi_squared import MultipleChiSquared
    return await generate_chart(request, MultipleChiSquared, "error_processing", extension="pdf")