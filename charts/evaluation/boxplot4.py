# Import required libraries
import pandas as pd
import matplotlib.pyplot as plt
from charts.basechart import BaseChart
from charts.constants import FIGURE_SIZE_DEFAULT, TITLE_FONT_SIZE, COLOR_BLACK, COLOR_BLUE


class Boxplot4(BaseChart):
    def process(self):
        title = self.chart.config.title
        df = pd.DataFrame(self.chart.data)
        # Set additional data
        ad = pd.DataFrame(self.chart.additional_data)

        # Generate plot
        bp = df.boxplot(
            color=COLOR_BLACK,
            patch_artist=True,
            boxprops=dict(facecolor=COLOR_BLUE),
            figsize=FIGURE_SIZE_DEFAULT
        )

        bp.set_title(title, fontsize=TITLE_FONT_SIZE, pad=20)

        return plt
