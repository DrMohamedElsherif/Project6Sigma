# Import required libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from charts.basechart import BaseChart
from charts.constants import TITLE_FONT_SIZE


class Individual5(BaseChart):
    def process(self):
        title = self.chart.config.title
        df = pd.DataFrame(self.chart.data)

        num_plots = len(df.columns)
        num_cols = 2
        num_rows = (num_plots + num_cols - 1) // num_cols

        # Define size of figure
        sns.set(style="whitegrid")

        plt.subplots_adjust(left=0.1, bottom=0.1, right=0.9, top=0.9)
        fig, axes = plt.subplots(
            num_rows, num_cols, figsize=(15, num_rows * 5))

        # Flatten the axes array if necessary
        axes = axes.flatten() if isinstance(axes, np.ndarray) else [axes]

        # Loop over columns in the data frame
        for (index, column) in enumerate(df.columns):
            ax = axes[index]
            sp = sns.stripplot(y=df[column],
                               marker='o', size=10, jitter=False, ax=ax)
            ax.grid(b=True, which='both', axis='both')

        # Remove any extra subplots
        for i in range(num_plots, len(axes)):
            fig.delaxes(axes[i])

        plt.suptitle(title, fontsize=TITLE_FONT_SIZE)

        # Adjust space between plot and title
        plt.subplots_adjust(top=0.9)

        return plt
