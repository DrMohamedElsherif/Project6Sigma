# # api/charts/evaluation/base_histogram.py

# import pandas as pd
# import matplotlib.pyplot as plt

# from api.schemas import BusinessLogicException
# from api.charts.constants import (
#     COLOR_BLACK,
#     COLOR_PALETTE,
#     TITLE_FONT_SIZE,
#     FIGURE_SIZE_A4_PORTRAIT
# )

# from api.charts.statistics import (
#     StatisticsCalculator,
#     add_descriptive_stats_table
# )

# from .histogram_schemas import HistogramRequest
# from api.charts.core.mixins import StatisticsMixin

# class BaseHistogram(StatisticsMixin):
#     def __init__(self, data: dict):
#         try:
#             validated = HistogramRequest(**data)

#             self.project = validated.project
#             self.step = validated.step
#             self.config = validated.config
#             self.data = validated.data

#             self.figure = None
#             self.statistics = None

#         except ValueError as e:
#             raise BusinessLogicException(
#                 error_code="error_validation",
#                 field=str(e),
#                 details={"message": f"Invalid or missing field: {str(e)}"}
#             )

#     # ----------------------------
#     # Shared helpers
#     # ----------------------------

#     def get_dataframe(self):
#         return pd.DataFrame(self.data.values)

#     def _setup_figure(self):
#         fig, ax = plt.subplots(figsize=FIGURE_SIZE_A4_PORTRAIT)

#         plt.subplots_adjust(top=0.85, bottom=0.3, left=0.15, right=0.85)

#         ax.grid(True, alpha=0.3)

#         ax.set_xlabel(self.config.labelx)
#         ax.set_ylabel(self.config.labely)

#         return fig, ax

#     def _apply_title(self, ax):
#         ax.set_title(self.config.title, fontsize=TITLE_FONT_SIZE, pad=20)

#     # def _finalize(self):
#     #     #plt.close("all")
#     #     plt.close(self.figure)
#     #     return self.figure
#     def finalize(self, add_stats=True):
#         if add_stats and self.statistics:
#             from api.charts.statistics import add_descriptive_stats_table

#             add_descriptive_stats_table(
#                 self.figure,
#                 self.statistics if len(self.statistics) > 1 else list(self.statistics.values())[0],
#                 dataset_name="Histogram Data"
#             )

#         plt.close(self.figure)
#         return self.figure