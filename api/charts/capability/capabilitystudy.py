import pandas as pd
from scipy.stats import normaltest, shapiro
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Union
from api.schemas import BusinessLogicException
from .continuous.normal import I_MR_chart
from .continuous.notnormal import I_MR_chart_transformed
from .discrete.pchart import P_chart
from .discrete.uchart import U_chart


class CapabilityConfig(BaseModel):
    title: str
    type: str = Field(..., pattern='^(pchart|uchart|continuous)$')
    target: Optional[float] = None
    acceptable_percent: Optional[float] = None
    acceptable_DPU: Optional[float] = None
    subgroup_size: Optional[int] = Field(None, gt=0)
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None

    @validator('subgroup_size', pre=True, always=True)
    def set_default_subgroup_size(cls, v, values):
        if v is None:
            if 'type' in values and values['type'] in ['pchart', 'uchart']:
                return 20
            return 1
        return v


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
        values = self.data.values
        data = pd.DataFrame({"value": values})

        if self.config.type == "continuous":
            if self.config.target is None:
                raise BusinessLogicException(
                    error_code="validation_error",
                    field="target",
                    details={"message": "Target is required for continuous data"}
                )
            if self.config.lower_bound is None or self.config.upper_bound is None:
                raise BusinessLogicException(
                    error_code="validation_error",
                    field="bounds",
                    details={"message": "Lower and upper bounds are required for continuous data"}
                )

            _, p_value_shapiro = shapiro(data.iloc[:, 0])
            _, p_value_normaltest = normaltest(data.iloc[:, 0])

            if p_value_shapiro > 0.05 and p_value_normaltest > 0.05:
                return I_MR_chart(data, self.config.title, target=self.config.target,
                                  subgroup_size=self.config.subgroup_size, USL=self.config.upper_bound,
                                  LSL=self.config.lower_bound)
            else:
                return I_MR_chart_transformed(data, self.config.title, target=self.config.target,
                                              subgroup_size=self.config.subgroup_size, LSL=self.config.lower_bound,
                                              USL=self.config.upper_bound)

        elif self.config.type == "pchart":
            if self.config.acceptable_percent is None:
                raise BusinessLogicException(
                    error_code="validation_error",
                    field="acceptable_percent",
                    details={"message": "Acceptable percent is required for p-chart"}
                )
            return P_chart(data, self.config.title,
                           acceptable_percent=self.config.acceptable_percent,
                           subgroup_size=self.config.subgroup_size)

        elif self.config.type == "uchart":
            if self.config.acceptable_DPU is None:
                raise BusinessLogicException(
                    error_code="validation_error",
                    field="acceptable_DPU",
                    details={"message": "Acceptable DPU is required for u-chart"}
                )
            return U_chart(data, self.config.title,
                           acceptable_DPU=self.config.acceptable_DPU,
                           subgroup_size=self.config.subgroup_size)