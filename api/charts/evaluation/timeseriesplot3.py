import pandas as pd
import matplotlib.pyplot as plt
from charts.basechart import BaseChart
from charts.constants import FIGURE_SIZE_DEFAULT, TITLE_FONT_SIZE, MARKERS


class Timeseriesplot3(BaseChart):
    def process(self):
        title = self.chart.config.title
        # Define data and parameters
        df = pd.DataFrame(self.chart.data)

        fig, axes = plt.subplots(
            ncols=len(df.iloc[:, 1].unique()), sharey=True, figsize=FIGURE_SIZE_DEFAULT)

        for i, (k, g) in enumerate(df.groupby(df.columns[1])):
            g[df.columns[0]].plot(ax=axes[i], marker=MARKERS[0])
            axes[i].set_title(k)
            axes[i].grid()

        plt.suptitle(title, fontsize=TITLE_FONT_SIZE, y=0.98)
        plt.tight_layout()

        return plt
