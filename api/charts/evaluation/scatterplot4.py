import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pydantic import BaseModel, Field
from typing import List, Dict
from api.schemas import BusinessLogicException
from api.charts.constants import FIGURE_SIZE_DEFAULT, TITLE_FONT_SIZE, MARKERS, COLORS


class Scatterplot4Config(BaseModel):
    title: str


class Scatterplot4Data(BaseModel):
    values: Dict[str, List[float]] = Field(..., min_length=1)


class Scatterplot4AdditionalData(BaseModel):
    xVar: str
    yVars: List[str]


class Scatterplot4Request(BaseModel):
    project: str
    step: str
    config: Scatterplot4Config
    data: Scatterplot4Data
    additional_data: Scatterplot4AdditionalData


class Scatterplot4:
    def __init__(self, data: dict):
        try:
            validated_data = Scatterplot4Request(**data)
            self.project = validated_data.project
            self.step = validated_data.step
            self.config = validated_data.config
            self.data = validated_data.data
            self.additional_data = validated_data.additional_data
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

        # Loop over y vars
        for index, value in enumerate(self.additional_data.yVars):
            sns.regplot(
                x=self.additional_data.xVar,
                y=value,
                data=df,
                fit_reg=False,
                color=COLORS[index],
                marker=MARKERS[index],
                label=value
            )

        plt.legend()
        plt.xlabel(self.additional_data.xVar)
        plt.ylabel('Y-Data')
        plt.title(title, fontsize=TITLE_FONT_SIZE, pad=20)
        plt.grid(True)

        return self.figure
