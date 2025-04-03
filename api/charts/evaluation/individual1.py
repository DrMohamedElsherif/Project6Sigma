import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pydantic import BaseModel, Field
from typing import List, Dict
from api.schemas import BusinessLogicException
from api.charts.constants import FIGURE_SIZE_A4_PORTRAIT, TITLE_FONT_SIZE


class Individual1Config(BaseModel):
    title: str


class Individual1Data(BaseModel):
    values: Dict[str, List[float]] = Field(..., min_length=1)


class Individual1Request(BaseModel):
    project: str
    step: str
    config: Individual1Config
    data: Individual1Data


class Individual1:
    def __init__(self, data: dict):
        try:
            validated_data = Individual1Request(**data)
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
        df = pd.DataFrame(self.data.values)

        # Define size of figure and style
        self.figure = plt.figure(figsize=FIGURE_SIZE_A4_PORTRAIT)
        plt.subplots_adjust(top=0.85, bottom=0.4, left=0.1, right=0.9)
        sns.set_theme(style="whitegrid")

        # Create subplot
        ax = self.figure.add_subplot(111)

        # Get first column for plotting
        key = list(df.columns)[0]

        # Create stripplot using modern API
        sns.stripplot(
            data=df,
            y=key,
            marker='o',
            size=10,
            jitter=False,
            legend=False,
            ax=ax,
            color='#95b92a'
        )

        # Add grid lines
        ax.grid(True, which='both')

        # Set title
        ax.set_title(title, fontsize=TITLE_FONT_SIZE, pad=20)

        # Adjust layout
        plt.close('all')
        return self.figure