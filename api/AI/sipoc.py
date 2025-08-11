from typing import Dict
import json
import os
import uuid
from api.utils.ai_utils import (
    call_azure_openai,
    convert_image_to_base64,
    image_to_b64,
    cleanup_temp_file,
)
import fitz #PyMuPDF
from api.AI.analysis import find_file_by_chart_id, determine_file_type_from_extension
from config import get_settings
from api.schemas import BusinessLogicException

settings = get_settings()

async def process_sipoc_logic(file_name: str, project: str, step: str) -> Dict:
    """
    Processes a file (PDF/PNG/JPG) for SIPOC analysis.
    """

    try: 
        file_name = file_name.rsplit('.', 1)[0] if '.' in file_name else file_name
        local_file_path, detected_extension = find_file_by_chart_id(project, step, file_name, settings.staticFilePath)
        file_type = determine_file_type_from_extension(detected_extension)

        temp_dir = os.path.join(settings.staticFilePath, 'tmp')
        os.makedirs(temp_dir, exist_ok=True)

        if file_type == 'pdf':
            doc = fitz.open(local_file_path)
            if len(doc) == 0:
                raise BusinessLogicException(
                    error_code="error_pdf_conversion",
                    details = {"message": "Failed to convert PDF to image for AI analysis"}
                )
            page = doc[0]
            mat = fitz.Matrix(300/72, 300/72)
            pix = page.get_pixmap(matrix=mat)
            temp_png_filename = f"temp_sipoc_{uuid.uuid4()}.png"
            png_path = os.path.join(temp_dir, temp_png_filename)
            pix.save(png_path)
            doc.close()
            pix = None
        elif file_type == 'image':
            png_path = local_file_path
        else:
            raise BusinessLogicException(
                error_code="error_unsupported_file_type",
                details={"message": f"Unsupported file type: {detected_extension}"}
            )
        try: 
            image_b64 = convert_image_to_base64(png_path)
        except Exception:
            image_b64 = image_to_b64(png_path)

        prompt = """
Analysiere das dargestellte SIPOC-Diagramm (Supplier-Input-Process-Output-Customer) oder Prozessdokument und extrahiere alle relevanten Informationen.

Ich brauche die Informationen in einem exakt definierten JSON-Format. Beachte dabei:
1. Identifiziere den Prozessstart und das Prozessende
2. Erfasse alle Prozessschritte/Aktivitäten als ARRAY
3. Identifiziere alle Outputs und zugehörige Kunden als ARRAYS
4. Identifiziere alle Inputs und zugehörige Lieferanten als ARRAYS
5. Erfasse alle Kennzahlen (KPIs) mit ihren Werten und Einheiten als ARRAY
6. Extrahiere eine kurze Prozessbeschreibung oder einen Kommentar

KRITISCH WICHTIG ZUR DATENSTRUKTUR:
- defineSipoc8, defineSipoc12, defineSipoc19 und defineSipoc26 MÜSSEN immer Arrays sein
- Diese Arrays müssen mindestens ein Element enthalten, auch wenn nur ein Eintrag erkennbar ist
- Jedes Array-Element muss exakt die vorgegebene Struktur haben

Gib deine Antwort AUSSCHLIESSLICH in folgendem JSON-Format zurück:

{
  "defineSipoc": {
    "defineSipoc6": "Startpunkt/Startereignis des Prozesses",
    "defineSipoc8": [
      { "defineSipoc9": "Prozessschritt 1" },
      { "defineSipoc9": "Prozessschritt 2" }
    ],
    "defineSipoc10": "Endpunkt/Endereignis des Prozesses",
    "defineSipoc12": [
      {
        "defineSipoc14": "Output 1",
        "defineSipoc16": [
          { "defineSipoc17": "Kunde für Output 1" }
        ]
      },
      {
        "defineSipoc14": "Output 2",
        "defineSipoc16": [
          { "defineSipoc17": "Kunde 1 für Output 2" },
          { "defineSipoc17": "Kunde 2 für Output 2" }
        ]
      }
    ],
    "defineSipoc19": [
      {
        "defineSipoc21": "Input 1",
        "defineSipoc23": [
          { "defineSipoc24": "Lieferant für Input 1" }
        ]
      },
      {
        "defineSipoc21": "Input 2",
        "defineSipoc23": [
          { "defineSipoc24": "Lieferant 1 für Input 2" },
          { "defineSipoc24": "Lieferant 2 für Input 2" }
        ]
      }
    ],
    "defineSipoc26": [
      {
        "defineSipoc28": "KPI/Messgröße 1",
        "defineSipoc30": "Wert/Einheit 1"
      },
      {
        "defineSipoc28": "KPI/Messgröße 2",
        "defineSipoc30": "Wert/Einheit 2"
      }
    ],
    "defineSipoc31": "Zusammenfassender Kommentar zum Prozess"
  }
}

Beispiele für korrekte Array-Strukturen:

1. Für einen einzelnen Prozessschritt:
   "defineSipoc8": [
     { "defineSipoc9": "Ein Prozessschritt" }
   ]

2. Für einen einzelnen Output mit einem Kunden:
   "defineSipoc12": [
     {
       "defineSipoc14": "Ein Output",
       "defineSipoc16": [
         { "defineSipoc17": "Ein Kunde" }
       ]
     }
   ]

WICHTIG:
- Stelle sicher, dass ALLE Felder im JSON ausgefüllt sind.
- Wenn Informationen fehlen, verwende einen leeren String ("") oder leere Arrays ([]).
- Ordne die Informationen korrekt den jeweiligen Schlüsseln zu.
- Antworte AUSSCHLIESSLICH mit dem JSON-Objekt ohne zusätzlichen Text oder Markdown.
- Die Felder defineSipoc8, defineSipoc12, defineSipoc19, defineSipoc26 MÜSSEN Arrays sein.

Analysiere das Bild jetzt und extrahiere alle SIPOC-Informationen:
"""
        ai_response = await call_azure_openai(prompt, image_data=image_b64)

        try: 
            cleaned_response = ai_response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()

            # Parse Json
            parsed_response = json.loads(cleaned_response)
            
            # Validate Structure
            if "defineSipoc" not in parsed_response:
                raise ValueError("Missing defineSipoc key in response")
            
            sipoc_data = parsed_response["defineSipoc"]

            # ensure all required keys are present with proper structure
            required_keys = {
                "defineSipoc6": "", 
                "defineSipoc8": [],
                "defineSipoc10": "",
                "defineSipoc12": [],
                "defineSipoc19": [],
                "defineSipoc26": [],
                "defineSipoc31": ""
            }

            for key, default_value in required_keys.items():
                if key not in sipoc_data:
                    sipoc_data[key] = default_value
            
            # Ensure correct structure for nested arrays
            if not isinstance(sipoc_data["defineSipoc8"], list):
                sipoc_data["defineSipoc8"] = []
            
            if len(sipoc_data["defineSipoc8"]) == 0:
                sipoc_data["defineSipoc8"] = [{"defineSipoc9": ""}]
            else:
                for i, item in enumerate(sipoc_data["defineSipoc8"]):
                    if "defineSipoc9" not in item:
                        sipoc_data["defineSipoc8"][i] = {"defineSipoc9": ""}
            
            # Validate and fix outputs & customers structure
            if not isinstance(sipoc_data["defineSipoc12"], list):
                sipoc_data["defineSipoc12"] = []
            
            if len(sipoc_data["defineSipoc12"]) == 0:
                sipoc_data["defineSipoc12"] = [{"defineSipoc14": "", "defineSipoc16": [{"defineSipoc17": ""}]}]
            else:
                for i, output in enumerate(sipoc_data["defineSipoc12"]):
                    if "defineSipoc14" not in output:
                        output["defineSipoc14"] = ""
                    if "defineSipoc16" not in output or not isinstance(output["defineSipoc16"], list):
                        output["defineSipoc16"] = [{"defineSipoc17": ""}]
                    else:
                        for j, customer in enumerate(output["defineSipoc16"]):
                            if "defineSipoc17" not in customer:
                                output["defineSipoc16"][j] = {"defineSipoc17": ""}
            
            # Validate and fix inputs & suppliers structure
            if not isinstance(sipoc_data["defineSipoc19"], list):
                sipoc_data["defineSipoc19"] = []
            
            if len(sipoc_data["defineSipoc19"]) == 0:
                sipoc_data["defineSipoc19"] = [{"defineSipoc21": "", "defineSipoc23": [{"defineSipoc24": ""}]}]
            else:
                for i, input_item in enumerate(sipoc_data["defineSipoc19"]):
                    if "defineSipoc21" not in input_item:
                        input_item["defineSipoc21"] = ""
                    if "defineSipoc23" not in input_item or not isinstance(input_item["defineSipoc23"], list):
                        input_item["defineSipoc23"] = [{"defineSipoc24": ""}]
                    else:
                        for j, supplier in enumerate(input_item["defineSipoc23"]):
                            if "defineSipoc24" not in supplier:
                                input_item["defineSipoc23"][j] = {"defineSipoc24": ""}
            
            # Validate and fix KPIs structure
            if not isinstance(sipoc_data["defineSipoc26"], list):
                sipoc_data["defineSipoc26"] = []
            
            if len(sipoc_data["defineSipoc26"]) == 0:
                sipoc_data["defineSipoc26"] = [{"defineSipoc28": "", "defineSipoc30": ""}]
            else:
                for i, kpi in enumerate(sipoc_data["defineSipoc26"]):
                    if "defineSipoc28" not in kpi:
                        kpi["defineSipoc28"] = ""
                    if "defineSipoc30" not in kpi:
                        kpi["defineSipoc30"] = ""
            
            # Check if all content is empty (indicating a failure to extract meaningful data)
            all_empty = (
                not sipoc_data["defineSipoc6"] and
                not sipoc_data["defineSipoc10"] and
                not sipoc_data["defineSipoc31"] and
                all(not item["defineSipoc9"] for item in sipoc_data["defineSipoc8"]) and
                all(not output["defineSipoc14"] for output in sipoc_data["defineSipoc12"]) and
                all(not input_item["defineSipoc21"] for input_item in sipoc_data["defineSipoc19"]) and
                all(not kpi["defineSipoc28"] for kpi in sipoc_data["defineSipoc26"])
            )
            
            if all_empty:
                raise BusinessLogicException(
                    error_code="error_could_not_extract_data",
                    details={"message": "Keine klaren Prozessinformationen im Bild erkennbar"}
                )
                
            return parsed_response

        except (json.JSONDecodeError, ValueError):
            raise BusinessLogicException(
                error_code="error_ai_analysis_processing",
                details={"message": "An error occured during AI analysis"}
            )
    finally:
        if 'file_type' in locals() and file_type == 'pdf' and 'png_path' in locals() and png_path != local_file_path:
            cleanup_temp_file(png_path)