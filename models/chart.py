from pydantic import BaseModel
from typing import Optional
from .config import Config

class Chart(BaseModel):
    project: str
    step: str
    type: str
    description: Optional[str] = None
    config: Config
    data: Optional[list] = None
    group_size: Optional[int] = None