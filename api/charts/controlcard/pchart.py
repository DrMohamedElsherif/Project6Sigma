import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statistics
from pydantic import BaseModel, Field
from typing import List, Optional
from api.schemas import BusinessLogicException
from api.charts.constants import FIGURE_SIZE_A4_PORTRAIT


class PchartConfig(BaseModel):
    title: str
    group_size: Optional[int] = Field(None, gt=0)


class PchartData(BaseModel):
    defects: List[int] = Field(..., min_length=1)
    sample_sizes: Optional[List[int]] = None


class PchartRequest(BaseModel):
    project: str
    step: str
    config: PchartConfig
    data: PchartData


class Pchart:
    def __init__(self, data: dict):
        try:
            validated_data = PchartRequest(**data)
            self.project = validated_data.project
            self.step = validated_data.step
            self.config = validated_data.config
            self.data = validated_data.data
            self.message = ""
            self.figure = None

        except ValueError as e:
            error_msg = str(e)

            if "int_from_float" in error_msg:
                error_code = "error_must_be_integer"
            else:
                error_code = "error_validation"

            if "data.defects" in error_msg:
                field = "data"
            else:
                field = error_msg.split("\n")[1].split(".")[0] if "\n" in error_msg else "data"

            raise BusinessLogicException(
                error_code=error_code,
                field=field,
                details={"message": "Invalid or missing field."}
            )

    def process(self):
        defects = self.data.defects
        group_size = self.config.group_size
        sample_sizes = self.data.sample_sizes

        if group_size:
            sample_sizes = [group_size] * len(defects)
        elif not sample_sizes:
            raise BusinessLogicException(
                error_code="error_validation",
                details={"message": "Either group_size or sample_sizes must be provided"}
            )

        data = pd.DataFrame({
            'defects': defects,
            'group_size': sample_sizes,
            'p': [d / n for d, n in zip(defects, sample_sizes)]
        })

        p_mean = statistics.mean(data['p'])
        std_dev = np.sqrt((p_mean * (1 - p_mean)) / data['group_size'])
        oeg = p_mean + 3 * std_dev
        ueg = p_mean - 3 * std_dev

        self.figure = plt.figure(figsize=FIGURE_SIZE_A4_PORTRAIT)
        plt.subplots_adjust(top=0.85, bottom=0.4, left=0.15, right=0.85)
        plt.plot(data['p'], color='black', marker='o', lw=0.5)
        plt.step(x=range(len(data)), y=oeg, color='#a03130', linestyle='dashed',
                 label=f'OEG={round(float(oeg[0]), 3)}')
        plt.axhline(p_mean, color='grey', label=f'p={round(p_mean, 3)}', linestyle='dashed', alpha=0.7)
        plt.step(x=range(len(data)), y=ueg, color='#a03130', linestyle='dashed',
                 label=f'UEG={round(float(ueg[0]), 3)}')

        plt.title(self.config.title, fontsize=28, pad=20)
        plt.xlabel('Sample')
        plt.ylabel('Proportion')
        plt.grid(True, alpha=0.3)
        plt.legend(loc='upper right', framealpha=1)

        violations = data[data['p'].gt(p_mean + 3 * std_dev) |
                          data['p'].lt(p_mean - 3 * std_dev)].index
        if len(violations) > 0:
            self.message = f'Groups {list(violations)} out of fraction defective control limits!'
        else:
            self.message = 'All points within control limits.'

        plt.close('all')
        return self.figure
