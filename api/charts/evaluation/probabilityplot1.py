import pandas as pd
import matplotlib.pyplot as plt
import scipy.stats as stats
import numpy as np
from math import exp
from pydantic import BaseModel, Field
from typing import List, Dict
from api.schemas import BusinessLogicException
from api.charts.constants import FIGURE_SIZE_A4_PORTRAIT, TITLE_FONT_SIZE, TITLE_PADDING


class Probabilityplot1Config(BaseModel):
    title: str


class Probabilityplot1Data(BaseModel):
    values: Dict[str, List[float]] = Field(..., min_length=1)


class Probabilityplot1AdditionalData(BaseModel):
    distribution: str


class Probabilityplot1Request(BaseModel):
    project: str
    step: str
    config: Probabilityplot1Config
    data: Probabilityplot1Data
    additional_data: Probabilityplot1AdditionalData


class Probabilityplot1:
    def __init__(self, data: dict):
        try:
            validated_data = Probabilityplot1Request(**data)
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

        # Calculate p-value
        z = ad_stat * (1 + 0.75 / n + 2.25 / (n ** 2))

        if z >= 0.6:
            p_value = exp(1.2937 - 5.709 * z + 0.0186 * (z ** 2))
        elif 0.34 <= z < 0.6:
            p_value = exp(0.9177 - 4.279 * z - 1.38 * (z ** 2))
        elif 0.2 <= z < 0.34:
            p_value = 1 - exp(-8.318 + 42.796 * z - 59.938 * (z ** 2))
        else:
            p_value = 1 - exp(-13.436 + 101.14 * z - 223.73 * (z ** 2))

        p_value = max(0, p_value)

        # Create probability plot
        params = dist.fit(data)
        probplot = stats.probplot(data, dist=dist(*params), plot=plt)

        # Calculate regression and confidence intervals
        regression = np.polyfit(probplot[0][0], probplot[0][1], 1)
        se = np.sqrt(np.mean((probplot[0][1] - np.polyval(regression, probplot[0][0])) ** 2))
        conf_interval = stats.t.interval(0.95, len(probplot[0][1]) - 2,
                                         loc=np.polyval(regression, probplot[0][0]),
                                         scale=se)

        # Create figure
        self.figure = plt.figure(figsize=FIGURE_SIZE_A4_PORTRAIT)

        # Plot data points and confidence intervals
        plt.scatter(probplot[0][0], probplot[0][1], color='black', zorder=3)
        plt.fill_between(probplot[0][0], conf_interval[0], conf_interval[1],
                         color='#95b92a', alpha=0.2, label='CI (95%)')

        # Set labels and title
        plt.ylabel('Ordered Values')
        plt.title(title, fontsize=TITLE_FONT_SIZE, pad=TITLE_PADDING)
        plt.grid(zorder=-1, alpha=0.3)

        # Add statistics annotation
        text = f"Mean: {round(mean, 3)}\nStDev: {round(stdev, 3)}\nN: {n}\nAD: {round(ad_stat, 3)}\nZ: {round(z, 3)}\nP-Value: {round(p_value, 3)}\n"
        plt.annotate(text, (0, 0), (0, -30), xycoords='axes fraction',
                     textcoords='offset points', va='top', fontsize=12)

        plt.subplots_adjust(top=0.85, bottom=0.4, left=0.15, right=0.85)
        plt.xticks([])
        plt.close('all')
        return self.figure
