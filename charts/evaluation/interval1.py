# Import required libraries
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from charts.basechart import BaseChart


class Interval1(BaseChart):
    def process(self):
        # Define data and parameters
        df = pd.DataFrame({
            self.chart.config.labels[0]: self.chart.data[0],
            self.chart.config.labels[1]: self.chart.data[1],
            self.chart.config.labels[2]: self.chart.data[2]
        })

        data = df[self.chart.config.labels[0]]

        # Calculate mean and standard deviation of the data
        mean = np.mean(data)
        stddev = np.std(data)

        # Calculate the 95% confidence interval
        confidence_interval = 1.96 * stddev / np.sqrt(len(data))

        # Plot the data with error bars
        plt.errorbar(x=1, y=mean, yerr=confidence_interval, fmt='o', capsize=15)

        # Add labels and title to the plot
        plt.ylabel('Value')
        plt.title(self.chart.config.title)

        # Hide x-axis labels
        plt.xticks([])

        # Enable grid lines
        plt.grid(True, which='both')

        return plt
