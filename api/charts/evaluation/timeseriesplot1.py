# Import required libraries
import pandas as pd
import matplotlib.pyplot as plt
from charts.basechart import BaseChart
from charts.constants import FIGURE_SIZE_DEFAULT, TITLE_FONT_SIZE, COLOR_BLUE


class Timeseriesplot1(BaseChart):
    def process(self):
        title = self.chart.config.title
        # Define data and parameters
        df = pd.DataFrame(self.chart.data)
        y = df.iloc[:, 0]
        x = range(1, df.iloc[:, 0].count() + 1)

        plt.figure(figsize=FIGURE_SIZE_DEFAULT)
        plt.plot(x, y, linestyle='-', marker='o', color=COLOR_BLUE)
        plt.title(title, fontsize=TITLE_FONT_SIZE, pad=20)

        # Enable grid lines
        plt.grid(True, which='both')

        return plt
