# Import required libraries
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from charts.basechart import BaseChart
from charts.constants import FIGURE_SIZE_DEFAULT, COLOR_BLUE, TITLE_FONT_SIZE, TITLE_FONT_SIZE_SMALL, TITLE_PADDING


class Interval1(BaseChart):
    def process(self):
        title = self.chart.config.title
        df = pd.DataFrame(self.chart.data)

        data = df.iloc[:, 0]

        # Calculate mean and standard deviation of the data
        mean = np.mean(data)
        stddev = np.std(data)

        # Calculate the 95% confidence interval
        confidence_interval = 1.96 * stddev / np.sqrt(len(data))

        plt.figure(figsize=FIGURE_SIZE_DEFAULT)

        # Plot the data with error bars
        plt.errorbar(x=1, y=mean, yerr=confidence_interval,
                     fmt='o', capsize=15, color=COLOR_BLUE)

        # Add labels and title to the plot
        plt.ylabel('Value')
        plt.title(title, fontsize=TITLE_FONT_SIZE, pad=TITLE_PADDING)
        plt.figtext(
            0.5, 0.05, df.columns[0], ha="center", fontsize=TITLE_FONT_SIZE_SMALL)

        # Hide x-axis labels
        plt.xticks([])

        # Enable grid lines
        plt.grid(True, which='both')

        return plt
