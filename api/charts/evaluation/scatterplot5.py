# Import required libraries
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from charts.basechart import BaseChart
from charts.constants import TITLE_FONT_SIZE


class Scatterplot5(BaseChart):
    def process(self):
        title = self.chart.config.title
        df = pd.DataFrame(self.chart.data)
        # Set additional data
        ad = self.chart.additional_data

        num_plots = len(ad["yVars"])
        num_cols = 2
        num_rows = (num_plots + num_cols - 1) // num_cols

        fig, axes = plt.subplots(
            num_rows, num_cols, figsize=(15, num_rows * 5))
        axes = axes.flatten()

        for i, y_variable in enumerate(ad["yVars"]):
            ax = axes[i]
            sns.scatterplot(data=df, x=ad["xVar"],
                            y=y_variable, ax=ax, zorder=3)
            ax.grid(True, axis='both', zorder=-1)

        # Remove any extra subplots
        for i in range(num_plots, len(axes)):
            fig.delaxes(axes[i])

        plt.tight_layout()
        # Adjust spacing between title and subplots
        plt.subplots_adjust(top=0.9)
        plt.suptitle(title, fontsize=TITLE_FONT_SIZE, y=0.98)

        return plt
