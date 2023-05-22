# Import required libraries
import pandas as pd
import matplotlib.pyplot as plt
from charts.basechart import BaseChart
from charts.constants import COLOR_BLACK, TITLE_FONT_SIZE, COLOR_BLUE


class Histogram3(BaseChart):
    def process(self):
        title = self.chart.config.title
        # Define data and parameters
        df = pd.DataFrame(self.chart.data)

        # Count the number of columns
        num_columns = len(df.columns)

        # Calculate the number of rows and columns for the subplots
        num_rows = (num_columns + 1) // 2
        num_cols = min(num_columns, 2)

        # Initialize the subplots
        fig, axes = plt.subplots(num_rows, num_cols, figsize=(
            15, num_rows * 5), sharey='row', squeeze=False)

        # Enable grid lines
        for ax_row in axes:
            for ax in ax_row:
                ax.grid(True, zorder=-1)

        # Iterate over the columns and create a histogram for each
        for i, column in enumerate(df.columns):
            # Determine the subplot coordinates
            row = i // num_cols
            col = i % num_cols

            # Select the current subplot
            ax = axes[row, col]

            # Plot the histogram
            ax.hist(
                df[column],
                edgecolor=COLOR_BLACK,
                align="left",
                color=COLOR_BLUE,
                zorder=3
            )

            # Set the subplot title
            ax.set_title(column)

        # Remove empty subplots
        if num_columns % 2 != 0:
            fig.delaxes(axes[-1, -1])

        # Add overall figure title
        fig.suptitle(title, fontsize=TITLE_FONT_SIZE, y=0.98)

        # Adjust the spacing between subplots
        fig.subplots_adjust(hspace=0)

        return plt
