# main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from config import get_settings
from api.router import api_router
from api.schemas import BusinessLogicException, ErrorResponse

# App Konfiguration
app = FastAPI(
    title="six sigma charts",
    description="",
    version="0.0.1"
)

# CORS
origins = ["*", "*:*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception Handlers
@app.exception_handler(BusinessLogicException)
async def business_logic_exception_handler(request: Request, exc: BusinessLogicException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error_code=exc.error_code,
            field=exc.field,
            details=exc.details
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error_code="internal_server_error",
            details={"error": str(exc)}
        ).dict()
    )


# Statische Dateien
settings = get_settings()
# Updated to use staticFilePath instead of filePath
app.mount("/static", StaticFiles(directory=settings.staticFilePath), name="static")

# Router einbinden
app.include_router(api_router)
