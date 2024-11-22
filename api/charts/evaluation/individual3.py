import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pydantic import BaseModel, Field
from typing import List, Dict
from api.schemas import BusinessLogicException
from api.charts.constants import FIGURE_SIZE_DEFAULT, TITLE_FONT_SIZE, COLORS


class Individual3Config(BaseModel):
    title: str


class Individual3Data(BaseModel):
    values: Dict[str, List[float]] = Field(..., min_length=1)
    categories: Dict[str, List[str]] = Field(..., min_length=1)
    groups: Dict[str, List[str]] = Field(..., min_length=1)


class Individual3AdditionalData(BaseModel):
    var: str
    catVar: str
    group: str


class Individual3Request(BaseModel):
    project: str
    step: str
    config: Individual3Config
    data: Individual3Data
    additional_data: Individual3AdditionalData


class Individual3:
    def __init__(self, data: dict):
        try:
            validated_data = Individual3Request(**data)
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

        # Create DataFrame from the input data
        df = pd.DataFrame({
            self.additional_data.var: self.data.values[list(self.data.values.keys())[0]],
            self.additional_data.catVar: self.data.categories[list(self.data.categories.keys())[0]],
            self.additional_data.group: self.data.groups[list(self.data.groups.keys())[0]]
        })

        # Set the order of categories
        unique_values = df[self.additional_data.catVar].unique()
        order = unique_values

        sns.set_style("whitegrid")

        # Create facet grid with subplots for each group
        sp = sns.FacetGrid(
            df,
            col=self.additional_data.group,
            col_wrap=2,
            aspect=1.5,
            height=5
        )

        # Create stripplot
        sp.map(
            sns.stripplot,
            self.additional_data.catVar,
            self.additional_data.var,
            hue=self.additional_data.group,
            data=df,
            order=order,
            marker='o',
            size=10,
            jitter=False,
            palette=COLORS
        )

        # Set title and adjust layout
        sp.fig.suptitle(title, fontsize=TITLE_FONT_SIZE)
        plt.subplots_adjust(top=0.9)

        # Add grid to all subplots
        for ax in sp.axes.flat:
            ax.grid(True, axis='both')

        self.figure = sp.fig
        return self.figure
