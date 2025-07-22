import pandas as pd
import matplotlib.pyplot as plt
from pydantic import BaseModel, Field
from typing import List, Dict
from api.schemas import BusinessLogicException
from api.charts.constants import COLOR_BLUE, FIGURE_SIZE_A4_PORTRAIT, COLOR_BLACK, TITLE_FONT_SIZE
import seaborn as sns


class Boxplot6Config(BaseModel):
    title: str


class Boxplot6Data(BaseModel):
    values: Dict[str, List[float]] = Field(..., min_length=1)


class Boxplot6Request(BaseModel):
    project: str
    step: str
    config: Boxplot6Config
    data: Boxplot6Data


class Boxplot6:
    def __init__(self, data: dict):
        try:
            validated_data = Boxplot6Request(**data)
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

        # Define the column count
        num_columns = 2

        # Count the number of columns
        num_datasets = len(df.columns)

        # Find the number of rows needed
        num_rows = num_datasets // 2 + num_datasets % 2

        self.figure = plt.figure(figsize=FIGURE_SIZE_A4_PORTRAIT)

        # Create subplot for each column
        for idx, column in enumerate(df.columns, 1):
            ax = self.figure.add_subplot(num_rows, num_columns, idx)
            sns.boxplot(
                data=df[column],
                color="#a1d111",
                linewidth=1,
                flierprops={"marker": "x"},
                showcaps=False,
                width=0.3,
                ax=ax,
                boxprops=dict(edgecolor='black')
            )
            ax.set_title(column)
            ax.grid(True, alpha=0.3)

        # Set main title for plot
        plt.suptitle(title, fontsize=TITLE_FONT_SIZE)
        plt.tight_layout(pad=2.0)
        plt.subplots_adjust(left=0.15, right=0.85, top=0.88, bottom=0.08)
        plt.close('all')
        return self.figure
