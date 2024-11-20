from fastapi import APIRouter
from api.schemas import BusinessLogicException, SuccessResponse
from .msa1chart import MSA1Chart
from ...utils.file_utils import save_figure

router = APIRouter()


@router.post("/msa1")
async def generate_msa1(request: dict):
    try:
        chart_generator = MSA1Chart(request)
        fig = chart_generator.process()
        _, url = save_figure(fig, chart_generator.project, chart_generator.step)

        return SuccessResponse(data={
            "url": url,
            "message": chart_generator.getProcessMessage() or "MSA1 chart generated successfully"
        })
    except Exception as e:
        if isinstance(e, BusinessLogicException):
            raise e
        raise BusinessLogicException(
            error_code="error_processing_msa1",
            details={"original_error": str(e)}
        )
