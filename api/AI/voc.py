from typing import Dict
import json
import os
import uuid
from api.utils.ai_utils import (
    call_azure_openai,
    convert_image_to_base64,
    image_to_b64,
    cleanup_temp_file
)
import fitz #PyMuPDF
from api.AI.analysis import find_file_by_chart_id, determine_file_type_from_extension
from config import get_settings
from api.schemas import BusinessLogicException

settings = get_settings()

async def process_voc_logic(file_name: str, project: str, step: str) -> Dict:
    """
    Processes a file (PDF/PNG/JGP) for VOC analysis
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
Analysiere das dargestellte Bild (z.B. ein VoC-Board, eine Kundenfeedback-Tabelle oder ein ähnliches Dokument) und extrahiere alle relevanten Voice-of-Customer-Informationen.

Ich brauche die Informationen in einem exakt definierten JSON-Format. Beachte dabei:

Erfasse jede identifizierbare Kundenstimme als EIN OBJEKT in einem ARRAY.
WICHTIG: Falls eine Kundenstimme mehrere "Originalaussage der Kundenstimme" enthält, erstelle für jede einzelne Aussage ein separates Objekt im Array. Jede Aussage soll als eigenständige Kundenstimme behandelt werden.

Für jede Kundenstimme extrahiere:
Ob sie intern oder extern ist (defineVoc3: 0 = "-- bitte wählen --", 1 = "Intern", 2 = "Extern")
Ob Kosten, Qualität oder Zeit betroffen sind (defineVoc4, defineVoc5, defineVoc6: true/false)
Die Originalaussage der Kundenstimme (defineVoc7)
Wer die Aussage gemacht hat (defineVoc8)
Woher die Aussage stammt (defineVoc9)
Kernthema/Stichworte (defineVoc10)
CTx/Parameter/Spezifikation (defineVoc11)
KRITISCH WICHTIG ZUR DATENSTRUKTUR:

Das Feld defineVoc2 MUSS immer ein Array sein, auch wenn nur eine Kundenstimme erkannt wird.
Jedes Array-Element muss exakt die vorgegebene Struktur haben und alle Felder enthalten.
Gib deine Antwort AUSSCHLIESSLICH in folgendem JSON-Format zurück:

{
  "defineVoc2": [
    {
      "defineVoc3": 1,
      "defineVoc4": true,
      "defineVoc5": false,
      "defineVoc6": true,
      "defineVoc7": "Originalaussage der Kundenstimme",
      "defineVoc8": "Wer",
      "defineVoc9": "Woher",
      "defineVoc10": "Kernthema",
      "defineVoc11": "CTx"
    }
  ]
}

Beispiele für korrekte Array-Strukturen:

Für eine einzelne Kundenstimme: "defineVoc2": [ { "defineVoc3": 2, "defineVoc4": false, "defineVoc5": true, "defineVoc6": false, "defineVoc7": "Kunde fordert bessere Qualität.", "defineVoc8": "Max Mustermann", "defineVoc9": "Kundendienst", "defineVoc10": "Qualität", "defineVoc11": "CTQ: Fehlerquote < 1%" } ]
WICHTIG:

Stelle sicher, dass ALLE Felder im JSON ausgefüllt sind.
Wenn Informationen fehlen, verwende einen leeren String ("") oder den passenden Standardwert (z.B. false für Checkboxen oder "0" für defineVoc3).
Ordne die Informationen korrekt den jeweiligen Schlüsseln zu.
Antworte AUSSCHLIESSLICH mit dem JSON-Objekt ohne zusätzlichen Text oder Markdown.
Das Feld defineVoc2 MUSS ein Array sein.
Analysiere das Bild jetzt und extrahiere alle VoC-Informationen:
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

            if "defineVoc2" not in parsed_response:
                raise ValueError("Missing defineVoc2 key in response")

            voc_entries = parsed_response["defineVoc2"]
            if not isinstance(voc_entries, list):
                voc_entries = []
                parsed_response["defineVoc2"] = voc_entries

            template_entry = {
                "defineVoc3": 0,
                "defineVoc4": False,
                "defineVoc5": False,
                "defineVoc6": False,
                "defineVoc7": "",
                "defineVoc8": "",
                "defineVoc9": "",
                "defineVoc10": "",
                "defineVoc11": ""
            }

            if not voc_entries:
                voc_entries.append(template_entry.copy())

            def _to_bool(value):
                if isinstance(value, bool):
                    return value
                if isinstance(value, (int, float)):
                    return value != 0
                if isinstance(value, str):
                    return value.strip().lower() in {"true", "1", "yes", "ja"}
                return False

            for i, entry in enumerate(voc_entries):
                if not isinstance(entry, dict):
                    voc_entries[i] = entry = template_entry.copy()
                for key, default in template_entry.items():
                    if key not in entry:
                        entry[key] = default

                try:
                    entry["defineVoc3"] = int(entry["defineVoc3"])
                except (TypeError, ValueError):
                    entry["defineVoc3"] = 0
                if entry["defineVoc3"] not in (0, 1, 2):
                    entry["defineVoc3"] = 0

                for bool_key in ("defineVoc4", "defineVoc5", "defineVoc6"):
                    entry[bool_key] = _to_bool(entry[bool_key])

                for text_key in ("defineVoc7", "defineVoc8", "defineVoc9", "defineVoc10", "defineVoc11"):
                    value = entry[text_key]
                    entry[text_key] = "" if value is None else str(value)

            all_empty = all(
                entry["defineVoc3"] == 0 and
                not entry["defineVoc4"] and
                not entry["defineVoc5"] and
                not entry["defineVoc6"] and
                not entry["defineVoc7"] and
                not entry["defineVoc8"] and
                not entry["defineVoc9"] and
                not entry["defineVoc10"] and
                not entry["defineVoc11"]
                for entry in voc_entries
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