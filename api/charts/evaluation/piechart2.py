# Import required libraries
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
from charts.basechart import BaseChart
from charts.constants import FIGURE_SIZE_DEFAULT, TITLE_FONT_SIZE


class Piechart2(BaseChart):
    def process(self):
        title = self.chart.config.title
        df = pd.DataFrame(self.chart.data)

        # Define the column count
        num_columns = 2

        # Count the number of columns
        num_datasets = len(df.columns)

        # Find the number of rows needed
        num_rows = num_datasets // 2 + num_datasets % 2

        # Get the column names as a list to plot
        columns = df.columns.tolist()

        # Generate plots with normalized value counts
        fig, axes = plt.subplots(
            num_rows, num_columns, figsize=(FIGURE_SIZE_DEFAULT))

        # Flatten the axes if there's only one row
        axes = axes.flatten()

        for col, ax in zip(columns, axes):
            data_counts = df[col].value_counts(normalize=True)

            if not data_counts.empty:
                ax.pie(data_counts, labels=data_counts.index, autopct='%1.1f%%',
                       startangle=90, colors=plt.cm.Paired.colors)
                ax.set_title(col)

        # Remove empty subplots
        for i in range(len(columns), len(axes)):
            fig.delaxes(axes[i])

        # Set main title for plot
        plt.suptitle(title, fontsize=TITLE_FONT_SIZE)

        plt.tight_layout(rect=[0, 0, 1, 0.95])

        return plt
