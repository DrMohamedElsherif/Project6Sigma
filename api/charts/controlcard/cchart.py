import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statistics
from pydantic import BaseModel, Field
from typing import List

from api.charts.constants import FIGURE_SIZE_A4_PORTRAIT
from api.schemas import BusinessLogicException


class CchartConfig(BaseModel):
    title: str


class CchartData(BaseModel):
    values: List[int] = Field(..., min_length=1)


class CchartRequest(BaseModel):
    project: str
    step: str
    config: CchartConfig
    data: CchartData


class Cchart:
    def __init__(self, data: dict):
        try:
            validated_data = CchartRequest(**data)
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
        title = self.config.title
        data = self.data.values
        data_length = len(data)
        group_size = [data_length] * data_length

        c = pd.DataFrame({
            'defects': list(np.array(data)),
            'group_size': list(np.array(group_size))
        })

        self.figure = plt.figure(figsize=FIGURE_SIZE_A4_PORTRAIT)

        plt.subplots_adjust(top=0.85, bottom=0.4, left=0.1, right=0.9)

        plt.plot(c['defects'], color='black', marker='o', lw=0.5)

        C = statistics.mean(c['defects'])
        OEG = C + 3 * np.sqrt(C)
        UEG = C - 3 * np.sqrt(C)

        plt.axhline(OEG, color='red', linestyle='dashed',
                    label=f'OEG={round(OEG, 2)}')
        plt.axhline(C, color='grey', label=f'C={round(C, 1)}', linestyle='dashed', alpha=0.7)
        plt.axhline(UEG, color='red', linestyle='dashed',
                    label=f'UEG={round(UEG, 2)}')
        plt.title(title, fontsize=28, pad=20)
        plt.xlabel('Sample')
        plt.ylabel('Defect Count')
        plt.legend(loc='upper right', framealpha=1)
        plt.grid(True, alpha=0.3)

        control = True
        for i, group in enumerate(c['defects']):
            if group > OEG or group < UEG:
                self.message = f'Group {i} out of defects control limits!'
                control = False
                break

        if control:
            self.message = 'All points within control limits.'

        plt.close('all')
        return self.figure
