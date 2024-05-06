# Import required libraries
import pandas as pd
import matplotlib.pyplot as plt
from charts.basechart import BaseChart
from charts.constants import COLORS, FIGURE_SIZE_DEFAULT, COLOR_BLACK, TITLE_FONT_SIZE


class Boxplot1(BaseChart):
    def process(self):
        title = self.chart.config.title
        df = pd.DataFrame(self.chart.data)

        with plt.figure(figsize=FIGURE_SIZE_DEFAULT) as self.figure:
            key, value = list(self.chart.data.items())[0]
            # Generate plot
            bp = df.boxplot(
                column=[key],
                color=COLOR_BLACK,
                patch_artist=True,
                boxprops=dict(facecolor=COLORS[0]),
                figsize=FIGURE_SIZE_DEFAULT
            )
            bp.set_title(title, fontsize=TITLE_FONT_SIZE, pad=20)

        return self.figure
