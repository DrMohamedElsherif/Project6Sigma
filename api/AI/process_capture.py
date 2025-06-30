from typing import Dict
import json
import base64
import tempfile
import os
import uuid
import fitz  # PyMuPDF
from api.utils.ai_utils import (
    call_azure_openai,
    convert_image_to_base64,
    image_to_b64,
    get_local_path_from_url,
    cleanup_temp_file,
)
from api.AI.analysis import find_file_by_chart_id, determine_file_type_from_extension
from config import get_settings

settings = get_settings()

async def process_capture_logic(file_name: str, project: str, step: str) -> Dict:
    """
    Processes a file (PDF/PNG/JPG) for AI process capture analysis.
    Finds the file in the static folder, converts to image if needed, 
    and extracts structured process information using AI.
    """
    try:
        # Remove the file extension from the file name
        file_name = file_name.rsplit('.', 1)[0] if '.' in file_name else file_name
        # Use find_file_by_chart_id to robustly locate the file and extension
        local_file_path, detected_extension = find_file_by_chart_id(project, step, file_name, settings.staticFilePath)
        file_type = determine_file_type_from_extension(detected_extension)

        temp_dir = os.path.join(settings.staticFilePath, 'tmp')
        os.makedirs(temp_dir, exist_ok=True)

        # Step 2: If PDF, convert to PNG using PyMuPDF
        if file_type == 'pdf':
            # Convert PDF to PNG using PyMuPDF for AI analysis
            try:
                doc = fitz.open(local_file_path)
                if len(doc) == 0:
                    return {
                        "measureProcessCapture5": [{
                            "measureProcessCapture6": "",
                            "measureProcessCapture7": "",
                            "measureProcessCapture8": "No pages found in PDF file",
                            "measureProcessCapture9": "",
                            "measureProcessCapture10": "",
                            "measureProcessCapture11": "",
                            "measureProcessCapture12": ""
                        }]
                    }
                
                # Get first page and convert to PNG
                page = doc[0]
                mat = fitz.Matrix(300/72, 300/72)  # 300 DPI scaling
                pix = page.get_pixmap(matrix=mat)
                
                # Save as temporary PNG
                temp_png_filename = f"temp_process_capture_{uuid.uuid4()}.png"
                png_path = os.path.join(temp_dir, temp_png_filename)
                pix.save(png_path)
                
                # Cleanup PyMuPDF objects
                doc.close()
                pix = None
                
            except Exception as pdf_error:
                return {
                    "measureProcessCapture5": [{
                        "measureProcessCapture6": "",
                        "measureProcessCapture7": "",
                        "measureProcessCapture8": f"Failed to convert PDF to image: {str(pdf_error)}",
                        "measureProcessCapture9": "",
                        "measureProcessCapture10": "",
                        "measureProcessCapture11": "",
                        "measureProcessCapture12": ""
                    }]
                }
        elif file_type == 'image':
            png_path = local_file_path
        else:
            return {
                "measureProcessCapture5": [{
                    "measureProcessCapture6": "",
                    "measureProcessCapture7": "",
                    "measureProcessCapture8": f"Unsupported file type: {detected_extension}",
                    "measureProcessCapture9": "",
                    "measureProcessCapture10": "",
                    "measureProcessCapture11": "",
                    "measureProcessCapture12": ""
                }]
            }

        # Step 3: Convert image to base64
        try:
            image_b64 = convert_image_to_base64(png_path)
        except Exception:
            image_b64 = image_to_b64(png_path)

        # Step 4: Build prompt for AI to extract structured process information
        prompt = """
Analysiere das dargestellte Prozessdiagramm oder Dokument und extrahiere strukturierte Prozessinformationen.

Gib die Antwort als gültiges JSON-Objekt zurück mit folgendem Format:
{
  "measureProcessCapture5": [
    {
      "measureProcessCapture6": "Prozessschritt-Name",
      "measureProcessCapture7": "Prozessverantwortlicher/Owner", 
      "measureProcessCapture8": "Beschreibung oder Notizen",
      "measureProcessCapture12": "Zusätzliche Notizen",
      "measureProcessCapture9": "Details",
      "measureProcessCapture10": "Input/Eingabe",
      "measureProcessCapture11": "Output/Ausgabe"
    }
  ]
}

Wichtige Hinweise:
- Wenn mehrere Prozessschritte erkennbar sind, erstelle für jeden einen separaten Eintrag im Array
- Alle Felder müssen vorhanden sein, auch wenn sie leer sind (als leerer String "")
- Antworte NUR mit dem JSON-Objekt, ohne zusätzlichen Text
- Extrahiere alle erkennbaren Prozessschritte, Verantwortlichkeiten, Inputs und Outputs
- Verwende deutsche Begriffe und Beschreibungen
- Falls keine klaren Prozessinformationen erkennbar sind, gib ein Array mit einem leeren Objekt zurück

Analysiere das Bild und extrahiere die Prozessinformationen:
"""

        # Step 5: Call Azure OpenAI
        ai_response = await call_azure_openai(prompt, image_data=image_b64)

        # Step 6: Parse AI response as JSON
        try:
            # Clean the response - remove any markdown formatting or extra text
            cleaned_response = ai_response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()
            
            # Parse JSON
            parsed_response = json.loads(cleaned_response)
            
            # Validate structure
            if "measureProcessCapture5" not in parsed_response:
                raise ValueError("Missing measureProcessCapture5 key")
            
            # Ensure all objects have required keys
            required_keys = [
                "measureProcessCapture6", "measureProcessCapture7", "measureProcessCapture8",
                "measureProcessCapture9", "measureProcessCapture10", "measureProcessCapture11", 
                "measureProcessCapture12"
            ]
            
            for process in parsed_response["measureProcessCapture5"]:
                for key in required_keys:
                    if key not in process:
                        process[key] = ""
            
            return parsed_response
            
        except (json.JSONDecodeError, ValueError) as e:
            # If JSON parsing fails, return a default structure
            return {
                "measureProcessCapture5": [{
                    "measureProcessCapture6": "Prozessanalyse",
                    "measureProcessCapture7": "",
                    "measureProcessCapture8": f"AI-Antwort konnte nicht als JSON geparst werden: {str(e)}",
                    "measureProcessCapture9": ai_response[:500] if ai_response else "",
                    "measureProcessCapture10": "",
                    "measureProcessCapture11": "",
                    "measureProcessCapture12": ""
                }]
            }
    finally:
        # Clean up temporary PNG if created
        if 'file_type' in locals() and file_type == 'pdf' and 'png_path' in locals() and png_path != local_file_path:
            cleanup_temp_file(png_path)
