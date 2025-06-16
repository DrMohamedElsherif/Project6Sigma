import os
import base64
import uuid
import re
import shutil
from typing import Optional, Tuple
from openai import AzureOpenAI
from dotenv import load_dotenv
from pdf2image import convert_from_path
from PIL import Image
from api.schemas import BusinessLogicException
from config import get_settings
import fitz  # PyMuPDF


settings = get_settings()

async def call_azure_openai(prompt: str, image_data: Optional[str] = None) -> str:
    """
    Asynchronously sends a prompt to the Azure OpenAI service and returns the generated response.
    Supports both text-only and multimodal (text + image) requests.

    Args:
        prompt (str): The input prompt to send to the Azure OpenAI model.
        image_data (str, optional): Base64 data URI or file path to an image for multimodal analysis.

    Returns:
        str: The generated response content from the Azure OpenAI model.

    Raises:
        BusinessLogicException: If the Azure OpenAI endpoint or API key is not configured in the environment variables.
    """
    
    if not settings.azureEndpoint or not settings.azureApiKey:
        raise BusinessLogicException(
            error_code="MISSING_AZURE_OPENAI_CONFIG",
            details={"message": "Azure OpenAI endpoint or API key is not configured."}
        )

    client = AzureOpenAI(
        azure_endpoint=settings.azureEndpoint,
        api_key=settings.azureApiKey,
        api_version="2024-03-01-preview"
    )

    # Build messages based on whether we have an image
    if image_data:
        # Check if it's already a base64 data URI or a file path
        if image_data.startswith('data:'):
            # Already a base64 data URI
            image_uri = image_data
        elif os.path.exists(image_data):
            # Convert local file path to base64
            image_uri = convert_image_to_base64(image_data)
        else:
            # Assume it's already base64 data
            image_uri = image_data
            
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_uri}}
                ]
            }
        ]
    else:
        messages = [{"role": "user", "content": prompt}]

    response = client.chat.completions.create(
        model=settings.azureModel,
        messages=messages,
        max_tokens=2000,
        temperature=0.7
    )

    return response.choices[0].message.content

def build_ai_prompt(raw_data: str = "") -> str:
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

