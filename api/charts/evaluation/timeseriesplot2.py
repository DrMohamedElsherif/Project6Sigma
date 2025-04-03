import pandas as pd
import matplotlib.pyplot as plt
from pydantic import BaseModel, Field
from typing import List, Dict
from api.schemas import BusinessLogicException
from api.charts.constants import FIGURE_SIZE_A4_PORTRAIT, TITLE_FONT_SIZE, COLOR_PALETTE, MARKERS, LINES


class Timeseriesplot2Config(BaseModel):
    title: str


class Timeseriesplot2Data(BaseModel):
    values: Dict[str, List[float]] = Field(..., min_length=1)


class Timeseriesplot2Request(BaseModel):
    project: str
    step: str
    config: Timeseriesplot2Config
    data: Timeseriesplot2Data


class Timeseriesplot2:
    def __init__(self, data: dict):
        try:
            validated_data = Timeseriesplot2Request(**data)
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

        self.figure = plt.figure(figsize=FIGURE_SIZE_A4_PORTRAIT)

        for index, column in enumerate(df):
            y = df[column]
            x = range(1, df[column].count() + 1)
            count = df[column].count()

            plt.plot(
                (x + (index * count)),
                y,
                linestyle=LINES[index],
                marker=MARKERS[index],
                color=COLOR_PALETTE[index],
                label=df.columns[index]
            )

        plt.legend(loc='best')
        plt.title(title, fontsize=TITLE_FONT_SIZE, pad=20)
        plt.grid(True, alpha=0.3)
        plt.subplots_adjust(top=0.85, bottom=0.4, left=0.1, right=0.9)
        plt.close('all')
        return self.figure