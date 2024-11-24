import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pydantic import BaseModel, Field
from typing import List, Dict
from api.schemas import BusinessLogicException
from api.charts.constants import FIGURE_SIZE_DEFAULT, TITLE_FONT_SIZE, TITLE_PADDING


class Interval4Config(BaseModel):
    title: str


class Interval4Data(BaseModel):
    values: Dict[str, List[float]] = Field(..., min_length=1)


class Interval4Request(BaseModel):
    project: str
    step: str
    config: Interval4Config
    data: Interval4Data


class Interval4:
    def __init__(self, data: dict):
        try:
            validated_data = Interval4Request(**data)
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

        # Define size of figure
        self.figure = plt.figure(figsize=FIGURE_SIZE_DEFAULT)
        ax = self.figure.add_subplot(111)

        # Loop over columns and generate plots
        for index, column in enumerate(df):
            # Calculate means and standard deviations
            mean = np.mean(df[column])
            stddev = np.std(df[column])
            confidence_interval = 1.96 * stddev / np.sqrt(len(df[column]))

            # Plot data with error bars
            ax.errorbar(
                x=index,
                y=mean,
                yerr=confidence_interval,
                fmt='o',
                capsize=15,
                label=column
            )

            # Add labels and formatting
            ax.set_ylabel('Values')
            ax.set_xticks([])  # Hide x-axis labels
            ax.set_title(title, fontsize=TITLE_FONT_SIZE, pad=TITLE_PADDING)
            ax.legend(loc='best')
            ax.grid(True)  # Corrected grid parameter

        # Adjust layout
        plt.tight_layout()

        return self.figure
