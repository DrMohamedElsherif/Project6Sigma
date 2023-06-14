# Import required libraries
import pandas as pd
import matplotlib.pyplot as plt
import scipy.stats as stats
import numpy as np
from math import exp
from charts.basechart import BaseChart
from charts.constants import FIGURE_SIZE_DEFAULT, TITLE_FONT_SIZE, TITLE_PADDING


class Probabilityplot1(BaseChart):
    def process(self):
        title = self.chart.config.title
        # Define data and parameters
        df = pd.DataFrame(self.chart.data)
        # Set additional data
        ad = self.chart.additional_data
        # Assign data
        data = df.iloc[:, 0]

        # Calculate statistical measures
        mean = data.mean()
        stdev = data.std()
        n = len(df)

        # Define the name of the distribution
        dist_name = ad['distribution']

        # Get the distribution object based on the name
        dist = getattr(stats, dist_name)

        # Anderson Test
        result = stats.anderson(data)

        # Retrieve critical values
        ad_stat = result.statistic

        # Get p-value from calculation (see sixsigma excel example file)
        z = ad_stat * (1 + 0.75 / n + 2.25 / (n**2))

        if z >= 0.6:
            p_value = exp(1.2937 - 5.709 * z + 0.0186 * (z ** 2))
        elif 0.34 <= z < 0.6:
            p_value = exp(0.9177 - 4.279 * z - 1.38 * (z ** 2))
        elif 0.2 <= z < 0.34:
            p_value = 1 - exp(-8.318 + 42.796 * z - 59.938 * (z ** 2))
        else:
            p_value = 1 - exp(-13.436 + 101.14 * z - 223.73 * (z ** 2))

        if p_value < 0:
            p_value = 0

        # Fit the data to the selected distribution
        params = dist.fit(data)

        # Create the probability plot
        probplot = stats.probplot(data,
                                  dist=dist(*params), plot=plt)

        regression = np.polyfit(probplot[0][0], probplot[0][1], 1)

        se = np.sqrt(np.mean(
            (probplot[0][1] - np.polyval(regression, probplot[0][0])) ** 2))

        conf_interval = stats.t.interval(0.95, len(
            probplot[0][1]) - 2, loc=np.polyval(regression, probplot[0][0]), scale=se)

        plt.figure(figsize=FIGURE_SIZE_DEFAULT)

        # Scatter plot for data points
        plt.scatter(probplot[0][0], probplot[0][1], color='blue', zorder=3)

        # Plot confidence intervals for 'Hacker-Festzelt'
        plt.fill_between(probplot[0][0], conf_interval[0], conf_interval[1],
                         color='red', alpha=0.2, label='CI (95%)')

        # Set y-axis label
        plt.ylabel('Ordered Values')

        plt.title(title, fontsize=TITLE_FONT_SIZE, pad=TITLE_PADDING)

        plt.grid(zorder=-1)

        # Add text annotations
        text = f"Mean: {round(mean,3)}\nStDev: {round(stdev,3)}\nN: {n}\nAD: {round(ad_stat,3)}\nZ: {round(z,3)}\nP-Value: {round(p_value,3)}\n"

        plt.annotate(text, (0, 0), (0, -30), xycoords='axes fraction',
                     textcoords='offset points', va='top', fontsize=12)

        plt.tight_layout()
        # Hide x-axis labels
        plt.xticks([])

        return plt
