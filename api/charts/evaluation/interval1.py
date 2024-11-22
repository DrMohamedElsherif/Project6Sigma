import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pydantic import BaseModel, Field
from typing import List, Dict
from api.schemas import BusinessLogicException
from api.charts.constants import FIGURE_SIZE_DEFAULT, COLOR_BLUE, TITLE_FONT_SIZE, TITLE_FONT_SIZE_SMALL, TITLE_PADDING


class Interval1Config(BaseModel):
    title: str


class Interval1Data(BaseModel):
    values: Dict[str, List[float]] = Field(..., min_length=1)


class Interval1Request(BaseModel):
    project: str
    step: str
    config: Interval1Config
    data: Interval1Data


class Interval1:
    def __init__(self, data: dict):
        try:
            validated_data = Interval1Request(**data)
            self.project = validated_data.project
            self.step = validated_data.step
            self.config = validated_data.config
            self.data = validated_data.data
            self.figure = None

        except ValueError as e:
            raise BusinessLogicException(
                error_code="validation_error",
                field=str(e),
                details={"message": f"Invalid or missing field: {str(e)}"}
            )

    def process(self):
        title = self.config.title

        # Create DataFrame from the input data
        df = pd.DataFrame(self.data.values)

        # Get the first column of data
        data = df.iloc[:, 0]

        # Calculate statistics
        mean = np.mean(data)
        stddev = np.std(data)
        confidence_interval = 1.96 * stddev / np.sqrt(len(data))

        # Create figure
        plt.figure(figsize=FIGURE_SIZE_DEFAULT)

        # Plot error bar
        plt.errorbar(
            x=1,
            y=mean,
            yerr=confidence_interval,
            fmt='o',
            capsize=15,
            color=COLOR_BLUE
        )

        # Set labels and title
        plt.ylabel('Value')
        plt.title(title, fontsize=TITLE_FONT_SIZE, pad=TITLE_PADDING)
        plt.figtext(
            0.5,
            0.05,
            df.columns[0],
            ha="center",
            fontsize=TITLE_FONT_SIZE_SMALL
        )

        # Hide x-axis labels
        plt.xticks([])

        # Enable grid
        plt.grid(True, which='both')

        self.figure = plt.gcf()
        return self.figure
