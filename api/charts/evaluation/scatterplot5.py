import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pydantic import BaseModel, Field
from typing import List, Dict
from api.schemas import BusinessLogicException
from api.charts.constants import TITLE_FONT_SIZE


class Scatterplot5Config(BaseModel):
    title: str


class Scatterplot5Data(BaseModel):
    values: Dict[str, List[float]] = Field(..., min_length=1)


class Scatterplot5AdditionalData(BaseModel):
    xVar: str
    yVars: List[str]


class Scatterplot5Request(BaseModel):
    project: str
    step: str
    config: Scatterplot5Config
    data: Scatterplot5Data
    additional_data: Scatterplot5AdditionalData


class Scatterplot5:
    def __init__(self, data: dict):
        try:
            validated_data = Scatterplot5Request(**data)
            self.project = validated_data.project
            self.step = validated_data.step
            self.config = validated_data.config
            self.data = validated_data.data
            self.additional_data = validated_data.additional_data
            self.figure = None

        except ValueError as e:
            raise BusinessLogicException(
                error_code="validation_error",
                field=str(e),
                details={"message": f"Invalid or missing field: {str(e)}"}
            )

    def process(self):
        title = self.config.title
        df = pd.DataFrame(self.data.values)

        num_plots = len(self.additional_data.yVars)
        num_cols = 2
        num_rows = (num_plots + num_cols - 1) // num_cols

        self.figure, axes = plt.subplots(num_rows, num_cols, figsize=(15, num_rows * 5))
        axes = axes.flatten()

        for i, y_variable in enumerate(self.additional_data.yVars):
            ax = axes[i]
            sns.scatterplot(
                data=df,
                x=self.additional_data.xVar,
                y=y_variable,
                ax=ax,
                zorder=3
            )
            ax.grid(True, axis='both', zorder=-1)

        # Remove extra subplots
        for i in range(num_plots, len(axes)):
            self.figure.delaxes(axes[i])

        plt.tight_layout()
        plt.subplots_adjust(top=0.9)
        plt.suptitle(title, fontsize=TITLE_FONT_SIZE, y=0.98)

        return self.figure