def convert_pdf_to_png(pdf_path: str, output_dir: str) -> str:
    """
    Converts the first page of a PDF to PNG format.
    
    Args:
        pdf_path (str): Path to the PDF file.
        output_dir (str): Directory to save the PNG file.
        
    Returns:
        str: Path to the generated PNG file.
        
    Raises:
        BusinessLogicException: If PDF conversion fails.
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Convert first page of PDF to PNG
        pages = convert_from_path(pdf_path, first_page=1, last_page=1, dpi=300)
        
        if not pages:
            raise BusinessLogicException(
                error_code="PDF_CONVERSION_ERROR",
                details={"message": "No pages found in PDF file."}
            )
        
        # Generate unique filename
        png_filename = f"temp_{uuid.uuid4()}.png"
        png_path = os.path.join(output_dir, png_filename)
        
        # Save the first page as PNG
        pages[0].save(png_path, 'PNG')
        
        return png_path
        
    except Exception as e:
        raise BusinessLogicException(
            error_code="PDF_CONVERSION_ERROR",
            details={"message": f"Failed to convert PDF to PNG: {str(e)}"}
        )

def determine_file_type(file_url: str) -> str:
    """
    Determines the file type based on the URL extension.
    
    Args:
        file_url (str): URL or path to the file.
        
    Returns:
        str: File type ('pdf', 'png', 'jpg', 'jpeg', or 'unknown').
    """
    if not file_url:
        return 'unknown'
        
    extension = file_url.lower().split('.')[-1]
    
    if extension == 'pdf':
        return 'pdf'
    elif extension in ['png', 'jpg', 'jpeg']:
        return extension
    else:
        return 'unknown'

def get_local_path_from_url(file_url: str) -> str:
    """
    Converts a static URL to a local file path.
    
    Args:
        file_url (str): Static URL to the file.
        
    Returns:
        str: Local file path.
    """
    if file_url.startswith(settings.staticUrl):
        # Remove the static URL prefix and prepend the static file path
        relative_path = file_url.replace(settings.staticUrl, "").lstrip("/")
        return os.path.join(settings.staticFilePath, relative_path)
    elif os.path.exists(file_url):
        # Already a local path
        return file_url
    else:
        raise BusinessLogicException(
            error_code="FILE_NOT_FOUND",
            details={"message": f"Could not find local file for URL: {file_url}"}
        )

def save_ai_response_files(ai_response: str, project: str, step: str, chart_path: str = None, file_type: str = None) -> Tuple[str, str]:
    """
    Saves AI response as both PDF and HTML files with proper rendering.
    Creates a separate PDF from the chart and appends it to the AI report PDF.
    
    Args:
        ai_response (str): The AI response HTML content.
        project (str): Project name.
        step (str): Step name.
        chart_path (str): Local path to the original chart file.
        file_type (str): Type of the chart file ('pdf', 'png', 'jpg', 'jpeg').
        
    Returns:
        Tuple[str, str]: (PDF URL, HTML URL)
    """
    
    # Create project directory
    project_path = os.path.join(settings.staticFilePath, project, step)
    os.makedirs(project_path, exist_ok=True)
    
    # Create temp directory for intermediate files
    temp_dir = os.path.join(settings.staticFilePath, "tmp")
    os.makedirs(temp_dir, exist_ok=True)
    
    # Generate unique filenames
    unique_id = str(uuid.uuid4())
    pdf_filename = f"ai_analysis_{unique_id}.pdf"
    html_filename = f"ai_analysis_{unique_id}.html"
    
    pdf_path = os.path.join(project_path, pdf_filename)
    html_path = os.path.join(project_path, html_filename)
    
    # Save raw HTML file
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(ai_response)
    
    # Create PDF from AI response (report part)
    report_pdf_path = os.path.join(temp_dir, f"report_{unique_id}.pdf")
    create_pdf_with_pymupdf(ai_response, report_pdf_path)
    
    # Create PDF from chart if provided
    pdfs_to_merge = [report_pdf_path]
    chart_pdf_path = None
    
    if chart_path and file_type and os.path.exists(chart_path):
        try:
            chart_pdf_path = create_chart_pdf(chart_path, file_type, temp_dir)
            pdfs_to_merge.append(chart_pdf_path)
        except Exception as e:
            print(f"Warning: Could not create chart PDF: {e}")
            # Continue without chart - just use the report
    
    # Merge PDFs (report + chart)
    merge_pdfs(pdfs_to_merge, pdf_path)
    
    # Cleanup temporary files
    cleanup_temp_file(report_pdf_path)
    if chart_pdf_path:
        cleanup_temp_file(chart_pdf_path)
    
    # Clean up old files in temp directory (older than 24 hours)
    cleanup_temp_directory(temp_dir, max_age_hours=24)
    
    # Generate URLs
    if settings.useFullPath == "1":
        pdf_url = pdf_path
        html_url = html_path
    else:
        pdf_url = f"{settings.staticUrl}/{project}/{step}/{pdf_filename}"
        html_url = f"{settings.staticUrl}/{project}/{step}/{html_filename}"
    
    return pdf_url, html_url

def inject_css(html_content):
    """
    Injects CSS styles into HTML content for better PDF rendering.
    """
    css = """
    <style>
      body { 
        font-size: 10pt; 
        margin: 0; 
        box-sizing: border-box;
        line-height: 1.4;
        font-family: Arial, sans-serif;
      }
      img { 
        display: block; 
        margin: 0 auto 16px auto; 
        max-width: 100%; 
        max-height: 200px; 
        height: auto; 
        object-fit: contain;
        page-break-inside: avoid;
      }
      h1 {
        margin-top: 0.2em;
        margin-bottom: 0.5em;
        page-break-after: avoid;
      }
      h2, h3, h4, h5, h6 { 
        margin-top: 1em; 
        margin-bottom: 0.5em;
        page-break-after: avoid;
      }      
      p { 
        margin-top: 0.5em; 
        margin-bottom: 0.5em;
      }
      .section, .summary, .conclusion {
        page-break-inside: avoid;
        margin-bottom: 1em;
      }
      ul, ol {
        margin: 0.5em 0;
        padding-left: 1.5em;
      }
      li {
        margin: 0.25em 0;
      }
    </style>
    """
    if "<head>" in html_content:
        return html_content.replace("<head>", "<head>" + css)
    elif "<html>" in html_content:
        return html_content.replace("<html>", "<html><head>" + css + "</head>")
    else:
        return css + html_content

def set_img_size_attrs(html_content, max_height=400):
    """
    Add height attribute to all <img> tags in the HTML content, preserving aspect ratio.
    """
    def repl(match):
        tag = match.group(0)
        # Remove any existing width/height attributes
        tag = re.sub(r'\s(width|height)="[^"]*"', '', tag)
        # Add new height attribute only
        return tag[:-1] + f' height="{max_height}"' + '>'
    return re.sub(r'<img\b[^>]*>', repl, html_content)

def create_pdf_with_pymupdf(html_content: str, output_path: str):
    """
    Creates a PDF using PyMuPDF with HTML content.
    Uses improved HTML to PDF conversion with proper styling and header/footer support.
    
    Args:
        html_content (str): The AI response HTML content.
        output_path (str): Path where PDF should be saved.
    """
    # Process HTML content with CSS injection and image sizing
    processed_html = inject_css(html_content)
    processed_html = set_img_size_attrs(processed_html, max_height=400)
    
    # Create temporary HTML file
    temp_html_path = output_path.replace('.pdf', '_temp.html')
    with open(temp_html_path, 'w', encoding='utf-8') as f:
        f.write(processed_html)
    
    # Convert HTML to PDF using the improved function
    html_to_pdf_improved(temp_html_path, output_path)
    
    # Clean up temporary HTML file
    cleanup_temp_file(temp_html_path)

def html_to_pdf_improved(html_path, pdf_path):
    """
    Converts an HTML file to a multi-page PDF file using PyMuPDF's Story class.
    Adds header and footer images to each page if available.
    Uses the same A4 dimensions as multi_vari_chart.py for consistency.
    """
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Use same A4 dimensions as multi_vari_chart.py
    a4_width_inches = 8.27
    a4_height_inches = 11.69
    points_per_inch = 72
    a4_width_points = a4_width_inches * points_per_inch  # 595.44 points
    a4_height_points = a4_height_inches * points_per_inch  # 841.68 points
    MEDIABOX = fitz.Rect(0, 0, a4_width_points, a4_height_points)
    story = fitz.Story(html_content)
    
    # Create a temporary PDF first
    temp_pdf_path = pdf_path + "_temp"
    writer = fitz.DocumentWriter(temp_pdf_path)

    # Load header and footer images from assets folder
    def load_image_pixmap(image_path):
        # Calculate the correct path to assets/img from api/utils/
        # From api/utils/ we need to go up two levels to reach project root, then assets/img/
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        assets_img_path = os.path.join(project_root, "assets", "img", image_path)
        
        # Try different paths for header/footer images
        possible_paths = [
            assets_img_path,  # Primary path: project-root/assets/img/
            image_path,       # Direct path if provided
            os.path.join("assets", "img", image_path),  # Relative from current working directory
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    return fitz.Pixmap(path)
                except Exception as e:
                    print(f"Error loading image {path}: {e}")
        
        print(f"Warning: Image file {image_path} not found in any location")
        print(f"Tried paths: {possible_paths}")
        return None

    header_path = "Header.png"
    footer_path = "Footer.png"
    header_img = load_image_pixmap(header_path)
    footer_img = load_image_pixmap(footer_path)
    
    # Calculate header and footer heights (scaled to fit page width)
    header_height = 0
    footer_height = 0
    if header_img:
        header_height = header_img.height * MEDIABOX.width / header_img.width
    if footer_img:
        footer_height = footer_img.height * MEDIABOX.width / footer_img.width

    # Adjust content area to accommodate header and footer
    margin = 18  # 0.25 inch
    content_top = margin + header_height
    content_bottom = MEDIABOX.height - margin - footer_height

    more = 1
    page_count = 0
    max_pages = 50  # Safety limit to prevent infinite loops
    
    # First, create the PDF with content only
    while more and page_count < max_pages:
        dev = writer.begin_page(MEDIABOX)
        
        # Place content between header and footer
        place_rect = fitz.Rect(margin, content_top, MEDIABOX.width - margin, content_bottom)
        more, _ = story.place(place_rect)
        story.draw(dev)
        writer.end_page()
        page_count += 1
    
    writer.close()
    
    # Now open the temporary PDF and add header/footer to each page
    doc = fitz.open(temp_pdf_path)
    total_pages = len(doc)
    
    for page_num in range(total_pages):
        page = doc[page_num]
        
        # Draw header at the top
        if header_img:
            header_rect = fitz.Rect(0, 0, MEDIABOX.width, header_height)
            page.insert_image(header_rect, pixmap=header_img)
        
        # Draw footer at the bottom
        if footer_img:
            footer_rect = fitz.Rect(0, MEDIABOX.height - footer_height, MEDIABOX.width, MEDIABOX.height)
            page.insert_image(footer_rect, pixmap=footer_img)
        
        # Add KI-Analyse page numbers
        page_num_text = f"KI-Analyse {page_num + 1}/{total_pages}"
        
        # Position page number similar to the image PDF function - below footer, slightly to the left
        page_num_x = MEDIABOX.width * 0.82  # 90% from left edge
        page_num_y = MEDIABOX.height - footer_height + 15  # 15 points below footer start
        
        # Insert KI-Analyse page numbers
        page.insert_text(
            fitz.Point(page_num_x, page_num_y), 
            page_num_text,
            fontsize=9,
            color=(0, 0, 0),  # Black color
            fontname="helv"   # Helvetica font
        )
    
    # Save the final PDF
    doc.save(pdf_path)
    doc.close()
    
    # Clean up temporary file
    os.remove(temp_pdf_path)

def cleanup_temp_file(file_path: str) -> None:
    """
    Safely removes a temporary file.
    
    Args:
        file_path (str): Path to the file to remove.
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"Warning: Could not clean up temporary file {file_path}: {e}")

