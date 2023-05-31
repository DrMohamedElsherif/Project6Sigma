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
        # Set additional data
        ad = pd.DataFrame(self.chart.additional_data)

        # Define size of figure
        sns.set(rc={'figure.figsize': FIGURE_SIZE_DEFAULT})
        sns.set(style="whitegrid")

        if "catVar" in ad:
            # Combine the dataframes based on index
            combined_df = pd.concat([df, ad], axis=1)

            # Reshape the dataframe to have a single column for y-axis values
            melted_df = combined_df.melt(
                id_vars="catVar", var_name="column", value_name="value")

            sp = sns.stripplot(x="catVar", y="value", hue="column", data=melted_df, dodge=True,
                               marker=MARKERS[0], size=10, jitter=False, palette=COLORS)

            # Set custom labels for the x-axis, y-axis, and legend
            sp.set_xlabel("Categorical Variable")
            sp.set_ylabel("Values")
            plt.legend(title="")
        else:
            sp = sns.stripplot(
                data=df, marker=MARKERS[0], size=10, jitter=False, palette=COLORS)

        sp.set_xticklabels(sp.get_xticklabels(), rotation=45, ha='right')

        # Adjust the layout and padding to prevent xticklabels from being cut off
        plt.tight_layout(pad=1.5)

        # Add grid lines with both horizontal and vertical lines
        plt.grid(b=True, which='both')

        # Set the title for the plot
        sp.set_title(title, fontsize=TITLE_FONT_SIZE, pad=20)

        return plt
