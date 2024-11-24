import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statistics
from pydantic import BaseModel, Field
from typing import List, Optional
from api.schemas import BusinessLogicException
from api.charts.constants import FIGURE_SIZE_DEFAULT


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
            raise BusinessLogicException(
                error_code="error_validation",
                field=str(e),
                details={"message": f"Invalid or missing field: {str(e)}"}
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

        self.figure = plt.figure(figsize=FIGURE_SIZE_DEFAULT)
        plt.plot(data['p'], linestyle='-', marker='o', color='blue')
        plt.step(x=range(len(data)), y=oeg, color='red', linestyle='dashed',
                 label=f'OEG={round(float(oeg[0]), 3)}')
        plt.axhline(p_mean, color='green', label=f'p={round(p_mean, 3)}')
        plt.step(x=range(len(data)), y=ueg, color='red', linestyle='dashed',
                 label=f'UEG={round(float(ueg[0]), 3)}')

        plt.title(self.config.title, fontsize=28, pad=20)
        plt.xlabel('Sample')
        plt.ylabel('Proportion')
        plt.legend(loc='upper right', framealpha=1)

        violations = data[data['p'].gt(p_mean + 3 * std_dev) |
                          data['p'].lt(p_mean - 3 * std_dev)].index
        if len(violations) > 0:
            self.message = f'Groups {list(violations)} out of fraction defective control limits!'
        else:
            self.message = 'All points within control limits.'

        plt.close('all')
        return self.figure
