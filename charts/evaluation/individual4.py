# Import required libraries
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from charts.basechart import BaseChart
from charts.constants import FIGURE_SIZE_DEFAULT, TITLE_FONT_SIZE, COLORS, MARKERS


class Individual4(BaseChart):
    def process(self):
        title = self.chart.config.title
        df = pd.DataFrame(self.chart.data)

        # Define size of figure
        sns.set(rc={'figure.figsize': FIGURE_SIZE_DEFAULT})
        sns.set(style="whitegrid")

        sp = sns.stripplot(
            data=df, marker=MARKERS[0], size=10, jitter=False, palette=COLORS)

        sp.set_xticks(range(len(sp.get_xticklabels())))
        sp.set_xticklabels(sp.get_xticklabels(), rotation=45, ha='right')

        # Adjust the layout and padding to prevent xticklabels from being cut off
        plt.tight_layout(pad=1.5)

        # Add grid lines with both horizontal and vertical lines
        plt.grid(b=True, which='both')

        # Set the title for the plot
        sp.set_title(title, fontsize=TITLE_FONT_SIZE, pad=20)

        return plt
