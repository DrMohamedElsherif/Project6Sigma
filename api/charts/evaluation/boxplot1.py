import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pydantic import BaseModel, Field
from typing import List, Dict
from api.schemas import BusinessLogicException
from api.charts.constants import COLORS, FIGURE_SIZE_A4_PORTRAIT, COLOR_BLACK, TITLE_FONT_SIZE


class Boxplot1Config(BaseModel):
    title: str


class Boxplot1Data(BaseModel):
    values: Dict[str, List[float]] = Field(..., min_length=1)


class Boxplot1Request(BaseModel):
    project: str
    step: str
    config: Boxplot1Config
    data: Boxplot1Data


class Boxplot1:
    def __init__(self, data: dict):
        try:
            validated_data = Boxplot1Request(**data)
            self.project = validated_data.project
            self.step = validated_data.step
            self.config = validated_data.config
            self.data = validated_data.data
            self.message = ""
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

        key, _ = list(self.data.values.items())[0]

        plt.subplots_adjust(top=0.85, bottom=0.4, left=0.15, right=0.85)

        sns.set_style("whitegrid")

        # bp = df.boxplot(
        #     column=[key],
        #     color=COLOR_BLACK,
        #     patch_artist=True,
        #     boxprops=dict(facecolor=COLORS[0]),
        #     figsize=FIGURE_SIZE_A4_PORTRAIT
        # )
        bp = sns.boxplot(
                data=df,
                y=key,
                orient='h',
                color="#a1d111", 
                linecolor='black', 
                showcaps=False, 
                linewidth=1, 
                flierprops={"marker": "x"},
                width=0.3
            )

        bp.set_title(title, fontsize=TITLE_FONT_SIZE, pad=20)
        bp.grid(True, alpha=0.3)
        plt.close('all')
        return self.figure