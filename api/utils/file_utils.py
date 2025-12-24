# file_utils.py

import os
import uuid
import urllib.parse
from typing import Tuple

from api.schemas import SuccessResponse, BusinessLogicException
from config import get_settings

settings = get_settings()


def save_figure(figure, project: str, step: str, extension: str = "png", is_test: bool = False,
                test_title: str = "api_test_chart") -> Tuple[str, str]:
    """
    Speichert eine Figur und gibt den Speicherpfad und die URL zurück.

    Args:
        figure: matplotlib Figure oder BytesIO Objekt
        project: Projektname/ID
        step: Projektschritt
        extension: Dateiendung (default: "png")
        is_test: True, wenn es sich um einen Test handelt (default: False)
        test_title: Titel für Testcharts (default: "api_test_chart")

    Returns:
        Tuple[str, str]: (Speicherpfad, URL)
    """

    # Verzeichnis erstellen
    project_path = os.path.join(settings.staticFilePath, project, step)
    if not os.path.exists(project_path):
        os.makedirs(project_path)

    # Dateinamen generieren
    if is_test:
        filename = f"{test_title}.{extension}"
    else:
        filename = f"{uuid.uuid4()}.{extension}"

    save_path = os.path.join(project_path, filename)

    # Speichern
    if hasattr(figure, 'savefig'):
        figure.savefig(save_path)
        figure.clf()
    else:  # BytesIO
        with open(save_path, 'wb') as f:
            f.write(figure.read())

    # URL generieren

    url = save_path if settings.useFullPath == "1" else f"{settings.staticUrl}/{project}/{step}/{filename}"

    return save_path, url

async def generate_chart(request: dict, chart_class, error_code, extension="png"):
    try:
        chart_generator = chart_class(request)
        fig = chart_generator.process()

        project_id = chart_generator.project
        is_test = False

        if chart_generator.project == "api_test":
            project_id = "api_test"
            is_test = True

        save_path, url = save_figure(
            fig,
            project_id,
            chart_generator.step,
            extension=extension,
            is_test=is_test,
            test_title=request.get("config").get("title")
        )
        
        # ------------------ MODIFICATION START ------------------
        # URL-encode path to handle spaces/special chars
        url = urllib.parse.urljoin(url, urllib.parse.quote(os.path.basename(url)))
        # ------------------ MODIFICATION END --------------------
        
        # Extract chart_id from the filename (without extension)
        filename = os.path.basename(save_path)
        chart_id = os.path.splitext(filename)[0]

        # ------------------ MODIFICATION START ------------------
        # Include statistics if available
        response_data = {"url": url, "chart_id": chart_id}

        # Check if chart_generator has attribute `statistics` and include it
        if hasattr(chart_generator, "statistics") and chart_generator.statistics is not None:
            response_data["statistics"] = chart_generator.statistics
        # ------------------ MODIFICATION END --------------------
        

        return SuccessResponse(data=response_data)

    except Exception as e:
        if isinstance(e, BusinessLogicException):
            raise e
        raise BusinessLogicException(error_code=error_code, details={"original_error": str(e)})
