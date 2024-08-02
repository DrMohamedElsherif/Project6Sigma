from pydantic import BaseModel
from typing import Optional, Any
from .config import Config


class Chart(BaseModel):
    project: str
    step: str
    type: str
    description: Optional[str] = None
    config: Config
    data: Optional[Any] = None
    additional_data: Optional[Any] = None
    group_size: Optional[int] = None
