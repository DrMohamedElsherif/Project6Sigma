# Import required libraries
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from charts.basechart import BaseChart
from charts.constants import COLOR_BLUE, FIGURE_SIZE_DEFAULT, COLOR_BLACK, TITLE_FONT_SIZE, COLORS

class individual4(BaseChart):
    def process(self):
        
        # Create a sample pandas DataFrame with categorical variables
        df = pd.DataFrame({
            self.chart.config.labels[0]: self.chart.data[0],
            self.chart.config.labels[1]: self.chart.data[1],
            self.chart.config.labels[2]: self.chart.data[2]
        })

       # Define size of figure
        sns.set(style="whitegrid")

        plt.subplots_adjust(left=0.1, bottom=0.1, right=0.9, top=0.9)
        fig, ax = plt.subplots(1, 2, figsize=(15, 11))

        bp = sns.stripplot(y=df[self.chart.config.labels[0]], marker='o', size=10, jitter=False, ax=ax[0])
        bp = sns.stripplot(y=df[self.chart.config.labels[1]], marker='o', size=10, jitter=False, ax=ax[1])

        # add grid lines with both horizontal and vertical lines
        plt.grid(b=True, which='both')
        bp.set_title(self.chart.config.title, fontsize=TITLE_FONT_SIZE, pad=20)

        return plt