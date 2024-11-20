import os
import uuid
from typing import Tuple

from config import get_settings

settings = get_settings()


def save_figure(figure, project: str, step: str, extension: str = "png") -> Tuple[str, str]:
    """
    Speichert eine Figur und gibt den Speicherpfad und die URL zurück.

    Args:
        figure: matplotlib Figure oder BytesIO Objekt
        project: Projektname/ID
        step: Projektschritt
        extension: Dateiendung (default: "png")

    Returns:
        Tuple[str, str]: (Speicherpfad, URL)
    """

    # Verzeichnis erstellen
    project_path = os.path.join(settings.staticFilePath, project, step)
    if not os.path.exists(project_path):
        os.makedirs(project_path)

    # Dateinamen generieren
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
