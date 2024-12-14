import pandas as pd
import matplotlib.pyplot as plt
import scipy.stats as stats
import numpy as np
from pydantic import BaseModel, Field
from typing import List, Dict
from api.schemas import BusinessLogicException
from api.charts.constants import FIGURE_SIZE_DEFAULT, TITLE_FONT_SIZE, TITLE_PADDING, COLORS, MARKERS


class Probabilityplot4Config(BaseModel):
    title: str


class Probabilityplot4Data(BaseModel):
    values: Dict[str, List[float]] = Field(..., min_length=1)


class Probabilityplot4AdditionalData(BaseModel):
    distribution: str


class Probabilityplot4Request(BaseModel):
    project: str
    step: str
    config: Probabilityplot4Config
    data: Probabilityplot4Data
    additional_data: Probabilityplot4AdditionalData


class Probabilityplot4:
    def __init__(self, data: dict):
        try:
            validated_data = Probabilityplot4Request(**data)
            self.project = validated_data.project
            self.step = validated_data.step
            self.config = validated_data.config
            self.data = validated_data.data
            self.additional_data = validated_data.additional_data
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
        data = df.iloc[:, 0]

        mean = data.mean()
        stdev = data.std()
        n = len(df)
        result = stats.anderson(data)

        dist_name = self.additional_data.distribution
        dist = getattr(stats, dist_name)

        log_data = np.log(data)
        params = dist.fit(log_data)
        loc = params[0]
        scale = params[1]

        ad_stat = result.statistic
        p_value = result.significance_level[np.where(
            result.statistic < result.critical_values)[0][-1]]

        self.figure = plt.figure(figsize=FIGURE_SIZE_DEFAULT)

        for index, column in enumerate(df):
            params = dist.fit(df[column])
            probplot = stats.probplot(df[column], plot=None)

            plt.scatter(probplot[0][0], probplot[0][1],
                        color=COLORS[index], marker=MARKERS[index], zorder=3)

            regression = np.polyfit(probplot[0][0], probplot[0][1], 1)
            se = np.sqrt(np.mean((probplot[0][1] - np.polyval(regression, probplot[0][0])) ** 2))
            conf_interval = stats.t.interval(0.95, len(probplot[0][1]) - 2,
                                             loc=np.polyval(regression, probplot[0][0]),
                                             scale=se)

            plt.plot(probplot[0][0], np.polyval(regression, probplot[0][0]),
                     color=COLORS[index], zorder=3)
            plt.fill_between(probplot[0][0], conf_interval[0], conf_interval[1],
                             color=COLORS[index], alpha=0.2,
                             label='Confidence Interval (95%)')

        plt.ylabel('Ordered Values')
        plt.title(title, fontsize=TITLE_FONT_SIZE, pad=TITLE_PADDING)
        plt.grid(zorder=-1)

        text = f"Mean: {mean}\nStDev: {stdev}\nN: {n}\nAD: {ad_stat}\nP-Value: {p_value:.3f}\nLoc: {loc}\nScale: {scale}\n"
        plt.annotate(text, (0, 0), (0, -30), xycoords='axes fraction',
                     textcoords='offset points', va='top', fontsize=12)

        plt.tight_layout()
        plt.xticks([])
        plt.close('all')
        return self.figure
