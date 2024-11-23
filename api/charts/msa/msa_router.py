from fastapi import APIRouter
from api.schemas import BusinessLogicException, SuccessResponse
from .msa1chart import MSA1Chart
from .msa2n3crossedchart import MSA2n3CrossedChart
from .msa2n3gagerrchart import MSA2n3GagerrChart
from .msa2n3nestedchart import MSA2n3NestedChart
from .msagagereportchart import MsaGageReportChart
from ...utils.file_utils import save_figure, generate_chart

router = APIRouter()


@router.post("/msa1")
async def generate_msa1(request: dict):
    return await generate_chart(request, MSA1Chart, "error_processing", extension="pdf")


@router.post("/msa2n3crossedchart")
async def generate_msa2n3crossedchart(request: dict):
    return await generate_chart(request, MSA2n3CrossedChart, "error_processing", extension="pdf")


@router.post("/msa2n3gagerrchart")
async def generate_msa2n3gagerrchart(request: dict):
    return await generate_chart(request, MSA2n3GagerrChart, "error_processing", extension="pdf")


@router.post("/msa2n3nestedchart")
async def generate_msa2n3nestedchart(request: dict):
    return await generate_chart(request, MSA2n3NestedChart, "error_processing", extension="pdf")


@router.post("/msagagereportchart")
async def generate_msagagereportchart(request: dict):
    return await generate_chart(request, MsaGageReportChart, "error_processing", extension="pdf")
