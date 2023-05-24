import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from charts.basechart import BaseChart
from charts.constants import FIGURE_SIZE_DEFAULT, TITLE_FONT_SIZE, TITLE_PADDING


class Interval4(BaseChart):
    def process(self):
        title = self.chart.config.title
        df = pd.DataFrame(self.chart.data)
        # Set additional data
        ad = pd.DataFrame(self.chart.additional_data)

        plt.figure(figsize=FIGURE_SIZE_DEFAULT)

        if ad is not None and not ad.empty:
            # Group the data by a categorical variable
            grouped_data = df.groupby('Kategorie')

            # Loop over the groups and generate plots
            for (group, group_df) in grouped_data:
                # Calculate means and standard deviations of the data for each group
                mean = group_df.mean()
                stddev = group_df.std()
                confidence_interval = 1.96 * stddev / np.sqrt(len(group_df))

                # Plot the data for each group with error bars
                plt.errorbar(x=np.arange(len(mean)), y=mean, yerr=confidence_interval,
                             fmt='o', capsize=15, label=group)

            # Add labels, title, and legend to the plot
            plt.ylabel('Values')
            # Hide x-axis labels
            plt.xticks(np.arange(len(mean)), mean.index, rotation=45)
            plt.title(title, fontsize=TITLE_FONT_SIZE, pad=TITLE_PADDING)
            plt.legend(loc='best')

            # Enable grid lines
            plt.grid(b=True, which='both')

        else:
            # Loop over pd an genrate plots
            for (index, column) in enumerate(df):
                # Calculate means and standard deviations of the data for each loop
                mean = np.mean(df[column])
                # Calculate the 95% confidence intervals for each loop
                stddev = np.std(df[column])
                confidence_interval = 1.96 * stddev / np.sqrt(len(df[column]))

                # Plot the data for each loop with error bars
                plt.errorbar(x=index, y=mean, yerr=confidence_interval,
                             fmt='o', capsize=15, label=column)

                # Add labels, title, and legend to the plot
                plt.ylabel('Values')
                # Hide x-axis labels
                plt.xticks([])
                plt.title(title, fontsize=TITLE_FONT_SIZE, pad=TITLE_PADDING)
                plt.legend(loc='best')

                # Enable grid lines
                plt.grid(b=True, which='both')

        return plt
