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
        # Try to extract from raw_data (original format)
        raw_data = request.get("raw_data")
        if raw_data and isinstance(raw_data, dict):
            project = raw_data.get("project")
            step = raw_data.get("step")
            chart_id = raw_data.get("chart_id")
        else:
            # Fallback: try to extract from root (alternative format)
            project = request.get("project")
            step = request.get("step")
            chart_id = request.get("chart_id")
            raw_data = request  # Use the whole request as raw_data for downstream logic

        if not project:
            raise BusinessLogicException(
                error_code="error_missing_project",
                details={"message": "project is required for AI analysis"}
            )
        
        if not step:
            raise BusinessLogicException(
                error_code="error_missing_step",
                details={"message": "step is required for AI analysis"}
            )
        
        if not chart_id:
            raise BusinessLogicException(
                error_code="error_missing_chart_id",
                details={"message": "chart_id is required for AI analysis"}
            )
        
        # Process the AI analysis
        pdf_url, _ = await process_ai_analysis(project, step, chart_id, raw_data)
        
        # Return response with URLs
        return SuccessResponse(data={
            "analysis_pdf_url": pdf_url,
            "project": project,
            "step": step
        })
        
    except BusinessLogicException:
        raise
    except Exception:
        raise BusinessLogicException(
            error_code="error_ai_analysis", 
            details={"message": "An error occurred during AI analysis"}
        )

@router.post("/process-capture")
async def ai_process_capture_endpoint(request: dict = Body(...)):
    """
    AI Process Capture endpoint.
    Expects: {"file_name": "...", "project": "...", "step": "..."}
    """
    from .process_capture import process_capture_logic

    try:
        data = request.get("postBody", request)
        
        file_name = data.get("file_name")
        project = data.get("project")
        step = data.get("step")

        if not all([file_name, project, step]):
            raise BusinessLogicException(
                error_code="error_missing_parameters",
                details={"message": "Project, step, and file_name are required"}
            )

        result = await process_capture_logic(file_name, project, step)
        
        return SuccessResponse(data=result)

    except BusinessLogicException:
        raise
    except Exception as e:
        raise BusinessLogicException(
            error_code="error_ai_process_capture",
            details={"message": "An error occurred during AI process capture"}
        )

@router.post("/sipoc-capture")
async def ai_sipoc_capture_endpoint(request: dict = Body(...)):
    """
    AI SIPOC Capture endpoint.
    Expects: {"file_name": "...", "project": "...", "step": "..."}
    """
    from .sipoc import process_sipoc_logic

    try:
        data = request.get("postBody", request)
        
        file_name = data.get("file_name")
        project = data.get("project")
        step = data.get("step")

        if not all ([file_name, project, step]):
            raise BusinessLogicException(
                error_code="error_missing_parameters",
                details={"message": "Project, step, and file_name are required"}
            )
        
        result = await process_sipoc_logic(file_name, project, step)

        return SuccessResponse(data=result)
    except BusinessLogicException:
        raise
    except Exception:
        raise BusinessLogicException(
            error_code="error_ai_sipoc_capture",
            details={"message": "An error occured during AI SIPOC capture"}
        )
    
@router.post("/voc-capture")
async def ai_voc_capture_endpoint(request: dict = Body(...)):
    """
    AI VOC Capture endpoint.
    Expects: {"file_name": "...", "project": "...", "step": "..."}
    """
    from .voc import process_voc_logic

    try: 
        data = request.get("postBody", request)
        
        file_name = data.get("file_name")
        project = data.get("project")
        step = data.get("step")

        if not all([file_name, project, step]):
            raise BusinessLogicException(
                error_code="error_missing_parameters",
                details={"message": "Project, step and file_name are required"}
            )
        
        result = await process_voc_logic(file_name, project, step)

        return SuccessResponse(data=result)
    except BusinessLogicException:
        raise
    except Exception:
        raise BusinessLogicException(
            error_code="error_ai_voc_capture",
            details={"message": "An error occured during AI VOC capture"}
        )
    
@router.post("/excel-capture")
async def ai_excel_capture(request: dict = Body(...)):
    """
    AI Excel Capture endpoint.
    Expects: {"file_name": "...", "project": "...", "step": "...", "sheet_name": "..."}
    """
    from .excel_capture import process_excel_capture

    try:
        data = request.get("postBody", request)
        
        file_name = data.get("file_name")
        project = data.get("project")
        step = data.get("step")
        sheet_name = data.get("sheet_name")

        if not all ([file_name, project, step, sheet_name]):
            raise BusinessLogicException(
                error_code="error_missing_parameters",
                details={"message": "Project, step and file_name are required"}
            )
    
        result = await process_excel_capture(file_name, project, step, sheet_name)

        return SuccessResponse(data=result)
    except BusinessLogicException:
        raise
    except Exception as e:
        print(f"Unexpected error in excel-capture: {type(e).__name__}: {str(e)}")
        raise BusinessLogicException(
            error_code="error_ai_excel_capture",
            details={"message": f"An error occurred during AI Excel capture"}
        )

@router.post("/excel-capture-all-sheets")
async def ai_excel_capture_all_sheets(request: dict = Body(...)):
    """
    AI Excel Capture All Sheets endpoint.
    Processes all available sheets in the Excel workbook.
    Expects: {"file_name": "...", "project": "...", "step": "..."}
    """
    from .excel_capture import process_excel_capture, get_predefined_sheet_names

    try:
        file_name = request.get("file_name")
        project = request.get("project")
        step = request.get("step")

        if not all([file_name, project, step]):
            raise BusinessLogicException(
                error_code="error_missing_parameters",
                details={"message": "Project, step and file_name are required, "}
            )
        
        predefined_sheets = get_predefined_sheet_names()

        results = []
        for sheet_name in predefined_sheets:
            result = await process_excel_capture(file_name, project, step, sheet_name)
            results.append({
                "sheet_name": sheet_name,
                "result": result
            })

        return SuccessResponse(data={
            "sheets_processed": len(predefined_sheets),
            "results": results
        })
    except BusinessLogicException:
        raise
    except Exception as e:
        raise BusinessLogicException(
            error_code="error_ai_excel_capture_all_sheets",
            details={"message": f"An error occurred during AI All-Sheets-Excel capture"}
        )
