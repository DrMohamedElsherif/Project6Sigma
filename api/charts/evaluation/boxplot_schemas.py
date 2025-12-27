# boxplot_schemas.py
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Literal
class BoxplotConfig(BaseModel):
    title: str
    variant: Literal[
        "single",
        "faceted_by_group",
        "multipanel_columns"
    ]
class BoxplotData(BaseModel):
    dataset_name: Optional[str] = "Dataset"
    values: Dict[str, List[float]] = Field(..., min_length=1)
    categories: Optional[Dict[str, List[str]]] = None
class BoxplotRequest(BaseModel):
    project: str
    step: str
    config: BoxplotConfig
    data: BoxplotData



