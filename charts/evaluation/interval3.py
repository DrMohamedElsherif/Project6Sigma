import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from charts.basechart import BaseChart


class Interval3(BaseChart):
    def process(self):
        # Define data and parameters
        df = pd.DataFrame({
            self.chart.config.labels[0]: self.chart.data[0],
            self.chart.config.labels[1]: self.chart.data[1],
            self.chart.config.labels[2]: self.chart.data[2]
        })

        # Set the order of the categories in the 'group' column
        unique_values = df[self.chart.config.labels[0]].unique()
        order = unique_values

        # Add grid lines with both horizontal and vertical lines
        sns.set_style("whitegrid")

        # create facet grid with subplots for each group
        sp = sns.FacetGrid(df, col=self.chart.config.labels[2], col_wrap=2, aspect=1.5, height=5)

        # Plot the stripplot using seaborn's stripplot function and specify the x-axis to be the 'Category' column
        sp.map(sns.pointplot, self.chart.config.labels[0], self.chart.config.labels[1], hue=self.chart.config.labels[2],
               data=df, order=order, marker='o', size=10,
               capsize=0.1, join=False)

        for ax in sp.axes.flat:
            ax.grid(True, axis='both')

        return plt
