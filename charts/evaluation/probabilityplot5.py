# Import required libraries
import pandas as pd
import matplotlib.pyplot as plt
import scipy.stats as stats
import numpy as np
from charts.basechart import BaseChart
from charts.constants import FIGURE_SIZE_DEFAULT, TITLE_FONT_SIZE, TITLE_PADDING, COLORS, MARKERS


class Probabilityplot5(BaseChart):
    def process(self):
        title = self.chart.config.title
        # Define data and parameters
        df = pd.DataFrame(self.chart.data)
        # Set additional data
        ad = self.chart.additional_data

        # Calculate the number of columns and rows for the subplots
        num_columns = 2
        # Round up the division
        num_rows = (df.shape[1] + num_columns - 1) // num_columns

        # Create the figure and subplots
        fig, axes = plt.subplots(
            num_rows, num_columns, figsize=(15, 6.5 * num_rows))

        # Flatten the axes array if necessary
        if num_rows > 1:
            axes = axes.flatten()

        # Iterate over each column in the dataframe and plot the data
        for index, column in enumerate(df.columns):
            ax = axes[index]
            data = df[column]

            # Calculate statistical measures
            mean = data.mean()
            stdev = data.std()
            n = len(data)
            result = stats.anderson(data)

            # Retrieve critical values
            ad_stat = result.statistic
            critical_values = result.critical_values

            # Get p-value
            p_value = result.significance_level[np.where(
                result.statistic < result.critical_values)[0][-1]]

            # Fit the data to the normal distribution
            params = stats.norm.fit(data)

            # Create the probability plot
            probplot = stats.probplot(data, plot=None)

            # Scatter plot
            ax.scatter(probplot[0][0], probplot[0][1],
                       color=COLORS[index], marker=MARKERS[index], zorder=3)

            # Add regression line
            regression = np.polyfit(probplot[0][0], probplot[0][1], 1)
            se = np.sqrt(
                np.mean((probplot[0][1] - np.polyval(regression, probplot[0][0])) ** 2))
            conf_interval = stats.t.interval(0.95, len(
                probplot[0][1]) - 2, loc=np.polyval(regression, probplot[0][0]), scale=se)
            ax.plot(probplot[0][0], np.polyval(
                regression, probplot[0][0]), color=COLORS[index], zorder=3)

            # Plot confidence intervals
            ax.fill_between(probplot[0][0], conf_interval[0], conf_interval[1], color=COLORS[index], alpha=0.2,
                            label=f'{column} Confidence Interval (95%)')

            # Set y-axis label
            ax.set_ylabel('Theoretical Quantiles')

            # Set x-axis label for the last row of subplots
            if index >= (num_rows - 1) * num_columns:
                ax.set_xlabel('Ordered Values')

            # Set title for the subplot
            ax.set_title(column)

            # Enable grid lines for both axes
            ax.grid(True, zorder=-1)

            # Add text annotations
            text = f"Mean: {mean}\nStDev: {stdev}\nN: {n}\nAD: {ad_stat}\nP-Value: {p_value:.3f}"
            ax.annotate(text, xy=(0, -0.1), xycoords='axes fraction',
                        fontsize=10, va='top')

            # Hide x-axis labels
            ax.set_xticks([])

        # Remove any empty subplots
        if len(df.columns) < num_rows * num_columns:
            for i in range(len(df.columns), num_rows * num_columns):
                fig.delaxes(axes[i])

        # Adjust the spacing between subplots
        fig.tight_layout()

        return plt
