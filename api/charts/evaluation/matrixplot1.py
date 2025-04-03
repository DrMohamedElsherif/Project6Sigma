import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from pydantic import BaseModel, Field
from typing import List, Dict
from api.schemas import BusinessLogicException
from api.charts.constants import TITLE_FONT_SIZE, FIGURE_SIZE_A4_PORTRAIT


class Matrixplot1Config(BaseModel):
    title: str


class Matrixplot1Data(BaseModel):
    values: Dict[str, List[float]] = Field(..., min_length=2)  # Need at least 2 variables for a matrix plot


class Matrixplot1Request(BaseModel):
    project: str
    step: str
    config: Matrixplot1Config
    data: Matrixplot1Data


class Matrixplot1:
    def __init__(self, data: dict):
        try:
            validated_data = Matrixplot1Request(**data)
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

        # Set style
        sns.set_theme(style="whitegrid")

        # Create scatterplot matrix
        pair_plot = sns.pairplot(df, 
                                 diag_kind="hist", 
                                 height=1.8, 
                                 aspect=1.8, 
                                 plot_kws={'color': '#95b92a'},
                                 diag_kws={'color': '#95b92a', 'edgecolor': 'black'},
                                 )

        pair_plot.figure.set_size_inches(FIGURE_SIZE_A4_PORTRAIT)  # A4 portrait dimensions in inches

        # Add title
        pair_plot.figure.suptitle(title, fontsize=TITLE_FONT_SIZE)

        # Adjust layout
        plt.subplots_adjust(top=0.9, bottom=0.1, left=0.1, right=0.9)

        # Add grid
        for ax in pair_plot.axes.flatten():
            ax.grid(True, alpha=0.3)

        # Save figure
        self.figure = pair_plot.figure
        plt.close('all')
        return self.figure
