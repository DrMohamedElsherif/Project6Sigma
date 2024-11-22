import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from pydantic import BaseModel, Field
from typing import List, Dict, Union
from api.schemas import BusinessLogicException
from api.charts.constants import TITLE_FONT_SIZE, MARKERS, COLORS


class Matrixplot2Config(BaseModel):
    title: str


class Matrixplot2Data(BaseModel):
    values: Dict[str, List[float]] = Field(..., min_length=2)  # Numerical variables
    groups: List[str] = Field(..., min_length=1)  # Group labels
    group_variable: str  # Name of the grouping variable


class Matrixplot2Request(BaseModel):
    project: str
    step: str
    config: Matrixplot2Config
    data: Matrixplot2Data


class Matrixplot2:
    def __init__(self, data: dict):
        try:
            validated_data = Matrixplot2Request(**data)
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

        # Create dataframe from numerical values
        df = pd.DataFrame(self.data.values)

        # Add group variable
        df[self.data.group_variable] = self.data.groups

        # Set style
        sns.set(style="whitegrid")

        # Get number of unique groups
        num_unique = len(set(self.data.groups))

        # Create scatterplot matrix with groups
        pair_plot = sns.pairplot(
            df,
            hue=self.data.group_variable,
            diag_kind="kde",
            markers=MARKERS[0:num_unique],
            palette=COLORS[0:num_unique],
            height=1.8,
            aspect=1.8
        )

        # Add title
        pair_plot.fig.suptitle(title, fontsize=TITLE_FONT_SIZE)

        # Adjust layout
        plt.subplots_adjust(top=0.9)

        self.figure = pair_plot.fig
        return self.figure
