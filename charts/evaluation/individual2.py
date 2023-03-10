# Import required libraries
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from charts.basechart import BaseChart
from charts.constants import COLOR_BLUE, FIGURE_SIZE_DEFAULT, COLOR_BLACK, TITLE_FONT_SIZE, COLORS

class individual2(BaseChart):
    def process(self):
        # Define data and parameters
        title = "Einzelwertdiagramm mit kategorialen Variablen"
        colors = COLORS

        # Create a sample pandas DataFrame with categorical variables
        df = pd.DataFrame({
            self.chart.config.labels[0]: self.chart.data[0],
            self.chart.config.labels[1]: self.chart.data[1]
        })

        # Define size of figure
        sns.set(rc={'figure.figsize':(15,11)})
        sns.set(style="whitegrid")

        # Plot the stripplot using seaborn's stripplot function and specify the x-axis to be the 'Category' column
        sp = sns.stripplot(x=self.chart.config.labels[0], y=self.chart.config.labels[1], data=df, marker='o', size=10, jitter=False, palette=colors) # the jitter parameter is set to True, which will add the random noise and align the circles horizontally.

        # Add grid lines with both horizontal and vertical lines
        plt.grid(b=True, which='both')
        sp.set_title(self.chart.config.title, fontsize=TITLE_FONT_SIZE, pad=20)
        
        return plt