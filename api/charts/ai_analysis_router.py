import os
from fastapi import APIRouter, Body
from api.schemas import SuccessResponse, BusinessLogicException
from config import get_settings
from ..utils.ai_utils import (
    call_azure_openai, 
    build_ai_prompt, 
    convert_pdf_to_png,
    determine_file_type_encrypted,
    get_local_path_from_url,
    save_ai_response_files,
    cleanup_temp_file,
    convert_image_to_base64,
    decrypt_craft_encrypted_url
)

router = APIRouter()
settings = get_settings()

@router.post("/ai-analysis", tags=["charts-ai-analysis"])
async def ai_analysis_endpoint(request: dict = Body(...)):
    """
    AI Analysis endpoint that processes charts (PDF/PNG) and generates analysis.
    The chart will be appended to the analysis report as a separate PDF page.
    
    Expected request format:
    {
        "project": "project_name",
        "step": "analysis",
        "chart_url": "URL_to_PDF_or_PNG",
        "raw_data": "optional raw data string"
    }
    """
    temp_png_path = None
    
    try:
        # Extract relevant info from request
        project = request.get("project", "ai_analysis")
        step = request.get("step", "analysis")
        raw_data = request.get("raw_data", "")
        chart_url = request.get("chart_url")

        if not chart_url:
            raise BusinessLogicException(
                error_code="MISSING_CHART_URL",
                details={"message": "chart_url is required for AI analysis"}
            )
        
        # Step 1: Determine file type and prepare image
        key = settings.decryptKey
        if not key:
            raise BusinessLogicException(
                error_code="MISSING_DECRYPT_KEY",
                details={"message": "decryptKey is required for decryption"}
            )
        key_bytes = key.encode("utf-8")
        file_type = determine_file_type_encrypted(chart_url, key_bytes)

        # Decrypt chart_url if needed to get the real file path
        if not (chart_url.startswith('http') or chart_url.startswith('/')):
            chart_url_decrypted = decrypt_craft_encrypted_url(chart_url, key_bytes)
        else:
            chart_url_decrypted = chart_url

        if file_type == 'unknown':
            raise BusinessLogicException(
                error_code="UNSUPPORTED_FILE_TYPE",
                details={"message": f"Unsupported file type. Supported: PDF, PNG, JPG, JPEG"}
            )
        
        # Step 2: Convert file to local path and prepare for AI analysis
        local_file_path = get_local_path_from_url(chart_url_decrypted)
        
        if not os.path.exists(local_file_path):
            raise BusinessLogicException(
                error_code="FILE_NOT_FOUND",
                details={"message": f"File not found at path: {local_file_path}"}
            )
        
        # Step 3: Prepare image for AI vision analysis
        if file_type == 'pdf':
            # Ensure staticFilePath is set
            if not settings.staticFilePath:
                raise BusinessLogicException(
                    error_code="MISSING_STATIC_FILE_PATH",
                    details={"message": "staticFilePath is required for temporary file storage"}
                )
            temp_dir = os.path.join(settings.staticFilePath, "tmp")
            os.makedirs(temp_dir, exist_ok=True)
            temp_png_path = convert_pdf_to_png(local_file_path, temp_dir)
            image_path_for_ai = temp_png_path
        else:
            # Use image directly for AI analysis
            image_path_for_ai = local_file_path

        # Convert image to base64 for AI vision analysis
        chart_base64 = convert_image_to_base64(image_path_for_ai)
        
        # Step 4: Build AI prompt (without embedding the chart)
        prompt = build_ai_prompt(raw_data=raw_data)
        
        # Step 5: Call OpenAI with base64 image data for vision analysis
        ai_response = await call_azure_openai(prompt, image_data=chart_base64)
        
        if not ai_response:
            raise BusinessLogicException(
                error_code="AI_RESPONSE_EMPTY",
                details={"message": "AI service returned empty response"}
            )
        
        # Step 6: Save AI response and append chart PDF
        # Use original file path and type for chart PDF creation
        chart_file_path = local_file_path
        chart_file_type = file_type
        
        pdf_url, html_url = save_ai_response_files(
            ai_response, 
            project, 
            step, 
            chart_path=chart_file_path,
            file_type=chart_file_type
        )
        
        # Step 7: Cleanup temporary files
        if temp_png_path:
            cleanup_temp_file(temp_png_path)
        
        # Step 8: Return response with URLs
        return SuccessResponse(data={
            "analysis_pdf_url": pdf_url,
            # "analysis_html_url": html_url,
            "project": project,
            "step": step
        })
        
    except BusinessLogicException:
        # Cleanup on error
        if temp_png_path:
            cleanup_temp_file(temp_png_path)
        raise
    except Exception as e:
        # Cleanup on error
        if temp_png_path:
            cleanup_temp_file(temp_png_path)
        raise BusinessLogicException(
            error_code="AI_ANALYSIS_ERROR", 
            details={"original_error": str(e)}
        )
