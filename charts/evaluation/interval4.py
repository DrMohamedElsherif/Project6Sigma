import math
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
            grouped_data = df.groupby(ad.iloc[:, 0])

            # Define the order of categories
            unique_values = ad.iloc[:, 0].unique()

            # Determine the layout of subplots
            n_cols = 2
            n_subplots = len(df.columns)

            # Calculate the number of rows
            n_rows = math.ceil(n_subplots / n_cols)

            # Create subplots for each column
            fig, axes = plt.subplots(
                n_rows, n_cols, figsize=(15, n_rows * 5))

            # Reshape the axes array
            axes = axes.reshape(-1)

            # Loop over the columns and generate plots
            for i, column in enumerate(df.columns):
                ax = axes[i]

                # Loop over the unique values and categories simultaneously
                for j, (value, category) in enumerate(zip(unique_values, ad.iloc[:, 0])):
                    # Get the data for the current category and column
                    group_df = grouped_data.get_group(category)
                    values = group_df[column]

                    # Calculate mean and confidence interval
                    mean = np.mean(values)
                    stddev = np.std(values)
                    confidence_interval = 1.96 * stddev / np.sqrt(len(values))

                    # Plot the data for each category with error bars
                    ax.errorbar(x=j, y=mean, yerr=confidence_interval,
                                fmt='o', capsize=15, label=category)

                # Set the x-axis tick positions and labels
                ax.set_xticks(range(len(unique_values)))
                ax.set_xticklabels(unique_values)

                # Add labels, title, and legend to the plot
                ax.set_ylabel('Values')
                ax.set_title(column)
                ax.legend(loc='best')

                # Enable grid lines
                ax.grid(b=True, which='both')

            # Hide any extra subplots
            for i in range(n_subplots, len(axes)):
                fig.delaxes(axes[i])

            # Adjust the subplot layout
            plt.subplots_adjust(hspace=0.4)

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

        # Adjust the subplot layout
        plt.tight_layout()

        return plt
