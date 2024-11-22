import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pydantic import BaseModel, Field
from typing import List, Dict
from api.schemas import BusinessLogicException
from api.charts.constants import FIGURE_SIZE_DEFAULT, COLOR_BLACK, TITLE_FONT_SIZE


class Boxplot3Config(BaseModel):
    title: str


class Boxplot3Data(BaseModel):
    values: Dict[str, List[float]] = Field(..., min_length=1)


class Boxplot3Request(BaseModel):
    project: str
    step: str
    config: Boxplot3Config
    data: Boxplot3Data


class Boxplot3:
    def __init__(self, data: dict):
        try:
            validated_data = Boxplot3Request(**data)
            self.project = validated_data.project
            self.step = validated_data.step
            self.config = validated_data.config
            self.data = validated_data.data
            self.figure = None

        except ValueError as e:
            raise BusinessLogicException(
                error_code="validation_error",
                field=str(e),
                details={"message": f"Invalid or missing field: {str(e)}"}
            )

    def process(self):
        title = self.config.title
        df = pd.DataFrame(self.data.values)

        self.figure = plt.figure(figsize=FIGURE_SIZE_DEFAULT)

        # Set the style with grid
        sns.set_style("whitegrid")

        # Create subplot
        ax = self.figure.add_subplot(111)

        # Create boxplot using seaborn
        sns.boxplot(data=df, ax=ax)

        # Add title and adjust layout
        ax.set_title(title, fontsize=TITLE_FONT_SIZE, color=COLOR_BLACK, pad=20)
        plt.tight_layout()

        return self.figure
