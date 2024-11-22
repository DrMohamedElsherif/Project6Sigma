import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from pydantic import BaseModel, Field
from typing import List, Dict
from api.schemas import BusinessLogicException
from api.charts.constants import TITLE_FONT_SIZE, MARKERS, COLORS


class Matrixplot4Config(BaseModel):
    title: str


class Matrixplot4Data(BaseModel):
    values: Dict[str, List[float]] = Field(..., min_length=1)
    groups: List[str] = Field(..., min_length=1)  # Group labels
    group_variable: str  # Name of the grouping variable
    x_vars: List[str] = Field(..., min_length=1)
    y_vars: List[str] = Field(..., min_length=1)


class Matrixplot4Request(BaseModel):
    project: str
    step: str
    config: Matrixplot4Config
    data: Matrixplot4Data


class Matrixplot4:
    def __init__(self, data: dict):
        try:
            validated_data = Matrixplot4Request(**data)
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

        # Create dataframe from values
        df = pd.DataFrame(self.data.values)

        # Add group variable
        df[self.data.group_variable] = self.data.groups

        # Set style
        sns.set(style="whitegrid")

        # Get number of unique groups
        num_unique = len(set(self.data.groups))

        # Create pairplot with specified variables and groups
        pair_plot = sns.pairplot(
            df,
            hue=self.data.group_variable,
            diag_kind="kde",
            y_vars=self.data.y_vars,
            x_vars=self.data.x_vars,
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
