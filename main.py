from fastapi import FastAPI, File, Form, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv
import os
import uuid

from models.chart import Chart
from models.chartresult import ChartResult
from charts.controlcard.mrchart import Mrchart
from charts.controlcard.cchart import Cchart
from charts.controlcard.npchart import Npchart
from charts.controlcard.rchart import Rchart
from charts.controlcard.schart import Schart
from charts.controlcard.pchart import Pchart
from charts.controlcard.uchart import Uchart
from charts.evaluation.boxplot1 import Boxplot1
from charts.evaluation.boxplot2 import Boxplot2
from charts.evaluation.boxplot3 import Boxplot3


from charts.constants import *
import shutil;

origins = [
    "*",
    "*:*"
]

app = FastAPI(
    title="sixsigma charts",
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

load_dotenv()
filePath = os.environ.get("staticFilePath")
staticUrl = os.environ.get("staticUrl")

app.mount("/static", StaticFiles(directory=filePath), name="static")


@app.post("/upload")
async def create_file( project: str = Form(...), step: str =  Form(...), file: UploadFile = File(...)):
    projectPath = filePath + "/" + project + "/" + step 
    # check if dir exists
    if not os.path.exists(projectPath):
        os.makedirs(projectPath)

    filename = str(uuid.uuid4()) + "." + CHART_EXTENSION
    savePath = projectPath + "/" + filename;
    url = staticUrl + "/" + project + "/" + step  + "/" + filename
    
    with open(savePath, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)

    return {"filename": filename, 
            "url" : url }


@app.post("/chart", response_model=ChartResult)
async def generate(chart: Chart):
    projectPath = filePath + "/" + chart.project + "/" + chart.step 
    # check if dir exists
    if not os.path.exists(projectPath):
        os.makedirs(projectPath)

    filename = str(uuid.uuid4()) + "." + CHART_EXTENSION
    savePath = projectPath + "/" + filename;
    result = ChartResult()
    result.url = staticUrl + "/" + chart.project + "/" + chart.step + "/" + filename
    result.status = 200;

    if chart.type == "mrchart":
        generator = Mrchart(chart)
    elif chart.type == "cchart":
        generator = Cchart(chart)
    elif chart.type ==  "npchart":
        generator = Npchart(chart)
    elif chart.type ==  "rchart":
        generator = Rchart(chart)
    elif chart.type ==  "schart":
        generator = Schart(chart)
    elif chart.type ==  "pchart":
        generator = Pchart(chart)
    elif chart.type ==  "uchart":
        generator = Uchart(chart)
    elif chart.type ==  "boxplot1":
        generator = Boxplot1(chart)
    elif chart.type ==  "boxplot2":
        generator = Boxplot2(chart)
    elif chart.type ==  "boxplot3":
        generator = Boxplot3(chart)
    else:
        result.message = "not supported"
        result.status = 422
        return result

    fig = generator.process()
    fig.savefig(savePath)
    result.message = generator.getProcessMessage()
    return result



@app.get("/status")
async def ping():
    return {"status": "ok"}