import pandas as pd
import matplotlib.pyplot as plt
from pydantic import BaseModel, Field
from typing import List, Dict
from api.schemas import BusinessLogicException
from api.charts.constants import COLOR_BLACK, TITLE_FONT_SIZE, COLOR_BLUE


class Histogram3Config(BaseModel):
    title: str


class Histogram3Data(BaseModel):
    values: Dict[str, List[float]] = Field(..., min_length=1)


class Histogram3Request(BaseModel):
    project: str
    step: str
    config: Histogram3Config
    data: Histogram3Data


class Histogram3:
    def __init__(self, data: dict):
        try:
            validated_data = Histogram3Request(**data)
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
        df = pd.DataFrame(self.data.values)

        # Count the number of columns
        num_columns = len(df.columns)

        # Calculate the number of rows and columns for the subplots
        num_rows = (num_columns + 1) // 2
        num_cols = min(num_columns, 2)

        # Initialize the subplots
        self.figure, axes = plt.subplots(num_rows, num_cols, figsize=(
            15, num_rows * 5), sharey='row', squeeze=False)

        # Enable grid lines
        for ax_row in axes:
            for ax in ax_row:
                ax.grid(True, zorder=-1)

        # Iterate over the columns and create a histogram for each
        for i, column in enumerate(df.columns):
            # Determine the subplot coordinates
            row = i // num_cols
            col = i % num_cols

            # Select the current subplot
            ax = axes[row, col]

            # Plot the histogram
            ax.hist(
                df[column],
                edgecolor=COLOR_BLACK,
                align="left",
                color=COLOR_BLUE,
                zorder=3
            )

            # Set the subplot title
            ax.set_title(column)

        # Remove empty subplots
        if num_columns % 2 != 0:
            self.figure.delaxes(axes[-1, -1])

        # Add overall figure title
        self.figure.suptitle(title, fontsize=TITLE_FONT_SIZE, y=0.98)

        # Adjust the spacing between subplots
        self.figure.subplots_adjust(hspace=0)

        return self.figure
