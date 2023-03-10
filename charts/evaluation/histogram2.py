# Import required libraries
import matplotlib.pyplot as plt
from charts.basechart import BaseChart
from charts.constants import COLOR_BLACK, COLOR_BLUE, TITLE_FONT_SIZE


class Histogram2(BaseChart):
    def process(self):
        # Define data and parameters
        data = self.chart.data

        # Initialize layout
        fig, ax = plt.subplots(figsize=(15, 11))

        # Enable grid lines
        plt.grid(True)

        # Add labels
        plt.xlabel(self.chart.config.labelx)
        plt.ylabel(self.chart.config.labely)

        # Plot
        ax.hist(
            data,
            edgecolor=COLOR_BLACK,
            align="left",
            color=COLOR_BLUE
        )
        ax.set_title(self.chart.config.title, fontsize=TITLE_FONT_SIZE, pad=20)

        return plt
