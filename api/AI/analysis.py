import os
from typing import Tuple
from api.schemas import BusinessLogicException
from config import get_settings
from api.utils.ai_utils import (
    call_azure_openai,
    convert_pdf_to_png,
    cleanup_temp_file,
    convert_image_to_base64,
    save_ai_response_files
)

settings = get_settings()

def find_file_by_chart_id(project: str, step: str, chart_id: str, static_path: str) -> Tuple[str, str]:
    """
    Find a file in the static folder by project/step/chart_id and return path and extension.
    
    Args:
        project: Project name
        step: Step name
        chart_id: Chart filename without extension
        static_path: Path to static files directory
        
    Returns:
        Tuple[str, str]: (full_file_path, file_extension)
        
    Raises:
        BusinessLogicException: If file not found
    """
    if not project or not step or not chart_id:
        raise BusinessLogicException(
            error_code="INVALID_PARAMETERS",
            details={"message": "Project, step, and chart_id are required"}
        )
    
    # Construct the directory path
    chart_dir = os.path.join(static_path, project, step)
    
    if not os.path.exists(chart_dir):
        raise BusinessLogicException(
            error_code="DIRECTORY_NOT_FOUND",
            details={"message": f"Directory not found: {chart_dir}"}
        )
    
    # Common image and document extensions
    extensions = ['pdf', 'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff']
    
    for ext in extensions:
        file_path = os.path.join(chart_dir, f"{chart_id}.{ext}")
        if os.path.exists(file_path):
            return file_path, ext
    
    raise BusinessLogicException(
        error_code="FILE_NOT_FOUND",
        details={"message": f"No file found for chart_id '{chart_id}' in {chart_dir}"}
    )

def determine_file_type_from_extension(extension: str) -> str:
    """
    Determine file type from extension.
    
    Args:
        extension: File extension (without dot)
        
    Returns:
        str: 'pdf', 'image', or 'unknown'
    """
    extension = extension.lower()
    
    if extension == 'pdf':
        return 'pdf'
    elif extension in ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff']:
        return 'image'
    else:
        return 'unknown'

def build_ai_analysis_prompt(raw_data: str = "") -> str:
    """
    Builds a prompt for AI analysis based on raw data.
    Generates HTML output for better PDF rendering.
    The chart image will be appended separately to the final PDF.

    Args:
        raw_data (str): The raw data to be analyzed.

    Returns:
        str: The constructed AI prompt for HTML generation.
    """
    if raw_data:
        prompt_addition = f"Bitte analysiere die dargestellte statistische Grafik und nutze dazu auch die folgenden Daten: {raw_data}"
    else:
        prompt_addition = "Bitte analysiere die dargestellte statistische Grafik."

    prompt = f"""
    Gehe dabei nach einem festen Schema vor, welches nachfolgend beschrieben ist. Die Darstellung kann ein Datensatz oder eine Visualisierung (z.B. Boxplot, Histogramm, Streudiagramm, Korrelationsmatrix etc.) sein. 
    
    WICHTIG: Generiere die Antwort als sauberes HTML mit professioneller Formatierung. Verwende diese Struktur:

    <!DOCTYPE html>
    <html lang="de">
    <head>
        <meta charset="UTF-8">
        <title>Statistische Analyse</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0 40px 40px 40px; color: #333; }}
            h1 {{ color: #2c3e50; border-bottom: 3px solid #95b92a; padding-bottom: 10px; }}
            h2 {{ color: #34495e; border-bottom: 1px solid #bdc3c7; padding-bottom: 5px; margin-top: 30px; }}
            h3 {{ color: #7f8c8d; margin-top: 25px; }}
            ul {{ margin: 15px 0; }}
            li {{ margin: 8px 0; }}
            .summary {{ background: #ecf0f1; padding: 20px; border-radius: 5px; margin: 20px 0; }}
            .section {{ margin: 30px 0; }}
            .conclusion {{ background: #e8f6f3; padding: 20px; border-radius: 5px; border-left: 4px solid #95b92a; }}
            .chart-container {{ text-align: center; margin: 30px 0; padding: 20px; background: #f8f9fa; border-radius: 5px; }}
        </style>
    </head>
    <body>

    Gehe dabei wie folgt vor:
    
    1. ÜBERSCHRIFT UND BESCHREIBUNG:
        • Starte mit einer <h1>Überschrift über das was analysiert wird</h1>
        • Erstelle einen Einleitungssatz dazu
        • Erwähne, dass die Grafik als separater Anhang beigefügt ist

    2. STRUKTURIERTER ANALYSETEXT:
        Füge folgenden Text ein:
        <div class="summary">
        <p><strong>Im Folgenden wird die Darstellung/Daten in folgenden Schritten analysiert:</strong></p>
        <ol>
            <li>Beschreibung der Grafik</li>
            <li>Statistische Interpretation</li>
            <li>Empfehlung zur weiterführenden Analyse</li>
            <li>Fazit und Bedeutung</li>
        </ol>
        </div>

        3. DETAILANALYSE IN HTML-ABSCHNITTEN:

        <div class="section">
        <h2>1. Beschreibung der Daten oder Darstellung</h2>
        <p>Gib eine objektive, präzise Beschreibung der Ausgangsdaten oder der Visualisierung:</p>
        <ul>
            <li>Was wird gezeigt?</li>
            <li>Welche Variablen/Spalten sind enthalten?</li>
            <li>Welche Achsen, Maßeinheiten, Gruppen oder Aggregationen sind erkennbar?</li>
            <li>Welche Art von Skalenniveau liegt vor (nominal, ordinal, metrisch)?</li>
        </ul>
        <p>Runde den Abschnitt noch mit zwei bis drei zusammenfassenden Sätzen ab.</p>
        </div>

        <div class="section">
        <h2>2. Interpretation der Inhalte</h2>
        <p>Analysiere die dargestellten Informationen inhaltlich:</p>
        <ul>
            <li>Gibt es erkennbare Muster, Trends, Gruppen oder Ausreißer?</li>
            <li>Lassen sich Zusammenhänge, Unterschiede oder besondere Merkmale ableiten?</li>
            <li>Ist die Verteilung normal oder auffällig verschoben?</li>
        </ul>
        <p>Runde den Abschnitt noch mit zwei bis drei zusammenfassenden Sätzen ab.</p>
        </div>

        <div class="section">
        <h2>3. Empfehlungen für weiterführende Analysen</h2>
        <p>Leite aus deiner Interpretation konkrete nächste Schritte für eine vertiefende Analyse oder Datenaufbereitung ab:</p>
        <ul>
            <li>Welche weiteren statistischen Verfahren wären sinnvoll (z.B. Korrelation, Regression, ANOVA, Transformation, etc.)?</li>
            <li>Gibt es Daten, die bereinigt, transformiert oder aggregiert werden sollten?</li>
            <li>Welche weiteren Visualisierungen könnten Erkenntnisse schärfen?</li>
            <li>Sollten noch weitere Daten erhoben werden, um mögliche Tendenzen zu verfeinern, zu verfestigen oder statistisch abzusichern?</li>
        </ul>
        <p>Runde den Abschnitt noch mit zwei bis drei zusammenfassenden Sätzen ab.</p>
        </div>

        <div class="conclusion">
        <h2>4. Fazit und Einordnung</h2>
        <p>Fasse die wesentlichen Erkenntnisse kompakt zusammen:</p>
        <ul>
            <li>Was lässt sich abschließend sagen?</li>
            <li>Welche Bedeutung haben die bisherigen Ergebnisse im gegebenen Kontext?</li>
            <li>Gibt es Einschränkungen oder offene Fragen, die in Folgeanalysen berücksichtigt werden sollten?</li>
        </ul>
        <p>Runde das Ganze noch mit drei bis fünf zusammenfassenden Sätzen ab.</p>
        </div>

    </body>
    </html>

    Vorgehen: Gib für jeden Spiegelstrich eine Antwort und strukturiere danach
    Sprache: Bitte wähle eine klare, professionelle und verständliche Sprache aus Sicht eines erfahrenen Datenanalysten oder Six Sigma Experten – so, dass die Analyse auch für Dritte gut nachvollziehbar ist. Falls sinnvoll, beziehe auf gängige Begriffe der deskriptiven Statistik und von Six Sigma mit ein.
    
    WICHTIG: Antworte ausschließlich mit dem vollständigen HTML-Code, ohne zusätzliche Erklärungen oder Markdown-Formatierung.
    """

    final_prompt = f"{prompt_addition}\n\n{prompt}"
    return final_prompt

