# Import required libraries
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from charts.basechart import BaseChart
from charts.constants import TITLE_FONT_SIZE


class Matrixplot3(BaseChart):
    def process(self):
        title = self.chart.config.title
        df = pd.DataFrame(self.chart.data)
        # Set additional data
        ad = self.chart.additional_data

        sns.set(style="whitegrid")

        pp = sns.pairplot(
            df, diag_kind="None", y_vars=df[ad["y_vars"]], x_vars=df[ad["x_vars"]], height=1.8, aspect=1.8)

        pp.fig.suptitle(title, fontsize=TITLE_FONT_SIZE)

        # Adjust space between plot and title
        plt.subplots_adjust(top=0.9)

        return plt
