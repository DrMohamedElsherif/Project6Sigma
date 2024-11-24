import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pydantic import BaseModel, Field
from typing import List, Dict
from api.schemas import BusinessLogicException
from api.charts.constants import TITLE_FONT_SIZE


class Individual6Config(BaseModel):
    title: str


class Individual6Data(BaseModel):
    values: Dict[str, List[float]] = Field(..., min_length=1)


class Individual6Request(BaseModel):
    project: str
    step: str
    config: Individual6Config
    data: Individual6Data


class Individual6:
    def __init__(self, data: dict):
        try:
            validated_data = Individual6Request(**data)
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
        plt.close('all')

        # Create DataFrame from the input data
        df = pd.DataFrame(self.data.values)

        # Calculate layout
        num_plots = len(df.columns)
        num_cols = 2
        num_rows = (num_plots + num_cols - 1) // num_cols

        # Set style
        sns.set(style="whitegrid")

        # Create figure and subplots
        fig, axes = plt.subplots(num_rows, num_cols, figsize=(15, num_rows * 5))

        # Flatten the axes array if necessary
        axes = axes.flatten() if isinstance(axes, np.ndarray) else [axes]

        # Create stripplots for each column
        for index, column in enumerate(df.columns):
            ax = axes[index]
            sp = sns.stripplot(
                y=df[column],
                marker='o',
                size=10,
                jitter=False,
                ax=ax
            )
            ax.grid(True, which='both', axis='both')
            ax.set_title(column)

        # Remove any extra subplots
        for i in range(num_plots, len(axes)):
            fig.delaxes(axes[i])

        # Set main title and adjust layout
        plt.suptitle(title, fontsize=TITLE_FONT_SIZE)
        plt.subplots_adjust(left=0.1, bottom=0.1, right=0.9, top=0.9)

        self.figure = fig
        plt.close('all')
        return self.figure
