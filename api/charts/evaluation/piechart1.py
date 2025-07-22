import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
from pydantic import BaseModel, Field
from typing import List, Dict
from api.schemas import BusinessLogicException
from api.charts.constants import FIGURE_SIZE_A4_PORTRAIT, TITLE_FONT_SIZE, COLOR_PALETTE


class Piechart1Config(BaseModel):
    title: str


class Piechart1Data(BaseModel):
    values: Dict[str, List[str]] = Field(..., min_length=1)  # Using string type for categorical data


class Piechart1Request(BaseModel):
    project: str
    step: str
    config: Piechart1Config
    data: Piechart1Data


class Piechart1:
    def __init__(self, data: dict):
        try:
            validated_data = Piechart1Request(**data)
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

        # Create dataframe and get the first column
        df = pd.DataFrame(self.data.values)
        categories = df.iloc[:, 0]  # Get first column

        # Set figure size
        self.figure = plt.figure(figsize=FIGURE_SIZE_A4_PORTRAIT)

        # Count occurrences of each category
        data_counts = Counter(categories)

        # Sort data by counts in ascending order
        sorted_labels, sorted_counts = zip(*sorted(data_counts.items(), key=lambda x: x[1]))

        # Create pie chart
        plt.pie(
            sorted_counts,
            labels=sorted_labels,
            autopct='%1.1f%%',
            startangle=90,
            counterclock=False, 
            colors=COLOR_PALETTE
        )

        # Add title
        plt.title(title, fontsize=TITLE_FONT_SIZE)
        plt.subplots_adjust(top=0.85, bottom=0.1, left=0.15, right=0.85)
        plt.close('all')
        return self.figure
