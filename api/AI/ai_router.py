from fastapi import APIRouter, Body
from api.schemas import SuccessResponse, BusinessLogicException

router = APIRouter()

@router.post("/ai-analysis")
async def ai_analysis_endpoint(request: dict = Body(...)):
    """
    AI Analysis endpoint that processes charts (PDF/PNG) and generates analysis.
    The chart will be appended to the analysis report as a separate PDF page.
    
    Expected request format:
    {
        "project": "project_name",
        "step": "analysis", 
        "chart_id": "chart_filename_without_extension",
        "raw_data": "optional raw data string"
    }
    """
    from .analysis import process_ai_analysis
    
    try:
        # Extract relevant info from request
        project = request.get("project")
        step = request.get("step")
        raw_data = request.get("raw_data", "")
        chart_id = request.get("chart_id")

        if not project:
            raise BusinessLogicException(
                error_code="MISSING_PROJECT",
                details={"message": "project is required for AI analysis"}
            )
        
        if not step:
            raise BusinessLogicException(
                error_code="MISSING_STEP",
                details={"message": "step is required for AI analysis"}
            )
        
        if not chart_id:
            raise BusinessLogicException(
                error_code="MISSING_CHART_ID",
                details={"message": "chart_id is required for AI analysis"}
            )
        
        # Process the AI analysis
        pdf_url, html_url = await process_ai_analysis(project, step, chart_id, raw_data)
        
        # Return response with URLs
        return SuccessResponse(data={
            "analysis_pdf_url": pdf_url,
            "project": project,
            "step": step
        })
        
    except BusinessLogicException:
        raise
    except Exception as e:
        raise BusinessLogicException(
            error_code="AI_ANALYSIS_ERROR", 
            details={"original_error": str(e)}
        )

@router.post("/process-capture")
async def ai_process_capture_endpoint(request: dict):
    """
    AI Process Capture endpoint.
    Expects: {"file_name": "...", "file_extension": "...", "project": "...", "step": "..."}
    """
    from .process_capture import process_capture_logic

    try:
        file_name = request.get("file_name")
        file_extension = request.get("file_extension")
        project = request.get("project")
        step = request.get("step")

        if not all([file_name, file_extension, project, step]):
            raise BusinessLogicException(
                error_code="MISSING_PARAMETERS",
                details={"message": "file_name, file_extension, project, and step are required"}
            )

        result = await process_capture_logic(file_name, file_extension, project, step)
        print(f"Result: {result}")
        return SuccessResponse(data=result)

    except BusinessLogicException:
        raise
    except Exception as e:
        raise BusinessLogicException(
            error_code="AI_PROCESS_CAPTURE_ERROR",
            details={"original_error": str(e)}
        )
