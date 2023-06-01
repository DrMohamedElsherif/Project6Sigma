# Import required libraries
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from charts.basechart import BaseChart
from charts.constants import FIGURE_SIZE_DEFAULT, COLORS, MARKERS


class Scatterplot3(BaseChart):
    def process(self):
        title = self.chart.config.title
        df = pd.DataFrame(self.chart.data)
        # Set additional data
        ad = self.chart.additional_data

        g = sns.FacetGrid(df, col=ad["group"],
                          col_wrap=2, aspect=1.5, height=5)
        g.map(sns.scatterplot, ad["yVar"],
              ad["xVar"], zorder=3)

        g.set_titles(col_template="{col_name}")
        g.set_axis_labels(ad["yVar"], ad["xVar"])

        for ax in g.axes:
            ax.grid(True, axis='both', zorder=-1)

        plt.subplots_adjust(top=0.9)
        g.fig.suptitle('title')

        return plt
