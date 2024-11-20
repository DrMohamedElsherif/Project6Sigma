# Import required libraries
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from charts.basechart import BaseChart
from charts.constants import TITLE_FONT_SIZE, COLORS


class Individual3(BaseChart):
    def process(self):
        title = self.chart.config.title
        df = pd.DataFrame(self.chart.data)
        # Set additional data
        ad = self.chart.additional_data

        # Set the order of the categories in the 'group' column
        unique_values = df[ad["catVar"]].unique()
        order = unique_values

        sns.set_style("whitegrid")

        # create facet grid with subplots for each group
        sp = sns.FacetGrid(df, col=ad["group"],
                           col_wrap=2, aspect=1.5, height=5)

        # Plot the stripplot using seaborn's stripplot function and specify the x-axis to be the 'Category' column
        sp.map(sns.stripplot, ad["catVar"], ad["var"], hue=ad["group"],
               data=df, order=order, marker='o', size=10, jitter=False, palette=COLORS)

        sp.fig.suptitle(title, fontsize=TITLE_FONT_SIZE)

        # Adjust space between plot and title
        plt.subplots_adjust(top=0.9)

        for ax in sp.axes.flat:
            ax.grid(True, axis='both')

        return plt