def cleanup_temp_directory(temp_dir: str, max_age_hours: int = 24) -> None:
    """
    Cleans up old temporary files in the temp directory.
    Removes files older than max_age_hours.
    
    Args:
        temp_dir (str): Path to the temporary directory.
        max_age_hours (int): Maximum age in hours before files are deleted.
    """
    try:
        if not os.path.exists(temp_dir):
            return
            
        import time
        current_time = time.time()
        cutoff_time = current_time - (max_age_hours * 3600)  # Convert hours to seconds
        
        files_cleaned = 0
        for filename in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, filename)
            try:
                if os.path.isfile(file_path):
                    file_mtime = os.path.getmtime(file_path)
                    if file_mtime < cutoff_time:
                        os.remove(file_path)
                        files_cleaned += 1
                        print(f"Cleaned up old temporary file: {filename}")
            except Exception as e:
                print(f"Warning: Could not clean up {filename}: {e}")
        
        if files_cleaned > 0:
            print(f"Cleaned up {files_cleaned} old temporary files from {temp_dir}")
            
    except Exception as e:
        print(f"Warning: Could not clean up temp directory {temp_dir}: {e}")

def convert_image_to_base64(image_path: str) -> str:
    """
    Converts an image file to a base64 data URI.
    Uses improved base64 conversion from png_to_b64.py.
    
    Args:
        image_path (str): Path to the image file.
        
    Returns:
        str: Base64 data URI string (e.g., "data:image/png;base64,...")
        
    Raises:
        BusinessLogicException: If the image file cannot be read or converted.
    """
    try:
        if not os.path.exists(image_path):
            raise BusinessLogicException(
                error_code="IMAGE_FILE_NOT_FOUND",
                details={"message": f"Image file not found: {image_path}"}
            )
        
        # Determine image format from file extension
        file_extension = os.path.splitext(image_path)[1].lower()
        mime_type_map = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.webp': 'image/webp'
        }
        
        mime_type = mime_type_map.get(file_extension, 'image/png')
        
        # Use improved base64 conversion
        base64_data = image_to_b64(image_path)
        return f"data:{mime_type};base64,{base64_data}"
            
    except Exception as e:
        raise BusinessLogicException(
            error_code="IMAGE_CONVERSION_ERROR",
            details={"message": f"Failed to convert image to base64: {str(e)}"}
        )

