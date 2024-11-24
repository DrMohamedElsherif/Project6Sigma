import pandas as pd
import matplotlib.pyplot as plt
from pydantic import BaseModel, Field
from typing import List, Dict
from api.schemas import BusinessLogicException
from api.charts.constants import FIGURE_SIZE_DEFAULT, TITLE_FONT_SIZE, COLOR_BLUE


class Timeseriesplot1Config(BaseModel):
    title: str


class Timeseriesplot1Data(BaseModel):
    values: Dict[str, List[float]] = Field(..., min_length=1)


class Timeseriesplot1Request(BaseModel):
    project: str
    step: str
    config: Timeseriesplot1Config
    data: Timeseriesplot1Data


class Timeseriesplot1:
    def __init__(self, data: dict):
        try:
            validated_data = Timeseriesplot1Request(**data)
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
        y = df.iloc[:, 0]
        x = range(1, df.iloc[:, 0].count() + 1)

        self.figure = plt.figure(figsize=FIGURE_SIZE_DEFAULT)
        plt.plot(x, y, linestyle='-', marker='o', color=COLOR_BLUE)
        plt.title(title, fontsize=TITLE_FONT_SIZE, pad=20)
        plt.grid(True, which='both')

        return self.figure
