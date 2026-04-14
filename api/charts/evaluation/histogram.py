# api/charts/evaluation/histogram.py

from api.charts.core.base_chart import BaseChart
from api.charts.evaluation.histogram_schemas import HistogramRequest
from api.charts.core.styling import draw_histogram

class Histogram(BaseChart):

    request_model = HistogramRequest

    def process(self):
        df = self.get_dataframe()

        # ✅ unified
        self.compute_and_store_statistics(df)

        mode = self.config.mode

        if mode == "single":
            self._single(df)

        elif mode == "stacked":
            self._stacked(df)

        elif mode == "subplots":
            self._subplots(df)

        else:
            raise ValueError(f"Unsupported histogram mode: {mode}")

        return self.finalize(
            add_stats=self.config.show_stats,
            dataset_name="Histogram Data"
        )

    # ----------------------------
    # VARIANTS
    # ----------------------------

    def _single(self, df):
        ax = self.create_figure(layout="single")[0]

        draw_histogram(
            ax,
            df.iloc[:, 0],
            bins=self.config.bins
        )

        ax.set_title(self.config.title)
        ax.set_xlabel(self.config.labelx)
        ax.set_ylabel(self.config.labely)

    def _stacked(self, df):
        ax = self.create_figure(layout="single")[0]

        melted = df.melt(var_name="variable", value_name="value")

        draw_histogram(
            ax,
            melted,
            bins=self.config.bins,
            multiple="stack",
            x="value",
            hue="variable"
        )

        ax.set_title(self.config.title)

    def _subplots(self, df):
        n = len(df.columns)
        cols = 2
        rows = (n + 1) // 2

        axes = self.create_figure(
            layout="multipanel",
            rows=rows,
            cols=cols
        )

        for ax, col in zip(axes, df.columns):
            draw_histogram(
                ax,
                df[col],
                bins=self.config.bins
            )

            ax.set_title(col)
            ax.set_xlabel(self.config.labelx)
            ax.set_ylabel(self.config.labely)





##############################################################################################################################
# # api/charts/evaluation/histogram.py

# import matplotlib.pyplot as plt
# from api.charts.core.styling import style_axis
# from api.charts.constants import COLOR_BLACK, COLOR_PALETTE
# from .base_histogram import BaseHistogram
# from api.charts.statistics import (
#     add_descriptive_stats_table
# )

# class Histogram(BaseHistogram):

#     def process(self):
#         df = self.get_dataframe()

#         # Calculate statistics FIRST
#         #self._compute_statistics(df)
#         self.statistics = self.compute_statistics(df)

#         mode = self.config.mode

#         if mode == "single":
#             self._plot_single(df)

#         elif mode == "stacked":
#             self._plot_stacked(df)

#         elif mode == "subplots":
#             self._plot_subplots(df)

#         else:
#             raise ValueError(f"Unsupported histogram mode: {mode}")

#         # OPTIONAL: draw table
#         if self.config.show_stats:
#             add_descriptive_stats_table(
#                 self.figure,
#                 self.statistics if len(self.statistics) > 1 else list(self.statistics.values())[0],
#                 dataset_name="Histogram Data"
#             )

#         # return self._finalize()
#         return self.finalize(add_stats=self.config.show_stats)

#     # -----------------------------------
#     # Histogram Variants
#     # -----------------------------------

#     def _plot_single(self, df):
#         fig, ax = self._setup_figure()
#         self.figure = fig

#         data = df.iloc[:, 0]

#         ax.hist(
#             data,
#             bins=self.config.bins,
#             color=COLOR_PALETTE[0],
#             edgecolor=COLOR_BLACK,
#             zorder=3
#         )

#         self._apply_title(ax)

#     def _plot_stacked(self, df):
#         fig, ax = self._setup_figure()
#         self.figure = fig

#         data = [df[col].values for col in df.columns]
#         colors = COLOR_PALETTE[:len(data)]

#         ax.hist(
#             data,
#             bins=self.config.bins,
#             stacked=True,
#             histtype="barstacked",
#             edgecolor=COLOR_BLACK,
#             color=colors,
#             label=df.columns.tolist(),
#             zorder=3
#         )

#         ax.legend(loc="best")

#         self._apply_title(ax)

#     def _plot_subplots(self, df):
#         num_cols = 2
#         num_datasets = len(df.columns)
#         num_rows = (num_datasets + 1) // 2

#         fig, axes = plt.subplots(
#             num_rows,
#             num_cols,
#             figsize=(11.69, num_rows * 5),
#             squeeze=False
#         )

#         self.figure = fig

#         for i, col in enumerate(df.columns):
#             row = i // num_cols
#             col_idx = i % num_cols

#             ax = axes[row, col_idx]

#             ax.hist(
#                 df[col],
#                 bins=self.config.bins,
#                 color=COLOR_PALETTE[i],
#                 edgecolor=COLOR_BLACK,
#                 zorder=3
#             )

#             ax.set_title(col)
#             # ax.grid(True)
#             style_axis(ax)

#         # Remove empty subplot if odd
#         if num_datasets % 2 != 0:
#             fig.delaxes(axes[-1, -1])

#         fig.suptitle(self.config.title)