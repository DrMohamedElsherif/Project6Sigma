# Import required libraries
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from charts.basechart import BaseChart
from charts.constants import FIGURE_SIZE_DEFAULT, TITLE_FONT_SIZE


class Individual1(BaseChart):
    def process(self):
        title = self.chart.config.title
        df = pd.DataFrame(self.chart.data)

        # Define size of figure
        sns.set(rc={'figure.figsize': FIGURE_SIZE_DEFAULT})
        sns.set(style="whitegrid")

        plt.subplots_adjust(left=0.1, bottom=0.1, right=0.9, top=0.9)
        key, value = list(self.chart.data.items())[0]
        bp = sns.stripplot(y=df[key], marker='o', size=10, jitter=False)

        # add grid lines with both horizontal and vertical lines
        plt.grid(visible=True, which='both')
        bp.set_title(title, fontsize=TITLE_FONT_SIZE, pad=20)

        return plt
