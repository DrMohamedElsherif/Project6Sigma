import pandas as pd
import matplotlib.pyplot as plt
from pydantic import BaseModel, Field
from typing import List, Dict
from api.schemas import BusinessLogicException
from api.charts.constants import COLOR_BLACK, COLOR_BLUE, TITLE_FONT_SIZE


class Histogram1Config(BaseModel):
    title: str
    labelx: str
    labely: str


class Histogram1Data(BaseModel):
    values: Dict[str, List[float]] = Field(..., min_length=1)


class Histogram1Request(BaseModel):
    project: str
    step: str
    config: Histogram1Config
    data: Histogram1Data


class Histogram1:
    def __init__(self, data: dict):
        try:
            validated_data = Histogram1Request(**data)
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
        df = pd.DataFrame(self.data.values)
        data = df.iloc[:, 0]

        self.figure, ax = plt.subplots(figsize=(15, 11))

        # Enable grid lines
        plt.grid(True)

        # Add labels
        plt.xlabel(self.config.labelx)
        plt.ylabel(self.config.labely)

        # Plot histogram
        ax.hist(
            data,
            edgecolor=COLOR_BLACK,
            align="left",
            color=COLOR_BLUE
        )
        ax.set_title(self.config.title, fontsize=TITLE_FONT_SIZE, pad=20)

        return self.figure
