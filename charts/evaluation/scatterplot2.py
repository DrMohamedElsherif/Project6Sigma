# Import required libraries
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from charts.basechart import BaseChart
from charts.constants import FIGURE_SIZE_DEFAULT, COLORS, MARKERS


class Scatterplot2(BaseChart):
    def process(self):
        title = self.chart.config.title
        df = pd.DataFrame(self.chart.data)
        # Set additional data
        ad = self.chart.additional_data

        plt.figure(figsize=FIGURE_SIZE_DEFAULT)

        # Get the unique groups
        groups = df[ad["group"]].unique()
        # Assign colors and markers to groups
        colors = dict(zip(groups, COLORS[:len(groups)]))
        markers = dict(zip(groups, MARKERS[:len(groups)]))

        for group in groups:
            group_data = df[df[ad["group"]] == group]
            sns.scatterplot(x=ad["xVar"], y=ad["yVar"], data=group_data,
                            color=colors[group], marker=markers[group], zorder=3, s=80)

        # Create custom legend handles
        legend_handles = [plt.Line2D([0], [0], marker=markers[group], color=colors[group], linestyle='',
                                     label=group) for group in groups]
        plt.legend(handles=legend_handles, title=ad["group"])
        plt.xlabel(ad["xVar"])
        plt.ylabel(ad["yVar"])
        plt.title(title)

        plt.grid(True, which='both', zorder=-1)

        return plt