def image_to_b64(image_path):
    """
    Converts an image file to a base64 encoded string.
    Improved version from png_to_b64.py.

    Args:
        image_path (str): Path to the image file.

    Returns:
        str: Base64 encoded string of the image.
    """
    with open(image_path, "rb") as img_file:
        b64_str = base64.b64encode(img_file.read()).decode('utf-8')
    return b64_str



def create_pdf_from_image(image_path: str, output_pdf_path: str) -> None:
    """
    Creates an A4 PDF page from an image file (PNG, JPG, etc.) with header, footer, and page numbering.
    The image is scaled to fit the page while maintaining aspect ratio.
    
    Args:
        image_path (str): Path to the image file.
        output_pdf_path (str): Path where the PDF should be saved.
        
    Raises:
        BusinessLogicException: If the image cannot be processed or PDF creation fails.
    """
    try:
        # Load the image
        if not os.path.exists(image_path):
            raise BusinessLogicException(
                error_code="IMAGE_FILE_NOT_FOUND",
                details={"message": f"Image file not found: {image_path}"}
            )
        
        # Create a new PDF document with same A4 dimensions as multi_vari_chart.py
        doc = fitz.open()  # Create empty PDF
        a4_width_inches = 8.27
        a4_height_inches = 11.69
        points_per_inch = 72
        a4_width_points = a4_width_inches * points_per_inch  # 595.44 points
        a4_height_points = a4_height_inches * points_per_inch  # 841.68 points
        MEDIABOX = fitz.Rect(0, 0, a4_width_points, a4_height_points)
        page = doc.new_page(width=a4_width_points, height=a4_height_points)
        
        # Load header and footer images (reuse logic from html_to_pdf_improved)
        def load_image_pixmap(image_path):
            # Calculate the correct path to assets/img from api/utils/
            # From api/utils/ we need to go up two levels to reach project root, then assets/img/
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            assets_img_path = os.path.join(project_root, "assets", "img", image_path)
            
            # Try different paths for header/footer images
            possible_paths = [
                assets_img_path,  # Primary path: project-root/assets/img/
                image_path,       # Direct path if provided
                os.path.join("assets", "img", image_path),  # Relative from current working directory
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    try:
                        return fitz.Pixmap(path)
                    except Exception as e:
                        print(f"Error loading image {path}: {e}")
            
            print(f"Warning: Image file {image_path} not found in any location")
            print(f"Tried paths: {possible_paths}")
            return None

        header_path = "Header.png"
        footer_path = "Footer.png"
        header_img = load_image_pixmap(header_path)
        footer_img = load_image_pixmap(footer_path)
        
        # Calculate header and footer heights (scaled to fit page width)
        header_height = 0
        footer_height = 0
        if header_img:
            header_height = header_img.height * MEDIABOX.width / header_img.width
        if footer_img:
            footer_height = footer_img.height * MEDIABOX.width / footer_img.width
        
        # Load the main image as a pixmap
        pix = fitz.Pixmap(image_path)
        
        # Calculate scaling to fit A4 page with margins and header/footer space
        margin = 18  # 0.25 inch margins (same as html_to_pdf_improved)
        content_top = margin + header_height
        content_bottom = MEDIABOX.height - margin - footer_height
        content_width = MEDIABOX.width - 2 * margin
        content_height = content_bottom - content_top
        
        # Calculate scale factor to fit image in available content area
        scale_x = content_width / pix.width
        scale_y = content_height / pix.height
        scale = min(scale_x, scale_y)  # Use smaller scale to maintain aspect ratio
        
        # Calculate position within content area
        scaled_width = pix.width * scale
        scaled_height = pix.height * scale
        # Center horizontally, but position closer to top (similar to HTML content flow)
        x = margin + (content_width - scaled_width) / 2
        # Add small top margin from content_top instead of centering vertically
        y = content_top + 10  # Small 10-point margin from header content area
        
        # Insert the main image
        rect = fitz.Rect(x, y, x + scaled_width, y + scaled_height)
        page.insert_image(rect, pixmap=pix)
        
        # Draw header at the top
        if header_img:
            header_rect = fitz.Rect(0, 0, MEDIABOX.width, header_height)
            page.insert_image(header_rect, pixmap=header_img)
        
        # Draw footer at the bottom
        if footer_img:
            footer_rect = fitz.Rect(0, MEDIABOX.height - footer_height, MEDIABOX.width, MEDIABOX.height)
            page.insert_image(footer_rect, pixmap=footer_img)
        
        # Add page number "1/1" below footer, similar to matplotlib version
        page_num_text = "1 / 1"  # Using space around slash like in pdf_utils.py
        # Position it below the footer, slightly to the left (similar to matplotlib version)
        page_num_x = MEDIABOX.width * 0.90  # Slightly left from right edge (90% from left)
        page_num_y = MEDIABOX.height - footer_height + 15  # 15 points below footer start
        
        # Insert text with appropriate font and size
        page.insert_text(
            fitz.Point(page_num_x, page_num_y),
            page_num_text,
            fontsize=9,  # Same size as matplotlib version
            color=(0, 0, 0),  # Black color
            fontname="helv"   # Helvetica font
        )
        
        # Save the PDF
        doc.save(output_pdf_path)
        doc.close()
        pix = None  # Clean up
        
    except Exception as e:
        raise BusinessLogicException(
            error_code="PDF_FROM_IMAGE_ERROR",
            details={"message": f"Failed to create PDF from image: {str(e)}"}
        )

def merge_pdfs(pdf_paths: list, output_path: str) -> None:
    """
    Merges multiple PDF files into a single PDF.
    
    Args:
        pdf_paths (list): List of paths to PDF files to merge.
        output_path (str): Path where the merged PDF should be saved.
        
    Raises:
        BusinessLogicException: If PDF merging fails.
    """
    try:
        # Create output document
        output_doc = fitz.open()
        
        for pdf_path in pdf_paths:
            if os.path.exists(pdf_path):
                # Open source PDF
                source_doc = fitz.open(pdf_path)
                
                # Insert all pages from source into output
                output_doc.insert_pdf(source_doc)
                source_doc.close()
            else:
                print(f"Warning: PDF file not found: {pdf_path}")
        
        # Save merged PDF
        output_doc.save(output_path)
        output_doc.close()
        
    except Exception as e:
        raise BusinessLogicException(
            error_code="PDF_MERGE_ERROR",
            details={"message": f"Failed to merge PDFs: {str(e)}"}
        )

def create_chart_pdf(chart_path: str, file_type: str, temp_dir: str) -> str:
    """
    Creates a PDF from a chart file (PDF or image).
    
    Args:
        chart_path (str): Path to the chart file.
        file_type (str): Type of the chart file ('pdf', 'png', 'jpg', 'jpeg').
        temp_dir (str): Directory for temporary files.
        
    Returns:
        str: Path to the created chart PDF.
        
    Raises:
        BusinessLogicException: If chart PDF creation fails.
    """
    try:
        chart_pdf_filename = f"chart_{uuid.uuid4()}.pdf"
        chart_pdf_path = os.path.join(temp_dir, chart_pdf_filename)
        
        if file_type == 'pdf':
            # If it's already a PDF, just copy it
            shutil.copy2(chart_path, chart_pdf_path)
        else:
            # Convert image to PDF
            create_pdf_from_image(chart_path, chart_pdf_path)
        
        return chart_pdf_path
        
    except Exception as e:
        raise BusinessLogicException(
            error_code="CHART_PDF_CREATION_ERROR",
            details={"message": f"Failed to create chart PDF: {str(e)}"}
        )
