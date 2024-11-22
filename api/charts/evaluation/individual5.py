import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from api.schemas import BusinessLogicException
from api.charts.constants import FIGURE_SIZE_DEFAULT, TITLE_FONT_SIZE, COLORS, MARKERS


class Individual5Config(BaseModel):
    title: str


class Individual5Data(BaseModel):
    values: Dict[str, List[float]] = Field(..., min_length=1)
    categories: Dict[str, List[str]] = Field(..., min_length=1)


class Individual5AdditionalData(BaseModel):
    catVar: Optional[List[str]] = None
    values2: Optional[List[float]] = None


class Individual5Request(BaseModel):
    project: str
    step: str
    config: Individual5Config
    data: Individual5Data
    additional_data: Optional[Individual5AdditionalData] = None


class Individual5:
    def __init__(self, data: dict):
        try:
            validated_data = Individual5Request(**data)
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

    def get_color_palette(self, n_colors):
        """Get a subset of colors based on the number needed."""
        return [COLORS[i % len(COLORS)] for i in range(n_colors)]

    def process(self):
        title = self.config.title

        # Create main DataFrame
        df = pd.DataFrame({
            'values1': list(self.data.values.values())[0],
            'category': list(self.data.categories.values())[0]
        })

        # Set figure size and style
        sns.set(rc={'figure.figsize': FIGURE_SIZE_DEFAULT})
        sns.set(style="whitegrid")

        if self.additional_data and self.additional_data.values2 is not None:
            # Create additional data DataFrame
            df['values2'] = self.additional_data.values2

            # Reshape the dataframe
            melted_df = df.melt(
                id_vars=['category'],
                value_vars=['values1', 'values2'],
                var_name='measurement_type',
                value_name='value'
            )

            # Get number of unique measurement types
            n_groups = melted_df['measurement_type'].nunique()
            palette = self.get_color_palette(n_groups)

            # Create stripplot with dodged groups
            sp = sns.stripplot(
                x="category",
                y="value",
                hue="measurement_type",
                data=melted_df,
                dodge=True,
                marker=MARKERS[0],
                size=10,
                jitter=False,
                palette=palette
            )

            # Set labels
            sp.set_xlabel("Category")
            sp.set_ylabel("Values")
            plt.legend(title="")

        else:
            # Get number of unique categories
            n_categories = df['category'].nunique()
            palette = self.get_color_palette(n_categories)

            # Create simple stripplot
            sp = sns.stripplot(
                x='category',
                y='values1',
                data=df,
                marker=MARKERS[0],
                size=10,
                jitter=False,
                palette=palette
            )

        # Rotate x-axis labels
        sp.set_xticks(range(len(sp.get_xticklabels())))
        sp.set_xticklabels(sp.get_xticklabels(), rotation=45, ha='right')

        # Add grid lines
        plt.grid(True, which='both')

        # Set title
        sp.set_title(title, fontsize=TITLE_FONT_SIZE, pad=20)

        # Adjust layout
        plt.tight_layout(pad=1.5)

        self.figure = plt.gcf()
        return self.figure
