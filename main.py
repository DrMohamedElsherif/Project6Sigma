from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv
import os
import uuid

from models.chart import Chart
from models.chartresult import ChartResult
from charts.mrchart import Mrchart
from charts.cchart import Cchart
from charts.npchart import Npchart
from charts.rchart import Rchart
from charts.schart import Schart
from charts.pchart import Pchart
from charts.uchart import Uchart

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

@app.post("/chart", response_model=ChartResult)
async def generate(chart: Chart):
    filename = str(uuid.uuid4()) + ".jpg"
    savePath = str(filePath) + "/" + filename;
    result = ChartResult()
    result.url = staticUrl + "/" + filename
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
    else:
        result.message = "not supported"
        result.status = 422
        return result

    fig = generator.process()
    fig.savefig(savePath)
    result.message = generator.getProcessMessage()
    return result
