from pydantic import BaseModel
from typing import Optional


class ChartResult(BaseModel):
    status: Optional[int]
    message: Optional[str]
    url: Optional[str]
