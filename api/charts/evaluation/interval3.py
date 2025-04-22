import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from api.schemas import BusinessLogicException
from api.charts.constants import TITLE_FONT_SIZE, MARKERS, COLOR_PALETTE, FIGURE_SIZE_A4_PORTRAIT


class Interval3Config(BaseModel):
    title: str


class Interval3Data(BaseModel):
    values: Dict[str, List[float]] = Field(..., min_length=1)
    categories: Dict[str, List[str]] = Field(..., min_length=1)
    groups: Dict[str, List[str]] = Field(..., min_length=1)


class Interval3Request(BaseModel):
    project: str
    step: str
    config: Interval3Config
    data: Interval3Data


class Interval3:
    def __init__(self, data: dict):
        try:
            validated_data = Interval3Request(**data)
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

        # Extract keys from data
        var_key = list(self.data.values.keys())[0]
        cat_var_key = list(self.data.categories.keys())[0]
        group_key = list(self.data.groups.keys())[0]

        # Create DataFrame from input data
        df = pd.DataFrame({
            var_key: self.data.values[var_key],
            cat_var_key: self.data.categories[cat_var_key],
            group_key: self.data.groups[group_key]
        })

        # Get unique values for ordering
        unique_values = df[cat_var_key].unique()
        order = unique_values

        # Set style
        sns.set_style("whitegrid")

        # Set figure size
        plt.figure(figsize=FIGURE_SIZE_A4_PORTRAIT)

        # Create facet grid
        sp = sns.FacetGrid(
            df,
            col=group_key,
            col_wrap=2,
            aspect=1.5,
            height=5
        )

        sp.figure.set_size_inches(FIGURE_SIZE_A4_PORTRAIT)

        def custom_pointplot(x, y, data, **kwargs):
            # Get the number of unique categories in the current subplot
            current_cats = data[x].unique()
            current_palette = COLOR_PALETTE[:len(current_cats)]

            ax = plt.gca()
            sns.pointplot(
                data=data,
                x=x,
                y=y,
                hue=x,  # Use x as hue variable
                order=kwargs.get('order'),
                markers=MARKERS[0],
                linestyle='none',
                capsize=0.1,
                palette=current_palette,  # Use dynamically sized color palette
                markersize=7.5,
                legend=False,
                ax=ax
            )

        # Create point plots with updated parameters
        sp.map_dataframe(
            custom_pointplot,
            cat_var_key,
            var_key
        )

        # Set title and adjust layout
        sp.figure.suptitle(title, fontsize=TITLE_FONT_SIZE)
        plt.subplots_adjust(top=0.9, left=0.1, right=0.9, bottom=0.1)

        # Add grid to all subplots
        for ax in sp.axes.flat:
            ax.grid(True, axis='both', alpha=0.3)

        self.figure = sp.figure
        plt.close('all')
        return self.figure
