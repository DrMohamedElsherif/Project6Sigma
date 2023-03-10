import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from charts.basechart import BaseChart


class Interval2(BaseChart):
    def process(self):
        # Define data and parameters
        df = pd.DataFrame({
            self.chart.config.labels[0]: self.chart.data[0],
            self.chart.config.labels[1]: self.chart.data[1],
            self.chart.config.labels[2]: self.chart.data[2]
        })

        plt.figure(figsize=(15, 11))

        # Loop over pd an genrate plots
        for (index, column) in enumerate(df):
            # Calculate means and standard deviations of the data for each loop
            mean = np.mean(df[column])
            # Calculate the 95% confidence intervals for each loop
            stddev = np.std(df[column])
            confidence_interval = 1.96 * stddev / np.sqrt(len(df[column]))

            # Plot the data for each loop with error bars
            plt.errorbar(x=index, y=mean, yerr=confidence_interval, fmt='o', capsize=15)

        # Add labels, title, and legend to the plot
        plt.ylabel('Values')
        # Hide x-axis labels
        plt.xticks([])
        plt.title(self.chart.config.title)

        # Enable grid lines
        plt.grid(b=True, which='both')

        return plt
