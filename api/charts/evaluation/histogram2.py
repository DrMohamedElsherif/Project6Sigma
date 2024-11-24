import pandas as pd
import matplotlib.pyplot as plt
from pydantic import BaseModel, Field
from typing import List, Dict
from api.schemas import BusinessLogicException
from api.charts.constants import COLOR_BLACK, TITLE_FONT_SIZE, COLORS, FIGURE_SIZE_DEFAULT


class Histogram2Config(BaseModel):
    title: str


class Histogram2Data(BaseModel):
    values: Dict[str, List[float]] = Field(..., min_length=1)


class Histogram2Request(BaseModel):
    project: str
    step: str
    config: Histogram2Config
    data: Histogram2Data


class Histogram2:
    def __init__(self, data: dict):
        try:
            validated_data = Histogram2Request(**data)
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

        # Count the number of columns
        num_datasets = len(df.columns)

        # Extract data into separate arrays
        data = [df[column].values.tolist() for column in df.columns]

        # Generate a list of colors for each subplot
        colors = COLORS[:num_datasets]

        self.figure, ax = plt.subplots(figsize=FIGURE_SIZE_DEFAULT)

        # Enable grid lines
        plt.grid(True)

        # Add labels
        plt.xlabel("Data")
        plt.ylabel("Frequency")

        # Plot histogram
        ax.hist(
            data,
            edgecolor=COLOR_BLACK,
            align="left",
            stacked=True,
            zorder=3,
            histtype='barstacked',
            color=colors,
            label=df.columns.tolist()
        )

        ax.set_title(title, fontsize=TITLE_FONT_SIZE, pad=20)

        # Add legend
        plt.legend(loc='best')

        return self.figure
