# Import required libraries
import pandas as pd
import matplotlib.pyplot as plt
from charts.basechart import BaseChart
from charts.constants import FIGURE_SIZE_DEFAULT, TITLE_FONT_SIZE, COLOR_BLACK, COLOR_BLUE


class Boxplot4(BaseChart):
    def process(self):
        title = self.chart.config.title
        df = pd.DataFrame(self.chart.data)
        # Set additional data
        ad = pd.DataFrame(self.chart.additional_data)

        if ad is not None and not ad.empty:
            # Count unique values
            unique_values = ad.iloc[:, 0].unique()
            count = len(unique_values)

            fig, axes = plt.subplots(
                1, count, figsize=FIGURE_SIZE_DEFAULT, sharex=True, sharey=True)

            for i, (category, data) in enumerate(df.join(ad).groupby(ad.columns[0])):
                ax = axes[i]
                data.boxplot(rot=45, color=COLOR_BLACK, patch_artist=True,
                             boxprops=dict(facecolor=COLOR_BLUE), ax=ax)
                ax.set_xlabel(unique_values[i])

            plt.suptitle(title, fontsize=TITLE_FONT_SIZE, y=0.99)
            plt.tight_layout()

        else:
            # Generate plot
            bp = df.boxplot(
                color=COLOR_BLACK,
                patch_artist=True,
                boxprops=dict(facecolor=COLOR_BLUE),
                figsize=FIGURE_SIZE_DEFAULT
            )

            bp.set_title(title, fontsize=TITLE_FONT_SIZE, pad=20)

        return plt
