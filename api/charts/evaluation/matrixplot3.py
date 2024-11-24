import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from pydantic import BaseModel, Field
from typing import List, Dict
from api.schemas import BusinessLogicException
from api.charts.constants import TITLE_FONT_SIZE


class Matrixplot3Config(BaseModel):
    title: str


class Matrixplot3Data(BaseModel):
    values: Dict[str, List[float]] = Field(..., min_length=1)
    x_vars: List[str] = Field(..., min_length=1)
    y_vars: List[str] = Field(..., min_length=1)


class Matrixplot3Request(BaseModel):
    project: str
    step: str
    config: Matrixplot3Config
    data: Matrixplot3Data


class Matrixplot3:
    def __init__(self, data: dict):
        try:
            validated_data = Matrixplot3Request(**data)
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

        # Create dataframe from values
        df = pd.DataFrame(self.data.values)

        # Set style
        sns.set(style="whitegrid")

        # Create pairplot with specified x and y variables
        pair_plot = sns.pairplot(
            df,
            diag_kind="none",
            y_vars=self.data.y_vars,
            x_vars=self.data.x_vars,
            height=1.8,
            aspect=1.8
        )

        # Add title
        pair_plot.fig.suptitle(title, fontsize=TITLE_FONT_SIZE)

        # Adjust layout
        plt.subplots_adjust(top=0.9)

        self.figure = pair_plot.fig
        plt.close('all')
        return self.figure
