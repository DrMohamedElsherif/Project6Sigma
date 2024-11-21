import pandas as pd
from scipy.stats import normaltest, shapiro
from pydantic import BaseModel, Field
from typing import List, Optional, Union
from api.schemas import BusinessLogicException
from .continuous.normal import I_MR_chart
from .continuous.notnormal import I_MR_chart_transformed
from .discrete.pchart import P_chart
from .discrete.uchart import U_chart


class CapabilityConfig(BaseModel):
    title: str
    target: Optional[float] = None
    acceptable_percent: Optional[float] = None
    acceptable_DPU: Optional[float] = None
    subgroup_size: int = Field(default=1, gt=0)
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None
    type: Optional[str] = Field(None, pattern='^(pchart|uchart)$')


class CapabilityData(BaseModel):
    values: List[Union[float, int]] = Field(..., min_length=1)


class CapabilityRequest(BaseModel):
    project: str
    step: str
    config: CapabilityConfig
    data: CapabilityData


class CapabilityStudy:
    def __init__(self, data: dict):
        try:
            validated_data = CapabilityRequest(**data)
            self.project = validated_data.project
            self.step = validated_data.step
            self.config = validated_data.config
            self.data = validated_data.data
            self.message = ""
            self.figure = None

        except ValueError as e:
            raise BusinessLogicException(
                error_code="validation_error",
                field=str(e),
                details={"message": f"Invalid or missing field: {str(e)}"}
            )

    def process(self):
        target = self.config.target
        acceptable_percent = self.config.acceptable_percent
        acceptable_DPU = self.config.acceptable_DPU
        subgroup_size = self.config.subgroup_size
        values = self.data.values
        lsl = self.config.lower_bound
        usl = self.config.upper_bound
        chart_type = self.config.type

        data = pd.DataFrame({"value": values})

        if isinstance(values[0], float):
            subgroup_size = 1
            _, p_value_shapiro = shapiro(data.iloc[:, 0])
            _, p_value_normaltest = normaltest(data.iloc[:, 0])

            if p_value_shapiro > 0.05 and p_value_normaltest > 0.05:
                return I_MR_chart(data, self.config.title, target=target,
                                  subgroup_size=subgroup_size, USL=usl, LSL=lsl)
            else:
                return I_MR_chart_transformed(data, self.config.title, target=target,
                                              subgroup_size=subgroup_size, LSL=lsl, USL=usl)
        else:
            if chart_type == "pchart":
                return P_chart(data, self.config.title,
                               acceptable_percent=acceptable_percent,
                               subgroup_size=subgroup_size)
            elif chart_type == "uchart":
                return U_chart(data, self.config.title,
                               acceptable_DPU=acceptable_DPU,
                               subgroup_size=subgroup_size)
