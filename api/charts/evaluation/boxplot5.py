import pandas as pd
import matplotlib.pyplot as plt
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from api.schemas import BusinessLogicException
from api.charts.constants import FIGURE_SIZE_DEFAULT, TITLE_FONT_SIZE, COLOR_BLACK, COLOR_BLUE


class Boxplot5Config(BaseModel):
    title: str


class Boxplot5Data(BaseModel):
    values: Dict[str, List[float]] = Field(..., min_length=1)
    categories: Optional[Dict[str, List[str]]] = None


class Boxplot5Request(BaseModel):
    project: str
    step: str
    config: Boxplot5Config
    data: Boxplot5Data


class Boxplot5:
    def __init__(self, data: dict):
        try:
            validated_data = Boxplot5Request(**data)
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
        categories_data = self.data.categories

        if categories_data is not None:
            categories_df = pd.DataFrame(categories_data)
            unique_categories = categories_df.iloc[:, 0].unique()
            count = len(unique_categories)

            self.figure, axes = plt.subplots(
                1, count, figsize=FIGURE_SIZE_DEFAULT, sharex=True, sharey=True)

            for i, (category, data) in enumerate(df.join(categories_df).groupby(categories_df.columns[0])):
                ax = axes[i]
                data.boxplot(rot=45, color=COLOR_BLACK, patch_artist=True,
                             boxprops=dict(facecolor=COLOR_BLUE), ax=ax)
                ax.set_xlabel(unique_categories[i])

            self.figure.suptitle(title, fontsize=TITLE_FONT_SIZE, y=0.99)
            plt.tight_layout()

        else:
            self.figure = plt.figure(figsize=FIGURE_SIZE_DEFAULT)
            ax = self.figure.add_subplot(111)

            df.boxplot(
                color=COLOR_BLACK,
                patch_artist=True,
                boxprops=dict(facecolor=COLOR_BLUE),
                ax=ax
            )

            ax.set_title(title, fontsize=TITLE_FONT_SIZE, pad=20)

        return self.figure
