import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from charts.basechart import BaseChart


class Interval4(BaseChart):
    def process(self):
        # Define data and parameters
        df = pd.DataFrame({
            self.chart.config.labels[0]: self.chart.data[0],
            self.chart.config.labels[1]: self.chart.data[1],
            self.chart.config.labels[2]: self.chart.data[2]
        })

        num_plots = len(df.columns)
        num_cols = 2
        num_rows = (num_plots + num_cols - 1) // num_cols

        plt.figure(figsize=(15, 11))
        plt.suptitle(self.chart.config.title, fontsize=18, y=0.95)

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
            ax.errorbar(x=index, y=mean, yerr=confidence_interval, fmt='o', capsize=15)
            ax.set_title("Data {}".format(index + 1))

            # Hide x-axis labels
            ax.set_xticks([])
            # Show grid lines for the current plot
            ax.grid(b=True, which='both', axis='both')

        return plt
