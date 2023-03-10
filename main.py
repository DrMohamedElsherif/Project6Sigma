from fastapi import FastAPI, File, Form, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv
import os
import uuid
import sys
from functools import reduce

from models.chart import Chart
from models.chartresult import ChartResult
#from charts.controlcard.mrchart import Mrchart
#from charts.controlcard.cchart import Cchart
#from charts.controlcard.npchart import Npchart
#from charts.controlcard.rchart import Rchart
#from charts.controlcard.schart import Schart
#from charts.controlcard.pchart import Pchart
#from charts.controlcard.uchart import Uchart
#from charts.evaluation.boxplot1 import Boxplot1
#from charts.evaluation.boxplot2 import Boxplot2
#from charts.evaluation.boxplot3 import Boxplot3
#from charts.evaluation.individual1 import Individual1
#from charts.evaluation.individual2 import Individual2
#from charts.evaluation.individual3 import Individual3
#from charts.evaluation.individual4 import Individual4

from charts import *
from charts.controlcard import *
from charts.evaluation import *


#from charts.constants import *
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

def str_to_class(str):
    return reduce(getattr, str.split("."), sys.modules[__name__])

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

    tmp, file_extension = os.path.splitext(file.filename)
    filename = str(uuid.uuid4()) + file_extension
    savePath = projectPath + "/" + filename;
    url = staticUrl + "/" + project + "/" + step  + "/" + filename
    
    with open(savePath, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)

    return { "filename": filename, 
            "url" : url }


@app.post("/chart", response_model=ChartResult)
async def generate(chart: Chart):
    projectPath = filePath + "/" + chart.project + "/" + chart.step 
    # check if dir exists
    if not os.path.exists(projectPath):
        os.makedirs(projectPath)

    filename = str(uuid.uuid4()) + "." + constants.CHART_EXTENSION
    savePath = projectPath + "/" + filename;
    result = ChartResult()
    
    try:
        chartclass = str_to_class(chart.type + "." + chart.type)
    except AttributeError:
        chartclass = None

    if (chartclass):
            generator = chartclass(chart)
    else: 
        result.message = "not supported"
        result.status = 422
        return result
   
    fig = generator.process()
    fig.savefig(savePath)
    result.message = generator.getProcessMessage()
    result.url = staticUrl + "/" + chart.project + "/" + chart.step + "/" + filename
    result.status = 200;

    return result



@app.get("/status")
async def ping():
    return {"status": "ok"}