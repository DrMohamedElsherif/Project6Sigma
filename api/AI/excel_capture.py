import json
import os
from api.schemas import BusinessLogicException
from config import get_settings
from .excel_utils.preprocess_excel import ExcelPipeline
from .excel_utils.sheet_prompts import get_prompt
from .excel_utils.sheet_validators import validate_json
from api.utils.ai_utils import call_azure_openai

settings = get_settings()

async def process_excel_capture(file_name: str, project: str, step: str, sheet_name: str):
    """
    Processes an Excel File to extract the contents of a sheet
    """

    try:
        file_name = file_name.replace(".xlsx", "").replace(".xls", "")

        base_path = os.path.join(settings.staticFilePath, project, step)
        
        file_path_xlsx = os.path.join(base_path, f"{file_name}.xlsx")
        file_path_xls = os.path.join(base_path, f"{file_name}.xls")
        
        if os.path.exists(file_path_xlsx):
            file_path = file_path_xlsx
        elif os.path.exists(file_path_xls):
            file_path = file_path_xls
        else:
            raise FileNotFoundError(
                f"Excel file not found. Tried: {file_path_xlsx} and {file_path_xls}"
            )
        
        pipeline = ExcelPipeline(file_path)
        try:
            preprocessed_excel_sheet = (pipeline
                .load_sheet(sheet_name)
                .get_data()
            )

        except Exception as e:
            raise BusinessLogicException(
                error_code="error_sheet_not_found",
                details={"message": f"Could not find the specific sheet"}
            )
        
        prompt = get_prompt(sheet_name, preprocessed_excel_sheet)
        
        ai_response = await call_azure_openai(prompt)

        try:
            cleaned_response = ai_response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()
            
            formatted_data = json.loads(cleaned_response)
            
            validate_json(sheet_name, formatted_data)
            return formatted_data
        
        except json.JSONDecodeError as e:
            print(f"[DEBUG] JSON Decode Error: {str(e)}")
            raise BusinessLogicException(
                error_code="error_ai_analysis_processing",
                details={"message": f"Failed to parse AI response as JSON: {str(e)}"}
            )
        except ValueError as e:
            print(f"[DEBUG] Validation Error: {str(e)}")
            raise BusinessLogicException(
                error_code="error_ai_analysis_processing",
                details={"message": f"Validation failed: {str(e)}"}
            )
    except ValueError as e:
        raise BusinessLogicException(
            error_code="error_ai_analysis_processing",
            details={"message": "An error occured during AI analysis"}
        )
    
def get_predefined_sheet_names():
    """
    Returns the list of predefined sheet names available for processing.
    These are locked sheets in the Excel workbook.
    """
    return [
        "D-VoC to CTx",
        "D-SIPOC",
        "M-Prozesserfassung",
        "Info-Sammlung",
        "D-Problembeschreibung",
        "D-Status",
        "D-Review Protokoll",
        "D-Stakeholderanalysis",
        "M-Prozessparametermodell",
        "M-Datenerfassungsplan",
        "M-Status",
        "M-Review Protokoll",
        "A-Status",
        "A-Review Protokoll",
        "I-Status",
        "I-Review Protokoll",
        "I-Ideenliste"
        "C-Status",
        "C-Review Protokoll",
        "C-Review _ Lessons Learned",
    ]
