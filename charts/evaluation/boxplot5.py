# Import required libraries
import pandas as pd
import matplotlib.pyplot as plt
from charts.basechart import BaseChart
from charts.constants import COLOR_BLUE, FIGURE_SIZE_DEFAULT, COLOR_BLACK, TITLE_FONT_SIZE


class Boxplot3(BaseChart):
    def process(self):
        title = self.chart.config.title
        df = pd.DataFrame(self.chart.data)
        self.figure = plt.figure(figsize=(FIGURE_SIZE_DEFAULT))
        # Define the column count
        num_columns = 2

        # Count the number of columns
        num_datasets = len(df.columns)

        # Find the number of rows needed
        num_rows = num_datasets // 2 + num_datasets % 2

        # Get the column names as a list to plot
        columns = df.columns.tolist()

        # Generate plots
        bp = df[columns].plot.box(
            subplots=True,
            layout=(num_rows, num_columns),
            color=COLOR_BLACK,
            patch_artist=True,
            grid=True,
            boxprops=dict(facecolor=COLOR_BLUE),
            title=columns, figsize=FIGURE_SIZE_DEFAULT
        )

        # Set main title for plot
        plt.suptitle(title, fontsize=TITLE_FONT_SIZE)

        return plt
