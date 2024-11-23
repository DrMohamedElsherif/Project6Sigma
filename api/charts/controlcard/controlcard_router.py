from fastapi import APIRouter

from .cchart import Cchart
from .mrchart import Mrchart
from .npchart import Npchart
from .pchart import Pchart
from .rchart import Rchart
from .schart import Schart
from .uchart import Uchart
from ...utils.file_utils import generate_chart

router = APIRouter()


@router.post("/cchart")
async def generate_cchart(request: dict):
    return await generate_chart(request, Cchart, "error_processing")


@router.post("/mrchart")
async def generate_mrchart(request: dict):
    return await generate_chart(request, Mrchart, "error_processing")


@router.post("/npchart")
async def generate_npchart(request: dict):
    return await generate_chart(request, Npchart, "error_processing")


@router.post("/pchart")
async def generate_pchart(request: dict):
    return await generate_chart(request, Pchart, "error_processing")


@router.post("/rchart")
async def generate_rchart(request: dict):
    return await generate_chart(request, Rchart, "error_processing")


@router.post("/schart")
async def generate_schart(request: dict):
    return await generate_chart(request, Schart, "error_processing")


@router.post("/uchart")
async def generate_uchart(request: dict):
    return await generate_chart(request, Uchart, "error_processing")
