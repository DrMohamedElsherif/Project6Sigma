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

        plt.rcParams["figure.figsize"] = (FIGURE_SIZE_DEFAULT)

        # Count occurrences of each element in the data
        data_counts = Counter(df.iloc[:, 0])

        # Extract labels and counts for plotting, sorted by counts in ascending order
        sorted_labels, sorted_counts = zip(
            *sorted(data_counts.items(), key=lambda x: x[1]))

        # Create a pie plot with clockwise arrangement
        plt.pie(sorted_counts, labels=sorted_labels,
                autopct='%1.1f%%', startangle=90, counterclock=False)
        plt.title(title, fontsize=TITLE_FONT_SIZE)

        return plt
