import pandas as pd
import matplotlib.pyplot as plt
from pydantic import BaseModel, Field
from typing import List, Dict
from api.schemas import BusinessLogicException
from api.charts.constants import COLOR_BLUE, FIGURE_SIZE_DEFAULT, COLOR_BLACK, TITLE_FONT_SIZE


class Boxplot2Config(BaseModel):
    title: str


class Boxplot2Data(BaseModel):
    values: Dict[str, List[float]] = Field(..., min_length=1)


class Boxplot2Request(BaseModel):
    project: str
    step: str
    config: Boxplot2Config
    data: Boxplot2Data


class Boxplot2:
    def __init__(self, data: dict):
        try:
            validated_data = Boxplot2Request(**data)
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

        self.figure = plt.figure(figsize=FIGURE_SIZE_DEFAULT)
        ax = self.figure.add_subplot(111)

        df.boxplot(
            column=df.columns.tolist(),
            color=COLOR_BLACK,
            patch_artist=True,
            grid=True,
            boxprops=dict(facecolor=COLOR_BLUE),
            ax=ax
        )
        ax.set_title(title, fontsize=TITLE_FONT_SIZE, pad=20)

        return self.figure