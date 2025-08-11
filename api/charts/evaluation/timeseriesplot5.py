import pandas as pd
import matplotlib.pyplot as plt
from pydantic import BaseModel, Field
from typing import List, Dict
from api.schemas import BusinessLogicException
from api.charts.constants import FIGURE_SIZE_A4_PORTRAIT, TITLE_FONT_SIZE, COLOR_PALETTE, MARKERS


class Timeseriesplot5Config(BaseModel):
    title: str


class Timeseriesplot5Data(BaseModel):
    values: Dict[str, List[float]] = Field(..., min_length=1)


class Timeseriesplot5Request(BaseModel):
    project: str
    step: str
    config: Timeseriesplot5Config
    data: Timeseriesplot5Data


class Timeseriesplot5:
    def __init__(self, data: dict):
        try:
            validated_data = Timeseriesplot5Request(**data)
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

        num_columns = 2
        num_datasets = len(df.columns)
        num_rows = num_datasets // 2 + num_datasets % 2
        columns = df.columns.tolist()
        colors = COLOR_PALETTE[:num_datasets]

        self.figure, axes = plt.subplots(num_rows, num_columns, figsize=FIGURE_SIZE_A4_PORTRAIT)
        axes = axes.flatten()

        for idx, column in enumerate(columns):
            axes[idx].plot(df[column], marker=MARKERS[0], color=colors[idx])
            axes[idx].set_title(column)
            axes[idx].grid(True, alpha=0.3)

        # Remove empty subplots
        for idx in range(num_datasets, len(axes)):
            self.figure.delaxes(axes[idx])

        plt.suptitle(title, fontsize=TITLE_FONT_SIZE)
        plt.tight_layout(pad=3.0)
        plt.subplots_adjust(top=0.85, bottom=0.1, left=0.15, right=0.85)
        plt.close('all')
        return self.figure