async def process_ai_analysis(project: str, step: str, chart_id: str, raw_data: str = "") -> Tuple[str, str]:
    """
    Processes AI analysis for a chart/image.
    
    Args:
        project (str): Project name.
        step (str): Step name.
        chart_id (str): Chart filename without extension.
        raw_data (str): Optional raw data string.
        
    Returns:
        Tuple[str, str]: (PDF URL, HTML URL)
        
    Raises:
        BusinessLogicException: If processing fails.
    """
    temp_png_path = None
    
    try:
        # Step 1: Find the chart file in static/{project}/{step}/{chart_id}.{ext}
        if not settings.staticFilePath:
            raise BusinessLogicException(
                error_code="MISSING_STATIC_FILE_PATH",
                details={"message": "staticFilePath is required to locate files"}
            )
        
        local_file_path, file_extension = find_file_by_chart_id(project, step, chart_id, settings.staticFilePath)
        
        # Step 2: Validate file type
        file_type = determine_file_type_from_extension(file_extension)

        if file_type == 'unknown':
            raise BusinessLogicException(
                error_code="UNSUPPORTED_FILE_TYPE",
                details={"message": f"Unsupported file type: {file_extension}. Supported: PDF, PNG, JPG, JPEG"}
            )
        
        # Step 3: Prepare image for AI vision analysis
        if file_type == 'pdf':
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
        prompt = build_ai_analysis_prompt(raw_data=raw_data)
        
        # Step 5: Call OpenAI with base64 image data for vision analysis
        ai_response = await call_azure_openai(prompt, image_data=chart_base64)
        
        if not ai_response:
            raise BusinessLogicException(
                error_code="AI_RESPONSE_EMPTY",
                details={"message": "AI service returned empty response"}
            )
        
        # Step 6: Save AI response and append chart PDF
        pdf_url, html_url = save_ai_response_files(
            ai_response, 
            project, 
            step, 
            chart_path=local_file_path,
            file_type=file_type
        )
        
        # Step 7: Cleanup temporary files
        if temp_png_path:
            cleanup_temp_file(temp_png_path)
        
        return pdf_url, html_url
        
    except Exception as e:
        # Cleanup on error
        if temp_png_path:
            cleanup_temp_file(temp_png_path)
        
        if isinstance(e, BusinessLogicException):
            raise
        else:
            raise BusinessLogicException(
                error_code="AI_ANALYSIS_PROCESSING_ERROR", 
                details={"original_error": str(e)}
            )
