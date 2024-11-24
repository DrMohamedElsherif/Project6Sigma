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
    categories: Dict[str, List[str]] = Field(..., min_length=1)


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

        # Create DataFrame from the input data
        df = pd.DataFrame({
            'value': list(self.data.values.values())[0],
            'category': list(self.data.categories.values())[0]
        })

        # Define size of figure and style
        sns.set(rc={'figure.figsize': FIGURE_SIZE_DEFAULT})
        sns.set(style="whitegrid")

        # Create stripplot
        sp = sns.stripplot(
            x='category',
            y='value',
            data=df,
            marker=MARKERS[0],
            size=10,
            jitter=False,
            palette=COLORS
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