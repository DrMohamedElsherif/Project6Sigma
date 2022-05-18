from pydantic import BaseModel
from typing import Optional

class Config(BaseModel):
    title: str
    labelx: Optional[str] = None
    labely: Optional[str] = None