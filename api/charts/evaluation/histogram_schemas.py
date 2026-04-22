# api/charts/evaluation/histogram_schemas.py

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Literal


class HistogramConfig(BaseModel):
    title: str
    mode: Literal["single", "stacked", "subplots"] = "single"
    labelx: Optional[str] = "Data"
    labely: Optional[str] = "Frequency"
    bins: Optional[int] = None
    show_stats: Optional[bool] = False


class HistogramData(BaseModel):
    values: Dict[str, List[float]] = Field(..., min_length=1)


class HistogramRequest(BaseModel):
    project: str
    step: str
    config: HistogramConfig
    data: HistogramData