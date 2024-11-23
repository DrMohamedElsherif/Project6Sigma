from fastapi import APIRouter

from .capabilitystudy import CapabilityStudy
from ...utils.file_utils import generate_chart

router = APIRouter()


@router.post("/capabilitychart")
async def generate_capabilitychart(request: dict):
    return await generate_chart(request, CapabilityStudy, "error_processing", extension="pdf")
