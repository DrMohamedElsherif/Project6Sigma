# Import required libraries
import pandas as pd
import matplotlib.pyplot as plt
from charts.basechart import BaseChart
from charts.constants import FIGURE_SIZE_DEFAULT, TITLE_FONT_SIZE, COLORS, MARKERS, LINES


class Timeseriesplot2(BaseChart):
    def process(self):
        title = self.chart.config.title
        # Define data and parameters
        df = pd.DataFrame(self.chart.data)

        plt.figure(figsize=FIGURE_SIZE_DEFAULT)

        # Loop over pd an genrate plots
        for (index, column) in enumerate(df):
            y = df[column]
            x = range(1, df[column].count() + 1)
            count = df[column].count()

            plt.plot((x + (index * count)), y,
                     linestyle=LINES[index], marker=MARKERS[index], color=COLORS[index], label=df.columns[index])

        plt.legend(loc='best')

        plt.title(title, fontsize=TITLE_FONT_SIZE, pad=20)

        # Grid lines
        plt.grid()

        return plt
