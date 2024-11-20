# Import required libraries
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from charts.basechart import BaseChart
from charts.constants import TITLE_FONT_SIZE, MARKERS, COLORS


class Matrixplot4(BaseChart):
    def process(self):
        title = self.chart.config.title
        df = pd.DataFrame(self.chart.data)
        # Set additional data
        ad = self.chart.additional_data

        sns.set(style="whitegrid")

        # Set categorical variable
        cat_var = ad["groupVariable"]

        # Get the number of unique values in the column
        num_unique = df[cat_var].nunique()

        # Create scatterplot matrix with overlaid groups
        pp = sns.pairplot(df, hue=cat_var, diag_kind="kde", y_vars=df[ad["y_vars"]], x_vars=df[ad["x_vars"]],
                          markers=MARKERS[0:num_unique], palette=COLORS[0:num_unique], height=1.8, aspect=1.8)

        pp.fig.suptitle(title, fontsize=TITLE_FONT_SIZE)

        # Adjust space between plot and title
        plt.subplots_adjust(top=0.9)

        return plt
