from fastapi import HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any


class ErrorResponse(BaseModel):
    success: bool = False
    error_code: str
    field: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class SuccessResponse(BaseModel):
    success: bool = True
    data: Dict[str, Any]


class BusinessLogicException(HTTPException):
    def __init__(
            self,
            error_code: str,
            field: Optional[str] = None,
            details: Optional[Dict[str, Any]] = None,
            status_code: int = 400
    ):
        self.error_code = error_code
        self.field = field
        self.details = details
        super().__init__(status_code=status_code)
