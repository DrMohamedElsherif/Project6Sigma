import statistics
from typing import List, Optional

import matplotlib.pyplot as plt
import numpy as np
from pydantic import BaseModel, Field

from api.charts.constants import FIGURE_SIZE_DEFAULT
from api.schemas import BusinessLogicException


class RchartConfig(BaseModel):
    title: str
    group_size: Optional[int] = Field(None, gt=0)


class RchartData(BaseModel):
    values: List[float] = Field(..., min_length=2)
    subgroups: Optional[List[List[float]]] = None


class RchartRequest(BaseModel):
    project: str
    step: str
    config: RchartConfig
    data: RchartData


class Rchart:
    def __init__(self, data: dict):
        try:
            validated_data = RchartRequest(**data)
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

    def _create_subgroups(self, data, group_size):
        n = len(data)
        return [data[i:i + group_size] for i in range(0, n, group_size)]

    def process(self):
        values = self.data.values
        group_size = self.config.group_size
        subgroups = self.data.subgroups

        if group_size:
            subgroups = self._create_subgroups(values, group_size)
        elif not subgroups:
            raise BusinessLogicException(
                error_code="error_validation",
                details={"message": "Either group_size or subgroups must be provided"}
            )

        # Constants for control limits
        A2 = 0.577  # Factor for Xbar chart
        D4 = 2.574  # Factor for R chart
        D3 = 0  # Factor for R chart

        # Calculate statistics
        x_bars = [np.mean(group) for group in subgroups if len(group) > 1]
        ranges = [max(group) - min(group) for group in subgroups if len(group) > 1]

        x_mean = statistics.mean(x_bars)
        r_mean = statistics.mean(ranges)

        # Control limits
        x_ucl = x_mean + A2 * r_mean
        x_lcl = x_mean - A2 * r_mean
        r_ucl = D4 * r_mean
        r_lcl = D3 * r_mean

        # Create plots
        self.figure, (ax1, ax2) = plt.subplots(2, figsize=FIGURE_SIZE_DEFAULT)

        # X-bar chart
        ax1.plot(x_bars, linestyle='-', marker='o', color='blue')
        ax1.axhline(x_ucl, color='red', linestyle='dashed', label=f'UCL={round(x_ucl, 3)}')
        ax1.axhline(x_mean, color='green', label=f'X={round(x_mean, 3)}')
        ax1.axhline(x_lcl, color='red', linestyle='dashed', label=f'LCL={round(x_lcl, 3)}')
        ax1.set_title(self.config.title, fontsize=28, pad=20)
        ax1.set(ylabel='Sample Mean')
        ax1.legend(loc='upper right', framealpha=1)

        # R chart
        ax2.plot(ranges, linestyle='-', marker='o', color='blue')
        ax2.axhline(r_ucl, color='red', linestyle='dashed', label=f'UCL={round(r_ucl, 3)}')
        ax2.axhline(r_mean, color='green', label=f'R={round(r_mean, 3)}')
        ax2.axhline(r_lcl, color='red', linestyle='dashed', label=f'LCL={round(r_lcl, 3)}')
        ax2.set(xlabel='Sample', ylabel='Sample Range')
        ax2.legend(loc='upper right', framealpha=1)

        # Check control limits
        x_violations = [i for i, x in enumerate(x_bars) if x > x_ucl or x < x_lcl]
        r_violations = [i for i, r in enumerate(ranges) if r > r_ucl or r < r_lcl]

        if x_violations:
            self.message = f'Groups {x_violations} out of mean control limits!'
        elif r_violations:
            self.message = f'Groups {r_violations} out of range control limits!'
        else:
            self.message = 'All points within control limits.'

        return self.figure
