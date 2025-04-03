import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pydantic import BaseModel, Field
from typing import List, Dict
from api.schemas import BusinessLogicException
from api.charts.constants import FIGURE_SIZE_A4_PORTRAIT, TITLE_FONT_SIZE, TITLE_PADDING, COLOR_PALETTE


class Interval2Config(BaseModel):
    title: str


class Interval2Data(BaseModel):
    values: Dict[str, List[float]] = Field(..., min_length=1)


class Interval2Request(BaseModel):
    project: str
    step: str
    config: Interval2Config
    data: Interval2Data


class Interval2:
    def __init__(self, data: dict):
        try:
            plt.close('all')  # Clean up any existing figures
            validated_data = Interval2Request(**data)
            self.project = validated_data.project
            self.step = validated_data.step
            self.config = validated_data.config
            self.data = validated_data.data
            self.figure = None

        except ValueError as e:
            plt.close('all')
            raise BusinessLogicException(
                error_code="error_validation",
                field=str(e),
                details={"message": f"Invalid or missing field: {str(e)}"}
            )

    def process(self):
        try:
            title = self.config.title

            # Create DataFrame from the input data
            df = pd.DataFrame(self.data.values)

            # Create figure and axis objects
            fig, ax = plt.subplots(figsize=FIGURE_SIZE_A4_PORTRAIT)

            # Process each column
            for index, column in enumerate(df):
                # Calculate statistics
                mean = np.mean(df[column])
                stddev = np.std(df[column])
                confidence_interval = 1.96 * stddev / np.sqrt(len(df[column]))

                # Plot error bar
                ax.errorbar(
                    x=index,
                    y=mean,
                    yerr=confidence_interval,
                    fmt='o',
                    capsize=15,
                    label=column,
                    color=COLOR_PALETTE[index % len(COLOR_PALETTE)]
                )

            # Set labels and title
            ax.set_ylabel('Values')
            ax.set_title(title, fontsize=TITLE_FONT_SIZE, pad=TITLE_PADDING)

            # Hide x-axis labels
            ax.set_xticks([])

            # Add legend
            ax.legend(loc='best')

            plt.subplots_adjust(top=0.85, bottom=0.4, left=0.1, right=0.9)

            # Enable grid
            ax.grid(True, which='both', alpha=0.3)

            # Store the figure
            self.figure = fig

            return self.figure

        finally:
            # Ensure we clean up any other figures that might have been created
            for fig_num in plt.get_fignums():
                if plt.figure(fig_num) != self.figure:
                    plt.close(fig_num)

    def cleanup(self):
        """Clean up all figures when done"""
        if self.figure is not None:
            plt.close(self.figure)
        plt.close('all')
