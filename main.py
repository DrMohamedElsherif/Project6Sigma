from fastapi import FastAPI, File, Form, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv
import os
import uuid
import sys
from functools import reduce

from charts import constants
from models.chart import Chart
from models.chartresult import ChartResult

# import all charts
from charts.controlcard import *
from charts.msa import *
from charts.evaluation import *

import shutil

origins = [
    "*",
    "*:*"
]

app = FastAPI(
    title="six sigma charts",
    description="",
    version="0.0.1"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def str_to_class(string):
    return reduce(getattr, string.split("."), sys.modules[__name__])


load_dotenv()
filePath = os.environ.get("staticFilePath")
staticUrl = os.environ.get("staticUrl")
useFullPath = os.environ.get("useFullPath")

app.mount("/static", StaticFiles(directory=filePath), name="static")


@app.post("/upload")
async def create_file(project: str = Form(...), step: str = Form(...), file: UploadFile = File(...)):
    project_path = filePath + "/" + project + "/" + step
    # check if dir exists
    if not os.path.exists(project_path):
        os.makedirs(project_path)

    tmp, file_extension = os.path.splitext(file.filename)
    filename = str(uuid.uuid4()) + file_extension
    save_path = project_path + "/" + filename
    if useFullPath == "1":
        url = save_path
    else:
        url = staticUrl + "/" + project + "/" + step + "/" + filename


    with open(save_path, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)

    return {"filename": filename,
            "url": url}


@app.post("/chart", response_model=ChartResult)
async def generate(chart: Chart):
    project_path = filePath + "/" + chart.project + "/" + chart.step

    # check if dir exists
    if not os.path.exists(project_path):
        os.makedirs(project_path)

    filename = str(uuid.uuid4()) + "." + constants.CHART_EXTENSION
    save_path = project_path + "/" + filename
    result = ChartResult(
        status=None,
        message=None,
        url=None
    )

    try:
        chart_class = str_to_class(chart.type + "." + chart.type.capitalize())
    except AttributeError:
        chart_class = None

    if chart_class:
        generator = chart_class(chart)
    else:
        result.message = "not supported"
        result.status = 422
        return result

    fig = generator.process()
    fig.savefig(save_path)
    # clear the current figure
    fig.clf()
    if useFullPath == "1":
        result.url = filePath + "/" + chart.project + "/" + chart.step + "/" + filename
    else:
        result.url = staticUrl + "/" + chart.project + "/" + chart.step + "/" + filename
    result.message = generator.getProcessMessage()
    result.status = 200

    return result


@app.get("/status")
async def ping():
    return {"status": "ok"}
