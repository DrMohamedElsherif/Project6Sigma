import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from charts.basechart import BaseChart
from charts.constants import FIGURE_SIZE_DEFAULT, TITLE_FONT_SIZE


class Interval6(BaseChart):
    def process(self):
        title = self.chart.config.title
        df = pd.DataFrame(self.chart.data)

        num_plots = len(df.columns)
        num_cols = 2
        num_rows = (num_plots + num_cols - 1) // num_cols

        plt.figure(figsize=FIGURE_SIZE_DEFAULT)
        plt.suptitle(title, fontsize=TITLE_FONT_SIZE, y=0.95)

        # Loop over columns in the data frame
        for (index, column) in enumerate(df.columns):
            # Calculate means and standard deviations of the data for each loop
            mean = np.mean(df[column])
            # Calculate the 95% confidence intervals for each loop
            stddev = np.std(df[column])
            confidence_interval = 1.96 * stddev / np.sqrt(len(df[column]))

            # add a new subplot iteratively
            ax = plt.subplot(num_rows, num_cols, index + 1)

            # Plot the data for each loop with error bars
            ax.errorbar(x=index, y=mean, yerr=confidence_interval,
                        fmt='o', capsize=15)
            ax.set_title(column)

            # Hide x-axis labels
            ax.set_xticks([])
            # Show grid lines for the current plot
            ax.grid(b=True, which='both', axis='both')

        return plt
