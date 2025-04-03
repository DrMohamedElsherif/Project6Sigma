import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pydantic import BaseModel, Field
from typing import List, Dict
from api.schemas import BusinessLogicException
from api.charts.constants import FIGURE_SIZE_A4_PORTRAIT, TITLE_FONT_SIZE, COLOR_PALETTE


class Piechart2Config(BaseModel):
    title: str


class Piechart2Data(BaseModel):
    values: Dict[str, List[str]] = Field(..., min_length=1)  # Dictionary of categorical columns


class Piechart2Request(BaseModel):
    project: str
    step: str
    config: Piechart2Config
    data: Piechart2Data


class Piechart2:
    def __init__(self, data: dict):
        try:
            validated_data = Piechart2Request(**data)
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

        # Create dataframe
        df = pd.DataFrame(self.data.values)

        # Define grid layout
        num_columns = 2
        num_datasets = len(df.columns)
        num_rows = (num_datasets + num_columns - 1) // num_columns  # Ceiling division

        # Create figure and subplots
        self.figure, axes = plt.subplots(num_rows, num_columns, figsize=FIGURE_SIZE_A4_PORTRAIT)

        # Convert axes to 2D array if it's 1D or single subplot
        if num_datasets == 1:
            axes = np.array([[axes]])
        elif num_rows == 1:
            axes = axes.reshape(1, -1)

        # Flatten axes for easier iteration
        axes_flat = axes.flatten()

        # Create pie charts for each column
        for idx, column_name in enumerate(df.columns):
            # Calculate normalized value counts
            data_counts = df[column_name].value_counts(normalize=True)

            if not data_counts.empty:
                axes_flat[idx].pie(
                    data_counts,
                    labels=data_counts.index,
                    autopct='%1.1f%%',
                    startangle=90,
                    colors=COLOR_PALETTE
                )
                axes_flat[idx].set_title(column_name)

        # Remove empty subplots
        for i in range(len(df.columns), len(axes_flat)):
            self.figure.delaxes(axes_flat[i])

        # Set main title
        plt.suptitle(title, fontsize=TITLE_FONT_SIZE)

        # Adjust layout
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        plt.close('all')
        return self.figure
