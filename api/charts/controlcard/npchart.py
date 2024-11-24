import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statistics
from pydantic import BaseModel, Field
from typing import List, Optional
from api.schemas import BusinessLogicException
from api.charts.constants import FIGURE_SIZE_DEFAULT


class NPchartConfig(BaseModel):
    title: str
    group_size: Optional[int] = Field(None, gt=0)


class NPchartData(BaseModel):
    defects: List[int] = Field(..., min_length=1)
    sample_sizes: Optional[List[int]] = None


class NPchartRequest(BaseModel):
    project: str
    step: str
    config: NPchartConfig
    data: NPchartData


class Npchart:
    def __init__(self, data: dict):
        try:
            validated_data = NPchartRequest(**data)
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
                field="data",
                details={"message": "Either group_size or sample_sizes must be provided"}
            )

        data = pd.DataFrame({
            'defects': defects,
            'group_size': sample_sizes,
            'np': [d / n for d, n in zip(defects, sample_sizes)]
        })

        np_mean = statistics.mean(data['np'])
        std_dev = np.sqrt((np_mean * (1 - np_mean)) / statistics.mean(data['group_size']))
        oeg = np_mean + 3 * std_dev
        ueg = np_mean - 3 * std_dev

        self.figure = plt.figure(figsize=FIGURE_SIZE_DEFAULT)
        plt.plot(data['np'], linestyle='-', marker='o', color='blue')
        plt.axhline(oeg, color='red', linestyle='dashed', label=f'OEG={round(oeg, 2)}')
        plt.axhline(np_mean, color='green', label=f'np={round(np_mean, 2)}')
        plt.axhline(ueg, color='red', linestyle='dashed', label=f'UEG={round(ueg, 2)}')

        plt.title(self.config.title, fontsize=28, pad=20)
        plt.xlabel('Sample')
        plt.ylabel('Sample Count')
        plt.legend(loc='upper right', framealpha=1)

        violations = data['np'][(data['np'] > oeg) | (data['np'] < ueg)].index
        if len(violations) > 0:
            self.message = f'Groups {list(violations)} out of fraction defective control limits!'
        else:
            self.message = 'All points within control limits.'

        plt.close('all')
        return self.figure
