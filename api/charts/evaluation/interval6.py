import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pydantic import BaseModel, Field
from typing import List, Dict
from api.schemas import BusinessLogicException
from api.charts.constants import FIGURE_SIZE_A4_PORTRAIT, TITLE_FONT_SIZE


class Interval6Config(BaseModel):
    title: str


class Interval6Data(BaseModel):
    values: Dict[str, List[float]] = Field(..., min_length=1)


class Interval6Request(BaseModel):
    project: str
    step: str
    config: Interval6Config
    data: Interval6Data


class Interval6:
    def __init__(self, data: dict):
        try:
            validated_data = Interval6Request(**data)
            self.project = validated_data.project
            self.step = validated_data.step
            self.config = validated_data.config
            self.data = validated_data.data
            self.figure = None
        except ValueError as e:
            raise BusinessLogicException(
                error_code="error_validation",
                field=str(e),
                details={"message": f"Invalid or missing field: {str(e)}"}
            )

    def process(self):
        title = self.config.title
        df = pd.DataFrame(self.data.values)

        # Calculate subplot layout
        num_plots = len(df.columns)
        num_cols = 2
        num_rows = (num_plots + num_cols - 1) // num_cols

        # Create figure
        self.figure = plt.figure(figsize=FIGURE_SIZE_A4_PORTRAIT)
        plt.suptitle(title, fontsize=TITLE_FONT_SIZE, y=0.95)
        plt.subplots_adjust(top=0.85, bottom=0.1, left=0.15, right=0.85)

        # Create subplots for each column
        for index, column in enumerate(df.columns):
            # Calculate statistics
            mean = np.mean(df[column])
            stddev = np.std(df[column])
            confidence_interval = 1.96 * stddev / np.sqrt(len(df[column]))

            # Create subplot
            ax = plt.subplot(num_rows, num_cols, index + 1)

            # Plot data with error bars
            ax.errorbar(
                x=index,
                y=mean,
                yerr=confidence_interval,
                fmt='o',
                capsize=15,
                color='black',
            )

            # Customize subplot
            ax.set_title(column)
            ax.set_xticks([])
            ax.grid(True)

        #plt.tight_layout()
        plt.close('all')
        return self.figure
