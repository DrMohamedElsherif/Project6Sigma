# Import required libraries
import pandas as pd
import matplotlib.pyplot as plt
from charts.basechart import BaseChart
from charts.constants import FIGURE_SIZE_DEFAULT, TITLE_FONT_SIZE, COLORS, MARKERS


class Timeseriesplot5(BaseChart):
    def process(self):
        title = self.chart.config.title
        # Define data and parameters
        df = pd.DataFrame(self.chart.data)

        plt.figure(figsize=FIGURE_SIZE_DEFAULT)

        # Define the column count
        num_columns = 2

        # Count the number of columns
        num_datasets = len(df.columns)

        # Find the number of rows needed
        num_rows = num_datasets // 2 + num_datasets % 2

        # Get the column names as a list to plot
        columns = df.columns.tolist()

        # Generate a list of colors for each subplot
        colors = COLORS[:num_datasets]

        # Generate plots
        bp = df[columns].plot(
            subplots=True,
            layout=(num_rows, num_columns),
            marker=MARKERS[0],
            color=colors,
            grid=True,
            title=columns, figsize=FIGURE_SIZE_DEFAULT,
            zorder=3,
            legend=False
        )

        plt.title(title, fontsize=TITLE_FONT_SIZE, pad=20)

        return plt
