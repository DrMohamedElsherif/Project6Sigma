# boxplot1.py

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import pandas as pd
import seaborn as sns
from api.charts.statistics import calculate_descriptive_stats, add_stats_table
from .base_boxplot import BaseBoxplot
from .boxplot_schemas import BoxplotRequest
from ..constants import FIGURE_SIZE_A4_PORTRAIT, TITLE_FONT_SIZE


class Boxplot1(BaseBoxplot):
    request_model = BoxplotRequest
    show_stats_table = True

    # def compute_statistics(self, df):
    #     """
    #     Compute stats for each column, return a dict keyed by column names
    #     """
    #     stats_dict = {}
    #     for col in df.columns:
    #         stats_dict[col] = calculate_descriptive_stats(df[col], column_name=col)
    #     return stats_dict

    # def postprocess(self, ax):
    #     # optional: extra decorations can be added here
    #     pass

    # def process(self):
    #     # Get dataset name if provided
    #     dataset_name = self.data.dataset_name  # now this will be "Machine A"
    #     df = pd.DataFrame(self.data.values)

    #     # Compute statistics
    #     self.statistics = self.compute_statistics(df)

    #     # Create figure with GridSpec (plot + table)
    #     self.figure = plt.figure(figsize=(8, 10))
    #     gs = gridspec.GridSpec(2, 1, height_ratios=[15, 2], hspace=0.000)

    #     # Plot axes
    #     ax = self.figure.add_subplot(gs[0])
    #     self.draw_boxplot(df, ax)
    #     ax.set_title(self.config.title, fontsize=TITLE_FONT_SIZE, pad=0)
    #     ax.grid(True, alpha=0.3)

    #     # Table axes
    #     table_ax = self.figure.add_subplot(gs[1])
    #     table_ax.axis("off")  # hide axes

    #     # Add stats table under plot
    #     add_stats_table(
    #         figure=self.figure,
    #         stats_data=self.statistics,
    #         dataset_name=dataset_name,
    #         fontsize=9
    #     )

    #     return self.figure


