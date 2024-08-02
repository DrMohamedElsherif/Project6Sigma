# Import required libraries
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from charts.basechart import BaseChart
from charts.constants import FIGURE_SIZE_DEFAULT, COLOR_BLACK, TITLE_FONT_SIZE

class Boxplot3(BaseChart):
    def process(self):
        title = self.chart.config.title
        df = pd.DataFrame(self.chart.data)
        self.figure = plt.figure(figsize=(FIGURE_SIZE_DEFAULT))

        # Set the order of the categories in the 'group' column
        unique_values = df[df.columns[1]].unique()
        order = unique_values

        # Add grid lines with both horizontal and vertical lines
        sns.set_style("whitegrid")

        # create facet grid with subplots for each group
        sp = sns.FacetGrid(df, col=df.columns[2], col_wrap=2, aspect=1.5, height=5)

        # Plot the stripplot using seaborn's stripplot function and specify the x-axis to be the 'Category' column
        sp.map(sns.boxplot, df.columns[1], df.columns[0], hue=df.columns[2], data=df, order=order)

        for ax in sp.axes.flat:
            ax.grid(True, axis='both')

        # Add title
        plt.suptitle(title, fontsize=TITLE_FONT_SIZE, color=COLOR_BLACK)
        plt.subplots_adjust(top=0.9, bottom=0.1)

        return plt