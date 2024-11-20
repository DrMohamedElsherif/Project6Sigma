# Import required libraries
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from charts.basechart import BaseChart
from charts.constants import FIGURE_SIZE_DEFAULT, TITLE_FONT_SIZE, MARKERS, COLORS


class Scatterplot4(BaseChart):
    def process(self):
        title = self.chart.config.title
        df = pd.DataFrame(self.chart.data)
        # Set additional data
        ad = self.chart.additional_data

        plt.figure(figsize=FIGURE_SIZE_DEFAULT)

        values = ad["yVars"]

        # Loop over y vars
        for index, value in enumerate(values):
            sns.regplot(x=ad["xVar"], y=value, data=df,
                        fit_reg=False, color=COLORS[index], marker=MARKERS[index], label=value)

        plt.legend()
        plt.xlabel(ad["xVar"])
        plt.ylabel('Y-Data')
        plt.title(title, fontsize=TITLE_FONT_SIZE, pad=20)

        plt.grid(True)

        return plt
