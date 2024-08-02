# Import required libraries
import pandas as pd
import matplotlib.pyplot as plt
from charts.basechart import BaseChart
from charts.constants import COLOR_BLACK, TITLE_FONT_SIZE, COLORS, FIGURE_SIZE_DEFAULT


class Histogram5(BaseChart):
    def process(self):
        title = self.chart.config.title
        # Define data and parameters
        df = pd.DataFrame(self.chart.data)

        # Count the number of columns
        num_datasets = len(df.columns)

        # Define the column count
        num_columns = 2

        # Count the number of columns
        num_datasets = len(df.columns)

        # Generate a list of colors for each subplot
        colors = COLORS[:num_datasets]

        # Find the number of rows needed
        num_rows = num_datasets // 2 + num_datasets % 2

        # Get the column names as a list to plot
        columns = df.columns.tolist()

        # Generate plots
        bp = df[columns].plot.hist(
            subplots=True,
            layout=(num_rows, num_columns),
            color=colors,
            edgecolor=COLOR_BLACK,
            grid=True,
            title=columns,
            figsize=[15, num_rows * 5],
            zorder=3,
            legend=False
        )

        return plt
