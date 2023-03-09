# Import required libraries
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from charts.basechart import BaseChart
from charts.constants import COLOR_BLUE, FIGURE_SIZE_DEFAULT, COLOR_BLACK, TITLE_FONT_SIZE

class Individual1(BaseChart):
    def process(self):
        # Define data and parameters
        df = pd.DataFrame({'data1': self.chart.data[0]})

        # Define size of figure
        sns.set(rc={'figure.figsize':(15,11)})
        sns.set(style="whitegrid")

        plt.subplots_adjust(left=0.1, bottom=0.1, right=0.9, top=0.9)

        bp = sns.stripplot(y=df["data1"], marker='o', size=10, jitter=False)

        # add grid lines with both horizontal and vertical lines
        plt.grid(b=True, which='both')
        bp.set_title(self.chart.config.title, fontsize=TITLE_FONT_SIZE, pad=20)

        return plt