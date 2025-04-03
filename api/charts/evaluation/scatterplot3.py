import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pydantic import BaseModel, Field
from typing import List, Dict
from api.schemas import BusinessLogicException
from api.charts.constants import FIGURE_SIZE_A4_PORTRAIT, COLORS, MARKERS


class Scatterplot3Config(BaseModel):
    title: str


class Scatterplot3Data(BaseModel):
    values: Dict[str, List[float | str]] = Field(..., min_length=1)


class Scatterplot3AdditionalData(BaseModel):
    xVar: str
    yVar: str
    group: str


class Scatterplot3Request(BaseModel):
    project: str
    step: str
    config: Scatterplot3Config
    data: Scatterplot3Data
    additional_data: Scatterplot3AdditionalData


class Scatterplot3:
    def __init__(self, data: dict):
        try:
            validated_data = Scatterplot3Request(**data)
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

        g = sns.FacetGrid(
            df,
            col=self.additional_data.group,
            col_wrap=2,
            aspect=1.5,
            height=5
        )

        g.map(
            sns.scatterplot,
            self.additional_data.yVar,
            self.additional_data.xVar,
            zorder=3
        )

        g.set_titles(col_template="{col_name}")
        g.set_axis_labels(self.additional_data.yVar, self.additional_data.xVar)

        for ax in g.axes:
            ax.grid(True, axis='both', zorder=-1, alpha=0.3)

        plt.subplots_adjust(top=0.9)
        g.figure.suptitle(title)

        # Set the figure size to A4 portrait
        g.figure.set_size_inches(*FIGURE_SIZE_A4_PORTRAIT)

        self.figure = g.figure
        plt.tight_layout(pad=2.0)
        plt.close('all')
        return self.figure
