# Import required libraries
import pandas as pd
import matplotlib.pyplot as plt
from charts.basechart import BaseChart
from charts.constants import COLOR_BLUE, FIGURE_SIZE_DEFAULT, COLOR_BLACK, TITLE_FONT_SIZE


class Boxplot2(BaseChart):
    def process(self):
        title = self.chart.config.title
        df = pd.DataFrame(self.chart.data)

        # Get the column names as a list to plot
        columns = df.columns.tolist()

        # Generate plot
        bp = df[columns].plot.box(
            color=COLOR_BLACK,
            patch_artist=True,
            grid=True,
            boxprops=dict(facecolor=COLOR_BLUE),
            figsize=FIGURE_SIZE_DEFAULT
        )
        bp.set_title(title, fontsize=TITLE_FONT_SIZE, pad=20)
        self.figure = bp.get_figure()

        return plt
