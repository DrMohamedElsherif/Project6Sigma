import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statistics
from pydantic import BaseModel, Field
from typing import List

from api.charts.constants import FIGURE_SIZE_DEFAULT
from api.schemas import BusinessLogicException


class MRchartConfig(BaseModel):
    title: str


class MRchartData(BaseModel):
    values: List[float] = Field(..., min_length=2)  # Need at least 2 points for moving range


class MRchartRequest(BaseModel):
    project: str
    step: str
    config: MRchartConfig
    data: MRchartData


class Mrchart:
    def __init__(self, data: dict):
        try:
            validated_data = MRchartRequest(**data)
            self.project = validated_data.project
            self.step = validated_data.step
            self.config = validated_data.config
            self.data = validated_data.data
            self.message = ""
            self.figure = None

        except ValueError as e:
            # Extract the field name from the error message
            error_msg = str(e)

            # Determine error code based on the error type
            if "int_from_float" in error_msg:
                error_code = "error_must_be_integer"
            else:
                error_code = "error_validation"

            # Extract the field name from the error path
            if "data.values" in error_msg:
                field = "data"
            else:
                # Default to the first field mentioned in the error
                field = error_msg.split("\n")[1].split(".")[0] if "\n" in error_msg else "data"

            raise BusinessLogicException(
                error_code=error_code,
                field=field,
                details={"message": f"Invalid or missing field."}
            )

    def process(self):
        x = pd.Series(self.data.values)
        mr = pd.Series([np.nan] + [abs(x[i] - x[i - 1]) for i in range(1, len(x))])
        data = pd.DataFrame({'x': x, 'mR': mr})

        # Constants for control limits
        D4 = 3.267  # UCL factor for n=2
        D3 = 0  # LCL factor for n=2
        d2 = 1.128  # Factor for individual measurements

        # Calculate statistics
        x_mean = statistics.mean(data['x'])
        mr_mean = statistics.mean(data['mR'].dropna())

        # Control limits for Individual chart
        x_ucl = x_mean + 3 * mr_mean / d2
        x_lcl = x_mean - 3 * mr_mean / d2

        # Control limits for MR chart
        mr_ucl = D4 * mr_mean
        mr_lcl = D3 * mr_mean

        # Create subplots
        self.figure, (ax1, ax2) = plt.subplots(2, figsize=FIGURE_SIZE_DEFAULT, sharex=True)

        # Individual Values chart
        ax1.plot(data['x'], linestyle='-', marker='o', color='blue')
        ax1.axhline(x_ucl, color='red', linestyle='dashed', label=f'UCL={round(x_ucl, 3)}')
        ax1.axhline(x_mean, color='green', label=f'X={round(x_mean, 3)}')
        ax1.axhline(x_lcl, color='red', linestyle='dashed', label=f'LCL={round(x_lcl, 3)}')
        ax1.set_title(self.config.title, fontsize=28, pad=20)
        ax1.set(ylabel='Individual Value')
        ax1.legend(loc='upper right', framealpha=1)

        # Moving Range chart
        ax2.plot(data['mR'], linestyle='-', marker='o', color='blue')
        ax2.axhline(mr_ucl, color='red', linestyle='dashed', label=f'UCL={round(mr_ucl, 3)}')
        ax2.axhline(mr_mean, color='green', label=f'MR={round(mr_mean, 3)}')
        ax2.axhline(mr_lcl, color='red', linestyle='dashed', label=f'LCL={round(mr_lcl, 3)}')
        ax2.set(xlabel='Observation', ylabel='Moving Range')
        ax2.legend(loc='upper right', framealpha=1)

        # Check control limits
        x_violations = data['x'][(data['x'] > x_ucl) | (data['x'] < x_lcl)].index
        mr_violations = data['mR'][(data['mR'] > mr_ucl) | (data['mR'] < mr_lcl)].dropna().index

        if len(x_violations) > 0:
            self.message = f'Individual values out of control at points: {list(x_violations)}'
        elif len(mr_violations) > 0:
            self.message = f'Moving ranges out of control at points: {list(mr_violations)}'
        else:
            self.message = 'All points within control limits.'

        plt.close('all')
        return self.figure
