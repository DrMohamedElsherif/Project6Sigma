# Import required libraries
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from charts.basechart import BaseChart
from charts.constants import COLOR_BLUE, FIGURE_SIZE_DEFAULT, COLOR_BLACK, TITLE_FONT_SIZE, COLORS

class Individual3(BaseChart):
    def process(self):
        
        # Create a sample pandas DataFrame with categorical variables
        df = pd.DataFrame({
            self.chart.config.labels[0]: self.chart.data[0],
            self.chart.config.labels[1]: self.chart.data[1],
            self.chart.config.labels[2]: self.chart.data[2]
        })

        # Set the order of the categories in the 'group' column
        unique_values = df[self.chart.config.labels[0]].unique()
        order = unique_values

        sns.set_style("whitegrid")

        # create facet grid with subplots for each group
        sp = sns.FacetGrid(df, col=self.chart.config.labels[2], col_wrap=2, aspect=1.5, height=5)

       # Plot the stripplot using seaborn's stripplot function and specify the x-axis to be the 'Category' column
        sp.map(sns.stripplot, self.chart.config.labels[0], self.chart.config.labels[1], hue=self.chart.config.labels[2], data=df, order=order, marker='o', size=10, jitter=False, palette=COLORS)

        for ax in sp.axes.flat:
            ax.grid(True, axis='both')

        return plt