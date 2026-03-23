# api/correlation/correlation_router.py

from fastapi import APIRouter
from api.utils.file_utils import generate_chart
from api.correlation.correlation import CorrelationAnalysis

router = APIRouter()

@router.post("/analyze")
async def analyze_correlation(request: dict):
    """
    Perform correlation analysis on two variables.
    
    Returns a scatter plot with regression line and statistics table.
    """
    return await generate_chart(request, CorrelationAnalysis, "correlation_error")

@router.post("/pearson")
async def pearson_correlation(request: dict):
    """
    Force Pearson correlation analysis.
    Overrides the auto-selection to use Pearson method.
    """
    # Ensure method is set to pearson
    if "config" in request:
        request["config"]["method"] = "pearson"
    return await generate_chart(request, CorrelationAnalysis, "correlation_error")

@router.post("/spearman")
async def spearman_correlation(request: dict):
    """
    Force Spearman correlation analysis.
    Overrides the auto-selection to use Spearman method.
    """
    if "config" in request:
        request["config"]["method"] = "spearman"
    return await generate_chart(request, CorrelationAnalysis, "correlation_error")

@router.post("/kendall")
async def kendall_correlation(request: dict):
    """
    Force Kendall-Tau correlation analysis.
    Overrides the auto-selection to use Kendall method.
    """
    if "config" in request:
        request["config"]["method"] = "kendall"
    return await generate_chart(request, CorrelationAnalysis, "correlation_error")