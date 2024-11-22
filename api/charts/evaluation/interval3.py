import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from api.schemas import BusinessLogicException
from api.charts.constants import TITLE_FONT_SIZE, MARKERS


class Interval3Config(BaseModel):
    title: str


class Interval3Data(BaseModel):
    values: Dict[str, List[float]] = Field(..., min_length=1)
    categories: Dict[str, List[str]] = Field(..., min_length=1)
    groups: Dict[str, List[str]] = Field(..., min_length=1)


class Interval3AdditionalData(BaseModel):
    var: str
    catVar: str
    group: str


class Interval3Request(BaseModel):
    project: str
    step: str
    config: Interval3Config
    data: Interval3Data
    additional_data: Interval3AdditionalData


class Interval3:
    def __init__(self, data: dict):
        try:
            validated_data = Interval3Request(**data)
            self.project = validated_data.project
            self.step = validated_data.step
            self.config = validated_data.config
            self.data = validated_data.data
            self.additional_data = validated_data.additional_data
            self.figure = None

        except ValueError as e:
            raise BusinessLogicException(
                error_code="validation_error",
                field=str(e),
                details={"message": f"Invalid or missing field: {str(e)}"}
            )

    def process(self):
        title = self.config.title

        # Create DataFrame from input data
        df = pd.DataFrame({
            self.additional_data.var: list(self.data.values.values())[0],
            self.additional_data.catVar: list(self.data.categories.values())[0],
            self.additional_data.group: list(self.data.groups.values())[0]
        })

        # Get unique values for ordering
        unique_values = df[self.additional_data.catVar].unique()
        order = unique_values

        # Set style
        sns.set_style("whitegrid")

        # Create facet grid
        sp = sns.FacetGrid(
            df,
            col=self.additional_data.group,
            col_wrap=2,
            aspect=1.5,
            height=5
        )

        # Create point plots
        sp.map(
            sns.pointplot,
            self.additional_data.catVar,
            self.additional_data.var,
            hue=self.additional_data.group,
            data=df,
            order=order,
            marker=MARKERS[0],
            scale=0.75,
            capsize=0.1,
            join=False
        )

        # Set title and adjust layout
        sp.fig.suptitle(title, fontsize=TITLE_FONT_SIZE)
        plt.subplots_adjust(top=0.9)

        # Add grid to all subplots
        for ax in sp.axes.flat:
            ax.grid(True, axis='both')

        self.figure = sp.fig
        return self.figure
