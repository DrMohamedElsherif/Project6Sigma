# Import required libraries
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from charts.basechart import BaseChart
from charts.constants import FIGURE_SIZE_DEFAULT, TITLE_FONT_SIZE


class Scatterplot1(BaseChart):
    def process(self):
        title = self.chart.config.title
        # Define data and parameters
        df = pd.DataFrame(self.chart.data)
        plt.figure(figsize=FIGURE_SIZE_DEFAULT)

        # Set the style to "whitegrid"
        sns.set_style("whitegrid")

        bp = sns.regplot(x=df.iloc[:, 1], y=df.iloc[:, 0], fit_reg=False)
        bp.set_title(title, fontsize=TITLE_FONT_SIZE, pad=20)

        return plt
