import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pydantic import BaseModel, Field
from typing import List, Dict
from api.schemas import BusinessLogicException
from api.charts.constants import FIGURE_SIZE_A4_PORTRAIT, COLOR_PALETTE, MARKERS


class Scatterplot2Config(BaseModel):
    title: str


class Scatterplot2Data(BaseModel):
    values: Dict[str, List[float | str]] = Field(..., min_length=1)


class Scatterplot2AdditionalData(BaseModel):
    xVar: str
    yVar: str
    group: str


class Scatterplot2Request(BaseModel):
    project: str
    step: str
    config: Scatterplot2Config
    data: Scatterplot2Data
    additional_data: Scatterplot2AdditionalData


class Scatterplot2:
    def __init__(self, data: dict):
        try:
            validated_data = Scatterplot2Request(**data)
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

        self.figure = plt.figure(figsize=FIGURE_SIZE_A4_PORTRAIT)

        groups = df[self.additional_data.group].unique()
        colors = dict(zip(groups, COLOR_PALETTE[:len(groups)]))
        markers = dict(zip(groups, MARKERS[:len(groups)]))

        for group in groups:
            group_data = df[df[self.additional_data.group] == group]
            sns.scatterplot(
                x=self.additional_data.xVar,
                y=self.additional_data.yVar,
                data=group_data,
                color=colors[group],
                marker=markers[group],
                zorder=3,
                s=80
            )

        legend_handles = [
            plt.Line2D([0], [0], marker=markers[group], color=colors[group],
                       linestyle='', label=group) for group in groups
        ]
        plt.legend(handles=legend_handles, title=self.additional_data.group)
        plt.xlabel(self.additional_data.xVar)
        plt.ylabel(self.additional_data.yVar)
        plt.title(title)
        plt.grid(True, which='both', zorder=-1, alpha=0.3)
        plt.subplots_adjust(top=0.85, bottom=0.4, left=0.1, right=0.9)
        plt.close('all')
        return self.figure
