import pandas as pd
import matplotlib.pyplot as plt
from pydantic import BaseModel, Field
from typing import List, Dict
from api.schemas import BusinessLogicException
from api.charts.constants import FIGURE_SIZE_A4_PORTRAIT, TITLE_FONT_SIZE, MARKERS, COLOR_PALETTE


class Timeseriesplot3Config(BaseModel):
    title: str


class Timeseriesplot3Data(BaseModel):
    values: Dict[str, List[float]] = Field(..., min_length=1)
    groups: Dict[str, List[str]] = Field(..., min_length=1)


class Timeseriesplot3Request(BaseModel):
    project: str
    step: str
    config: Timeseriesplot3Config
    data: Timeseriesplot3Data


class Timeseriesplot3:
    def __init__(self, data: dict):
        try:
            validated_data = Timeseriesplot3Request(**data)
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
        df = pd.DataFrame({
            'values': list(self.data.values.values())[0],
            'groups': list(self.data.groups.values())[0]
        })

        unique_groups = df['groups'].unique()
        self.figure, axes = plt.subplots(
            ncols=len(unique_groups),
            sharey=True,
            figsize=FIGURE_SIZE_A4_PORTRAIT
        )

        for i, (k, g) in enumerate(df.groupby('groups')):
            g['values'].plot(ax=axes[i], marker=MARKERS[0], color=COLOR_PALETTE[i*2])
            axes[i].set_title(k)
            axes[i].grid(True, alpha=0.3)

        plt.suptitle(title, fontsize=TITLE_FONT_SIZE, y=0.98)
        plt.subplots_adjust(top=0.85, bottom=0.4, left=0.1, right=0.9)
        plt.close('all')
        return self.figure
