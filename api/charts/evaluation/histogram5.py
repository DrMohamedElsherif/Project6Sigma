import pandas as pd
import matplotlib.pyplot as plt
from pydantic import BaseModel, Field
from typing import List, Dict
from api.schemas import BusinessLogicException
from api.charts.constants import COLOR_BLACK, TITLE_FONT_SIZE, COLOR_PALETTE, FIGURE_SIZE_DEFAULT


class Histogram5Config(BaseModel):
    title: str


class Histogram5Data(BaseModel):
    values: Dict[str, List[float]] = Field(..., min_length=1)


class Histogram5Request(BaseModel):
    project: str
    step: str
    config: Histogram5Config
    data: Histogram5Data


class Histogram5:
    def __init__(self, data: dict):
        try:
            validated_data = Histogram5Request(**data)
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

        # Generate a list of colors for each subplot
        colors = COLOR_PALETTE[:num_datasets]

        # Find the number of rows needed
        num_rows = num_datasets // 2 + num_datasets % 2

        # Get the column names as a list to plot
        columns = df.columns.tolist()

        self.figure = plt.figure(figsize=(11.69, num_rows * 5))

        for idx, column in enumerate(columns, 1):
            ax = self.figure.add_subplot(num_rows, num_columns, idx)
            ax.hist(
                df[column],
                color=colors[idx - 1],
                edgecolor=COLOR_BLACK,
                zorder=3
            )
            ax.grid(True)
            ax.set_title(column)

        plt.suptitle(title, fontsize=TITLE_FONT_SIZE, y=0.95)
        plt.tight_layout(pad=2.0)
        plt.subplots_adjust(top=0.85, bottom=0.15, left=0.15, right=0.85)
        plt.close('all')
        return self.figure
