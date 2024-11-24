from fastapi import APIRouter, File, Form, UploadFile
import os
import uuid
import shutil
from config import get_settings

router = APIRouter()
settings = get_settings()


# Split up if there is more than one function
@router.post("/")
async def create_file(
        project: str = Form(...),
        step: str = Form(...),
        file: UploadFile = File(...)
):
    project_path = settings.staticFilePath + "/" + project + "/" + step
    if not os.path.exists(project_path):
        os.makedirs(project_path)

    tmp, file_extension = os.path.splitext(file.filename)
    filename = str(uuid.uuid4()) + file_extension
    save_path = project_path + "/" + filename

    if settings.useFullPath == "1":
        url = save_path
    else:
        url = settings.staticUrl + "/" + project + "/" + step + "/" + filename

    with open(save_path, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)

    return {"filename": filename, "url": url}