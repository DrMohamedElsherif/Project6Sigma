# Import required libraries
import pandas as pd
import matplotlib.pyplot as plt
from charts.basechart import BaseChart
from charts.constants import FIGURE_SIZE_DEFAULT, TITLE_FONT_SIZE, COLORS


class Timeseriesplot3(BaseChart):
    def process(self):
        title = self.chart.config.title
        # Define data and parameters
        df = pd.DataFrame(self.chart.data)

        fig, ax = plt.subplots(figsize=FIGURE_SIZE_DEFAULT)
        for i, (name, group) in enumerate(df.groupby(df.columns[1])):
            ax.plot(group.index, group[df.columns[0]],
                    marker='o', linestyle='-', label=name, color=COLORS[i])

        ax.legend()
        ax.set_xlabel('Index')
        ax.set_ylabel(df.columns[0])

        plt.legend(loc='best')

        plt.title(title, fontsize=TITLE_FONT_SIZE, pad=20)

        # Grid lines
        plt.grid()

        return plt
