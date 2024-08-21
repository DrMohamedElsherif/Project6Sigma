from pydantic import BaseModel
from typing import Optional

class Config(BaseModel):
    title: str
    labelx: Optional[str] = None
    labely: Optional[str] = None
    labels: Optional[list] = None
    trials: Optional[int] = None
    reference: Optional[float] = None
    tolerance: Optional[float] = None
    percentage_of_tolerance: Optional[float] = None
    lcl: Optional[float] = None
    ucl: Optional[float] = None
