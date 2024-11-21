import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statistics
from pydantic import BaseModel, Field
from typing import List

from api.charts.constants import FIGURE_SIZE_DEFAULT
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
            raise BusinessLogicException(
                error_code="validation_error",
                field=str(e),
                details={"message": f"Invalid or missing field: {str(e)}"}
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

        self.figure = plt.figure(figsize=FIGURE_SIZE_DEFAULT)

        plt.plot(c['defects'], linestyle='-', marker='o', color='blue')

        C = statistics.mean(c['defects'])
        OEG = C + 3 * np.sqrt(C)
        UEG = C - 3 * np.sqrt(C)

        plt.axhline(OEG, color='red', linestyle='dashed',
                    label=f'OEG={round(OEG, 2)}')
        plt.axhline(C, color='green', label=f'C={round(C, 1)}')
        plt.axhline(UEG, color='red', linestyle='dashed',
                    label=f'UEG={round(UEG, 2)}')
        plt.title(title, fontsize=28, pad=20)
        plt.xlabel('Sample')
        plt.ylabel('Defect Count')
        plt.legend(loc='upper right', framealpha=1)

        control = True
        for i, group in enumerate(c['defects']):
            if group > OEG or group < UEG:
                self.message = f'Group {i} out of defects control limits!'
                control = False
                break

        if control:
            self.message = 'All points within control limits.'

        return self.figure
