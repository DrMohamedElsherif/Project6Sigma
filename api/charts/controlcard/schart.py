import statistics
from typing import List, Optional

import matplotlib.pyplot as plt
import numpy as np
from pydantic import BaseModel, Field

from api.charts.constants import FIGURE_SIZE_A4_PORTRAIT
from api.schemas import BusinessLogicException


class SchartConfig(BaseModel):
    title: str
    group_size: Optional[int] = Field(None, gt=0)


class SchartData(BaseModel):
    values: List[float] = Field(..., min_length=2)
    subgroups: Optional[List[List[float]]] = None


class SchartRequest(BaseModel):
    project: str
    step: str
    config: SchartConfig
    data: SchartData


class Schart:
    def __init__(self, data: dict):
        try:
            validated_data = SchartRequest(**data)
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

            if "data.values" in error_msg:
                field = "data"
            else:
                field = error_msg.split("\n")[1].split(".")[0] if "\n" in error_msg else "data"

            raise BusinessLogicException(
                error_code=error_code,
                field=field,
                details={"message": "Invalid or missing field."}
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
        A3 = 0.927  # Factor for Xbar chart
        B4 = 1.649  # Upper factor for S chart
        B3 = 0.321  # Lower factor for S chart

        # Calculate statistics
        x_bars = [np.mean(group) for group in subgroups if len(group) > 1]
        stdevs = [np.std(group, ddof=1) for group in subgroups if len(group) > 1]

        x_mean = statistics.mean(x_bars)
        s_mean = statistics.mean(stdevs)

        # Control limits
        x_ucl = x_mean + A3 * s_mean
        x_lcl = x_mean - A3 * s_mean
        s_ucl = B4 * s_mean
        s_lcl = B3 * s_mean

        # Create plots
        self.figure, (ax1, ax2) = plt.subplots(2, figsize=FIGURE_SIZE_A4_PORTRAIT)
        self.figure.subplots_adjust(top=0.85, bottom=0.15, left=0.15, right=0.85)

        # X-bar chart
        ax1.plot(x_bars, color='black', marker='o', lw=0.5)
        ax1.axhline(x_ucl, color='#a03130', linestyle='dashed', label=f'UCL={round(x_ucl, 3)}')
        ax1.axhline(x_mean, color='grey', label=f'X={round(x_mean, 3)}', linestyle='dashed', alpha=0.7)
        ax1.axhline(x_lcl, color='#a03130', linestyle='dashed', label=f'LCL={round(x_lcl, 3)}')
        ax1.set_title(self.config.title, fontsize=28, pad=20)
        ax1.set(ylabel='Sample Mean')
        ax1.grid(True, alpha=0.3)
        ax1.legend(loc='upper right', framealpha=1)

        # S chart
        ax2.plot(stdevs, color='black', marker='o', lw=0.5)
        ax2.axhline(s_ucl, color='#a03130', linestyle='dashed', label=f'UCL={round(s_ucl, 3)}')
        ax2.axhline(s_mean, color='grey', label=f'S={round(s_mean, 3)}', linestyle='dashed', alpha=0.7)
        ax2.axhline(s_lcl, color='#a03130', linestyle='dashed', label=f'LCL={round(s_lcl, 3)}')
        ax2.set(xlabel='Sample', ylabel='Standard Deviation')
        ax2.grid(True, alpha=0.3)
        ax2.legend(loc='upper right', framealpha=1)

        # Check control limits
        x_violations = [i for i, x in enumerate(x_bars) if x > x_ucl or x < x_lcl]
        s_violations = [i for i, s in enumerate(stdevs) if s > s_ucl or s < s_lcl]

        if x_violations:
            self.message = f'Groups {x_violations} out of mean control limits!'
        elif s_violations:
            self.message = f'Groups {s_violations} out of standard deviation control limits!'
        else:
            self.message = 'All points within control limits.'

        plt.close('all')
        return self.figure
