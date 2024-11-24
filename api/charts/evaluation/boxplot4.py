import pandas as pd
import matplotlib.pyplot as plt
from pydantic import BaseModel, Field
from typing import List, Dict
from api.schemas import BusinessLogicException
from api.charts.constants import FIGURE_SIZE_DEFAULT, TITLE_FONT_SIZE, COLOR_BLACK, COLOR_BLUE


class Boxplot4Config(BaseModel):
    title: str


class Boxplot4Data(BaseModel):
    values: Dict[str, List[float]] = Field(..., min_length=1)


class Boxplot4Request(BaseModel):
    project: str
    step: str
    config: Boxplot4Config
    data: Boxplot4Data


class Boxplot4:
    def __init__(self, data: dict):
        try:
            validated_data = Boxplot4Request(**data)
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

        self.figure = plt.figure(figsize=FIGURE_SIZE_DEFAULT)
        ax = self.figure.add_subplot(111)

        df.boxplot(
            color=COLOR_BLACK,
            patch_artist=True,
            boxprops=dict(facecolor=COLOR_BLUE),
            ax=ax
        )

        ax.set_title(title, fontsize=TITLE_FONT_SIZE, pad=20)

        return self.figure
