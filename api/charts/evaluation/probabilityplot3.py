import pandas as pd
import matplotlib.pyplot as plt
import scipy.stats as stats
import numpy as np
from pydantic import BaseModel, Field
from typing import List, Dict
from api.schemas import BusinessLogicException
from api.charts.constants import FIGURE_SIZE_DEFAULT, TITLE_FONT_SIZE, TITLE_PADDING, COLORS, MARKERS


class Probabilityplot3Config(BaseModel):
    title: str


class Probabilityplot3Data(BaseModel):
    values: Dict[str, List[float]] = Field(..., min_length=1)


class Probabilityplot3Request(BaseModel):
    project: str
    step: str
    config: Probabilityplot3Config
    data: Probabilityplot3Data


class Probabilityplot3:
    def __init__(self, data: dict):
        try:
            validated_data = Probabilityplot3Request(**data)
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

        num_columns = 2
        num_rows = (df.shape[1] + num_columns - 1) // num_columns

        self.figure, axes = plt.subplots(num_rows, num_columns, figsize=(15, 6.5 * num_rows))

        if num_rows > 1:
            axes = axes.flatten()

        for index, column in enumerate(df.columns):
            ax = axes[index]
            data = df[column]

            mean = data.mean()
            stdev = data.std()
            n = len(data)
            result = stats.anderson(data)
            ad_stat = result.statistic
            p_value = result.significance_level[np.where(
                result.statistic < result.critical_values)[0][-1]]

            params = stats.norm.fit(data)
            probplot = stats.probplot(data, plot=None)

            ax.scatter(probplot[0][0], probplot[0][1],
                       color=COLORS[index], marker=MARKERS[index], zorder=3)

            regression = np.polyfit(probplot[0][0], probplot[0][1], 1)
            se = np.sqrt(np.mean((probplot[0][1] - np.polyval(regression, probplot[0][0])) ** 2))
            conf_interval = stats.t.interval(0.95, len(probplot[0][1]) - 2,
                                             loc=np.polyval(regression, probplot[0][0]),
                                             scale=se)

            ax.plot(probplot[0][0], np.polyval(regression, probplot[0][0]),
                    color=COLORS[index], zorder=3)
            ax.fill_between(probplot[0][0], conf_interval[0], conf_interval[1],
                            color=COLORS[index], alpha=0.2,
                            label=f'{column} Confidence Interval (95%)')

            ax.set_ylabel('Theoretical Quantiles')
            if index >= (num_rows - 1) * num_columns:
                ax.set_xlabel('Ordered Values')
            ax.set_title(column)
            ax.grid(True, zorder=-1)

            text = f"Mean: {mean}\nStDev: {stdev}\nN: {n}\nAD: {ad_stat}\nP-Value: {p_value:.3f}"
            ax.annotate(text, xy=(0, -0.1), xycoords='axes fraction',
                        fontsize=10, va='top')
            ax.set_xticks([])

        if len(df.columns) < num_rows * num_columns:
            for i in range(len(df.columns), num_rows * num_columns):
                self.figure.delaxes(axes[i])

        self.figure.tight_layout()
        return self.figure
