# Import required libraries
import pandas as pd
import matplotlib.pyplot as plt
from charts.basechart import BaseChart
from charts.constants import COLOR_BLACK, TITLE_FONT_SIZE, COLORS, FIGURE_SIZE_DEFAULT


class Histogram4(BaseChart):
    def process(self):
        title = self.chart.config.title
        # Define data and parameters
        df = pd.DataFrame(self.chart.data)

        # Count the number of columns
        num_datasets = len(df.columns)

        # Extract data into separate arrays
        data = [df[column].values.tolist() for column in df.columns]

        # Generate a list of colors for each subplot
        colors = COLORS[:num_datasets]

        # Initialize layout
        fig, ax = plt.subplots(figsize=FIGURE_SIZE_DEFAULT)

        # Enable grid lines
        plt.grid(True)

        # Add labels
        plt.xlabel("Data")
        plt.ylabel("Frequency")

        # Plot
        handles = ax.hist(
            data,
            edgecolor=COLOR_BLACK,
            align="left",
            stacked=True,
            zorder=3,
            histtype='barstacked',
            color=colors,
            label=df.columns.tolist()
        )

        ax.set_title(title, fontsize=TITLE_FONT_SIZE, pad=20)

        # Add legend
        plt.legend(loc='best')

        return plt
