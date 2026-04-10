# histogram4.py

import pandas as pd
import matplotlib.pyplot as plt
from pydantic import BaseModel, Field
from typing import List, Dict
from api.schemas import BusinessLogicException
from api.charts.constants import COLOR_BLACK, TITLE_FONT_SIZE, COLOR_PALETTE, FIGURE_SIZE_A4_PORTRAIT


class Histogram4Config(BaseModel):
    title: str


class Histogram4Data(BaseModel):
    values: Dict[str, List[float]] = Field(..., min_length=1)


class Histogram4Request(BaseModel):
    project: str
    step: str
    config: Histogram4Config
    data: Histogram4Data


class Histogram4:
    def __init__(self, data: dict):
        try:
            validated_data = Histogram4Request(**data)
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

        # Count the number of columns
        num_datasets = len(df.columns)

        # Extract data into separate arrays
        data = [df[column].values.tolist() for column in df.columns]

        # Generate a list of colors for each subplot
        colors = COLOR_PALETTE[:num_datasets]

        self.figure, ax = plt.subplots(figsize=FIGURE_SIZE_A4_PORTRAIT)

        plt.subplots_adjust(top=0.85, bottom=0.4, left=0.15, right=0.85)

        # Enable grid lines
        plt.grid(True)

        # Add labels
        plt.xlabel("Data")
        plt.ylabel("Frequency")

        # Plot histogram
        handles = ax.hist(
            data,
            edgecolor=COLOR_BLACK,
            align="left",
            stacked=True,
            zorder=3,
            histtype='barstacked',
            color=colors,
            label=df.columns.tolist()
        )

        ax.set_title(title, fontsize=TITLE_FONT_SIZE, pad=20)

        # Add legend
        plt.legend(loc='best')
        plt.close('all')
        return self.figure
