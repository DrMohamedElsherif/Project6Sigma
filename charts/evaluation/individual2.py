# Import required libraries
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from charts.basechart import BaseChart
from charts.constants import FIGURE_SIZE_DEFAULT, TITLE_FONT_SIZE, COLORS, MARKERS


class Individual2(BaseChart):
    def process(self):
        title = self.chart.config.title
        df = pd.DataFrame(self.chart.data)
        # Set additional data
        ad = self.chart.additional_data

        # Define size of figure
        sns.set(rc={'figure.figsize': FIGURE_SIZE_DEFAULT})
        sns.set(style="whitegrid")

        # Plot the stripplot using seaborn's stripplot function and specify the x-axis to be the 'Category' column
        sp = sns.stripplot(x=ad["catVar"], y=ad["var"], data=df, marker=MARKERS[0], size=10,
                           jitter=False,
                           # the jitter parameter is set to True, which will add the random noise and align the circles horizontally.
                           palette=COLORS)

        # Add grid lines with both horizontal and vertical lines
        plt.grid(visible=True, which='both')
        sp.set_title(title, fontsize=TITLE_FONT_SIZE, pad=20)

        return plt
