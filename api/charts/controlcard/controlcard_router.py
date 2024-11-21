from fastapi import APIRouter
from api.schemas import BusinessLogicException, SuccessResponse
from .npchart import Npchart
from .pchart import Pchart
from .rchart import Rchart
from .schart import Schart
from .uchart import Uchart
from ...utils.file_utils import save_figure
from .cchart import Cchart
from .mrchart import Mrchart

router = APIRouter()


async def generate_chart(request: dict, chart_class, error_code, extension="png"):
    try:
        chart_generator = chart_class(request)
        fig = chart_generator.process()
        _, url = save_figure(fig, chart_generator.project, chart_generator.step, extension=extension)
        return SuccessResponse(
            data={"url": url}
        )
    except Exception as e:
        if isinstance(e, BusinessLogicException):
            raise e
        raise BusinessLogicException(error_code=error_code, details={"original_error": str(e)})


@router.post("/cchart")
async def generate_cchart(request: dict):
    return await generate_chart(request, Cchart, "error_processing")


@router.post("/mrchart")
async def generate_mrchart(request: dict):
    return await generate_chart(request, Mrchart, "error_processing")


@router.post("/npchart")
async def generate_npchart(request: dict):
    return await generate_chart(request, Npchart, "error_processing", extension="pdf")


@router.post("/pchart")
async def generate_pchart(request: dict):
    return await generate_chart(request, Pchart, "error_processing", extension="pdf")


@router.post("/rchart")
async def generate_rchart(request: dict):
    return await generate_chart(request, Rchart, "error_processing", extension="pdf")


@router.post("/schart")
async def generate_schart(request: dict):
    return await generate_chart(request, Schart, "error_processing", extension="pdf")


@router.post("/uchart")
async def generate_uchart(request: dict):
    return await generate_chart(request, Uchart, "error_processing", extension="pdf")