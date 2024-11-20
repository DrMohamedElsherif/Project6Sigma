from pydantic import BaseModel
from typing import Optional, Any, Dict


class BaseChart(BaseModel):
    project: str
    step: str
    config: Dict[str, Any]
    data: Optional[Dict[str, Any]] = None
