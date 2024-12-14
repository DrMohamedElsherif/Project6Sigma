import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pydantic import BaseModel, Field
from typing import List, Dict
from api.schemas import BusinessLogicException
from api.charts.constants import FIGURE_SIZE_DEFAULT, TITLE_FONT_SIZE, COLORS, MARKERS


class Individual2Config(BaseModel):
    title: str


class Individual2Data(BaseModel):
    values: Dict[str, List[float]] = Field(..., min_length=1)
    categories: Dict[str, List[str]] = Field(..., min_length=1)


class Individual2Request(BaseModel):
    project: str
    step: str
    config: Individual2Config
    data: Individual2Data


class Individual2:
    def __init__(self, data: dict):
        try:
            validated_data = Individual2Request(**data)
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

        # Prepare data
        values = list(self.data.values.values())[0]  # Get values list
        categories = list(self.data.categories.values())[0]  # Get categories list

        df = pd.DataFrame({
            'value': values,
            'category': categories
        })

        # Define size of figure and style
        self.figure = plt.figure(figsize=FIGURE_SIZE_DEFAULT)
        sns.set(style="whitegrid")

        # Create subplot
        ax = self.figure.add_subplot(111)

        # Get number of unique categories for color limiting
        n_categories = len(df['category'].unique())

        # Create stripplot with updated parameters to avoid deprecation warnings
        sns.stripplot(
            data=df,
            x='category',
            y='value',
            marker=MARKERS[0],
            s=10,  # Using 's' instead of 'size' for consistency with matplotlib
            jitter=False,
            hue='category',  # Use the category for both x and hue
            palette=COLORS[:n_categories],  # Limit colors to number of categories
            legend=False,  # Hide the legend since categories are shown on x-axis
            ax=ax
        )

        # Add grid lines
        ax.grid(True, which='both')

        # Set title
        ax.set_title(title, fontsize=TITLE_FONT_SIZE, pad=20)

        # Adjust layout
        plt.tight_layout()
        plt.close('all')
        return self.figure
