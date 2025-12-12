from pydantic import BaseModel, Field
from typing import Dict, List, Optional

class BoxplotConfig(BaseModel):
    title: str

class BoxplotData(BaseModel):
    values: Dict[str, List[float]] = Field(..., min_length=1)

class BoxplotCategoryData(BoxplotData):
    categories: Optional[Dict[str, List[str]]] = None

class BoxplotRequest(BaseModel):
    project: str
    step: str
    config: BoxplotConfig
    data: BoxplotData

class Boxplot5Request(BaseModel):
    project: str
    step: str
    config: BoxplotConfig
    data: BoxplotCategoryData
