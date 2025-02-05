import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pydantic import BaseModel, Field
from typing import List, Dict
from api.schemas import BusinessLogicException
from api.charts.constants import FIGURE_SIZE_DEFAULT, TITLE_FONT_SIZE, COLORS, MARKERS


class Individual4Config(BaseModel):
    title: str


class Individual4Data(BaseModel):
    values: Dict[str, List[float]] = Field(..., min_length=1)


class Individual4Request(BaseModel):
    project: str
    step: str
    config: Individual4Config
    data: Individual4Data


class Individual4:
    def __init__(self, data: dict):
        try:
            validated_data = Individual4Request(**data)
            self.project = validated_data.project
            self.step = validated_data.step
            self.config = validated_data.config
            self.data = validated_data.data.values
            self.figure = None

        except ValueError as e:
            raise BusinessLogicException(
                error_code="error_validation",
                field=str(e),
                details={"message": f"Invalid or missing field: {str(e)}"}
            )

    def process(self):
        title = self.config.title

        # Create DataFrame from the combined input data
        df = pd.DataFrame({
            'category': [key for key, values in self.data.items() for _ in values],
            'value': [value for values in self.data.values() for value in values]
        })

        # Define size of figure and style
        sns.set(rc={'figure.figsize': FIGURE_SIZE_DEFAULT})
        sns.set(style="whitegrid")

        palette = self.get_color_palette(len(df['category'].unique()))

        # Create stripplot with updated parameters
        sp = sns.stripplot(
            x='category',
            y='value',
            data=df,
            hue='category',  # Add hue parameter
            marker=MARKERS[0],
            size=10,  # Use size instead of markersize for stripplot
            jitter=False,
            palette=palette,  # Use new palette format
            legend=False  # Hide legend since categories are shown on x-axis
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
        plt.close('all')
        return self.figure

    def get_color_palette(self, n_colors):
        """Get a subset of colors based on the number needed."""
        return [COLORS[i % len(COLORS)] for i in range(n_colors)]
