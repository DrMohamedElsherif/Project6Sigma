import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pydantic import BaseModel, Field
from typing import List, Dict
from api.schemas import BusinessLogicException
from api.charts.constants import COLOR_PALETTE, TITLE_FONT_SIZE


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
                error_code="error_validation",
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

        # Calculate the number of rows and columns dynamically based on the number of groups
        num_groups = df[self.additional_data.group].nunique()
        cols = 2  # Fixed number of columns
        rows = -(-num_groups // cols)  # Ceiling division to determine rows

        # Create facet grid with subplots for each group
        sp = sns.FacetGrid(
            df,
            col=self.additional_data.group,
            col_wrap=cols,
            aspect=0.7,
            height=(11.69 - 2) / rows,  # Adjust height dynamically for A4 portrait
        )

        def custom_stripplot(x, y, data, **kwargs):
            # Get the number of unique categories in the current subplot
            current_cats = data[x].unique()
            current_palette = COLOR_PALETTE[:len(current_cats)]

            sns.stripplot(
                data=data,
                x=x,
                y=y,
                hue=x,  # Use x variable as hue
                order=kwargs.get('order'),
                marker='o',
                size=10,
                jitter=False,
                palette=current_palette,  # Use dynamically sized palette
                legend=False,
                ax=plt.gca()
            )

        # Create stripplot using custom function
        sp.map_dataframe(
            custom_stripplot,
            self.additional_data.catVar,
            self.additional_data.var
        )

        # Set title and adjust layout
        sp.figure.suptitle(title, fontsize=TITLE_FONT_SIZE)
        plt.subplots_adjust(top=0.9)

        # Add grid to all subplots
        for ax in sp.axes.flat:
            ax.grid(True, axis='both')

        # Set the figure size to A4 portrait
        sp.figure.set_size_inches(8.27, 11.69)

        self.figure = sp.figure
        plt.close('all')
        return self.figure
