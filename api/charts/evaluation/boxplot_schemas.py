# boxplot_schemas.py

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any


class BoxplotConfig(BaseModel):
    title: str


class BoxplotData(BaseModel):
    dataset_name: Optional[str] = "Dataset"
    values: Dict[str, List[float]] = Field(..., min_length=1)
    categories: Optional[Dict[str, List[str]]] = None



class BoxplotRequest(BaseModel):
    project: str
    step: str
    config: BoxplotConfig
    data: BoxplotData
