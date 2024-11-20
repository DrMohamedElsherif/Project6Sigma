# Import required libraries
import pandas as pd
import matplotlib.pyplot as plt
import scipy.stats as stats
import numpy as np
from charts.basechart import BaseChart
from charts.constants import FIGURE_SIZE_DEFAULT, TITLE_FONT_SIZE, TITLE_PADDING, COLORS, MARKERS


class Probabilityplot2(BaseChart):
    def process(self):
        title = self.chart.config.title
        # Define data and parameters
        df = pd.DataFrame(self.chart.data)
        # Set additional data
        ad = self.chart.additional_data

        plt.figure(figsize=FIGURE_SIZE_DEFAULT)

        data = df.iloc[:, 0]
        # Calculate statistical measures
        mean = data.mean()
        stdev = data.std()
        n = len(df)
        result = stats.anderson(data)

        # Define the name of the distribution
        dist_name = ad['distribution']

        # Get the distribution object based on the name
        dist = getattr(stats, dist_name)

        # Fit the data to the lognormal distribution
        log_data = np.log(data)
        params = dist.fit(log_data)

        # Retrieve the 'loc' and 'scale' parameters
        loc = params[0]
        scale = params[1]

        # Retrieve critical values
        ad_stat = result.statistic
        critical_values = result.critical_values

        # Get p-value
        p_value = result.significance_level[np.where(
            result.statistic < result.critical_values)[0][-1]]

        # Fit the data to the normal distribution
        params = dist.fit(data)

        # Loop over pd an genrate plots
        for (index, column) in enumerate(df):
            # Fit the data to the normal distribution
            params = dist.fit(df[column])

            # Create the probability plot for 'Hacker-Festzelt'
            probplot = stats.probplot(df[column], plot=None)

            # Scatter plot for 'Hacker-Festzelt' with red color
            plt.scatter(probplot[0][0], probplot[0]
                        [1], color=COLORS[index], marker=MARKERS[index], zorder=3)

            # Add regression line for 'Hacker-Festzelt'
            regression = np.polyfit(probplot[0][0], probplot[0][1], 1)
            se_hacker = np.sqrt(np.mean(
                (probplot[0][1] - np.polyval(regression, probplot[0][0])) ** 2))
            conf_interval = stats.t.interval(0.95, len(
                probplot[0][1]) - 2, loc=np.polyval(regression, probplot[0][0]), scale=se_hacker)
            plt.plot(probplot[0][0], np.polyval(
                regression, probplot[0][0]), color=COLORS[index], zorder=3)

            # Plot confidence intervals for 'Hacker-Festzelt'
            plt.fill_between(probplot[0][0], conf_interval[0], conf_interval[1],
                             color=COLORS[index], alpha=0.2, label='Hacker-Festzelt Confidence Interval (95%)')

        # Set y-axis label
        plt.ylabel('Ordered Values')

        plt.title(title, fontsize=TITLE_FONT_SIZE, pad=TITLE_PADDING)

        plt.grid(zorder=-1)

        # Add text annotations
        text = f"Mean: {mean}\nStDev: {stdev}\nN: {n}\nAD: {ad_stat}\nP-Value: {p_value:.3f}\nLoc: {loc}\nScale: {scale}\n"

        plt.annotate(text, (0, 0), (0, -30), xycoords='axes fraction',
                     textcoords='offset points', va='top', fontsize=12)

        plt.tight_layout()
        # Hide x-axis labels
        plt.xticks([])

        return plt
