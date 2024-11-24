import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pydantic import BaseModel, Field
from typing import List, Dict
from api.schemas import BusinessLogicException
from api.charts.constants import FIGURE_SIZE_DEFAULT, TITLE_FONT_SIZE


class Scatterplot1Config(BaseModel):
    title: str


class Scatterplot1Data(BaseModel):
    values: Dict[str, List[float]] = Field(..., min_length=1)


class Scatterplot1Request(BaseModel):
    project: str
    step: str
    config: Scatterplot1Config
    data: Scatterplot1Data


class Scatterplot1:
    def __init__(self, data: dict):
        try:
            validated_data = Scatterplot1Request(**data)
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
        sns.set_style("whitegrid")

        bp = sns.regplot(x=df.iloc[:, 1], y=df.iloc[:, 0], fit_reg=False)
        bp.set_title(title, fontsize=TITLE_FONT_SIZE, pad=20)

        return self.figure
