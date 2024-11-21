from fastapi import APIRouter
from api.schemas import BusinessLogicException, SuccessResponse
from .capabilitystudy import CapabilityStudy
from ...utils.file_utils import save_figure

router = APIRouter()


async def generate_chart(request: dict, chart_class, error_code, extension="png"):
    try:
        chart_generator = chart_class(request)
        fig = chart_generator.process()
        _, url = save_figure(fig, chart_generator.project, chart_generator.step, extension=extension)
        return SuccessResponse(data={"url": url})
    except Exception as e:
        if isinstance(e, BusinessLogicException):
            raise e
        raise BusinessLogicException(error_code=error_code, details={"original_error": str(e)})


@router.post("/capabilitychart")
async def generate_capabilitychart(request: dict):
    return await generate_chart(request, CapabilityStudy, "error_processing", extension="pdf")
