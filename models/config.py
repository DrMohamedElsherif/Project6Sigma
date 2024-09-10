from pydantic import BaseModel
from typing import Optional

class Config(BaseModel):
    title: str
    type: Optional[str] = None
    labelx: Optional[str] = None
    labely: Optional[str] = None
    labels: Optional[list] = None

    # Controlcard and MSA
    trials: Optional[int] = None
    reference: Optional[float] = None
    tolerance: Optional[float] = None
    percentage_of_tolerance: Optional[float] = None
    lcl: Optional[float] = None
    ucl: Optional[float] = None

    # Capabilitystudy
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None
    target: Optional[float] = None
    subgroup_size: Optional[int] = None
    acceptable_percent: Optional[float] = None
    acceptable_DPU: Optional[float] = None
