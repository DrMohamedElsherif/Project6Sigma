import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pydantic import BaseModel, Field
from typing import List, Dict
from api.schemas import BusinessLogicException
from api.charts.constants import FIGURE_SIZE_DEFAULT, TITLE_FONT_SIZE, TITLE_PADDING


class Interval2Config(BaseModel):
    title: str


class Interval2Data(BaseModel):
    values: Dict[str, List[float]] = Field(..., min_length=1)


class Interval2Request(BaseModel):
    project: str
    step: str
    config: Interval2Config
    data: Interval2Data


class Interval2:
    def __init__(self, data: dict):
        try:
            validated_data = Interval2Request(**data)
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

        # Create figure
        plt.figure(figsize=FIGURE_SIZE_DEFAULT)

        # Process each column
        for index, column in enumerate(df):
            # Calculate statistics
            mean = np.mean(df[column])
            stddev = np.std(df[column])
            confidence_interval = 1.96 * stddev / np.sqrt(len(df[column]))

            # Plot error bar
            plt.errorbar(
                x=index,
                y=mean,
                yerr=confidence_interval,
                fmt='o',
                capsize=15,
                label=column
            )

        # Set labels and title
        plt.ylabel('Values')
        plt.title(title, fontsize=TITLE_FONT_SIZE, pad=TITLE_PADDING)

        # Hide x-axis labels
        plt.xticks([])

        # Add legend
        plt.legend(loc='best')

        # Enable grid
        plt.grid(True, which='both')

        self.figure = plt.gcf()
        return self.figure
