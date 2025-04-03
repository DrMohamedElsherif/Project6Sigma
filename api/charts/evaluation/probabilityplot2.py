import pandas as pd
import matplotlib.pyplot as plt
import scipy.stats as stats
import numpy as np
from pydantic import BaseModel, Field
from typing import List, Dict
from api.schemas import BusinessLogicException
from api.charts.constants import FIGURE_SIZE_A4_PORTRAIT, TITLE_FONT_SIZE, TITLE_PADDING, COLOR_PALETTE, MARKERS


class Probabilityplot2Config(BaseModel):
    title: str


class Probabilityplot2Data(BaseModel):
    values: Dict[str, List[float]] = Field(..., min_length=1)


class Probabilityplot2AdditionalData(BaseModel):
    distribution: str


class Probabilityplot2Request(BaseModel):
    project: str
    step: str
    config: Probabilityplot2Config
    data: Probabilityplot2Data
    additional_data: Probabilityplot2AdditionalData


class Probabilityplot2:
    def __init__(self, data: dict):
        try:
            validated_data = Probabilityplot2Request(**data)
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

        # Create DataFrame and get data
        df = pd.DataFrame(self.data.values)
        data = df.iloc[:, 0]

        # Calculate statistics
        mean = data.mean()
        stdev = data.std()
        n = len(df)

        # Get distribution and perform Anderson-Darling test
        dist_name = self.additional_data.distribution
        dist = getattr(stats, dist_name)
        result = stats.anderson(data)
        ad_stat = result.statistic

        # Calculate log parameters
        log_data = np.log(data)
        params = dist.fit(log_data)
        loc = params[0]
        scale = params[1]

        # Get p-value
        p_value = result.significance_level[np.where(
            result.statistic < result.critical_values)[0][-1]]

        # Create figure
        self.figure = plt.figure(figsize=FIGURE_SIZE_A4_PORTRAIT)

        # Create plots for each column
        for index, column in enumerate(df):
            params = dist.fit(df[column])
            probplot = stats.probplot(df[column], plot=None)

            plt.scatter(probplot[0][0], probplot[0][1],
                        color=COLOR_PALETTE[index*2], marker=MARKERS[index], zorder=3)

            regression = np.polyfit(probplot[0][0], probplot[0][1], 1)
            se = np.sqrt(np.mean((probplot[0][1] - np.polyval(regression, probplot[0][0])) ** 2))
            conf_interval = stats.t.interval(0.95, len(probplot[0][1]) - 2,
                                             loc=np.polyval(regression, probplot[0][0]),
                                             scale=se)

            plt.plot(probplot[0][0], np.polyval(regression, probplot[0][0]),
                     color=COLOR_PALETTE[index*2], zorder=3)
            plt.fill_between(probplot[0][0], conf_interval[0], conf_interval[1],
                             color=COLOR_PALETTE[index*2], alpha=0.2,
                             label='Confidence Interval (95%)')

        # Set labels and title
        plt.ylabel('Ordered Values')
        plt.title(title, fontsize=TITLE_FONT_SIZE, pad=TITLE_PADDING)
        plt.grid(zorder=-1)

        # Add statistics annotation
        text = f"Mean: {mean}\nStDev: {stdev}\nN: {n}\nAD: {ad_stat}\nP-Value: {p_value:.3f}\nLoc: {loc}\nScale: {scale}\n"
        plt.annotate(text, (0, 0), (0, -30), xycoords='axes fraction',
                     textcoords='offset points', va='top', fontsize=12)

        plt.subplots_adjust(top=0.85, bottom=0.4, left=0.1, right=0.9)
        plt.xticks([])
        plt.close('all')
        return self.figure
