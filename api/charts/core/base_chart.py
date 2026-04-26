
# # api/charts/core/base_chart.py
# """
# BaseChart - NO dependencies on old code
# """
# from api.charts.core.base_chart_compat import BaseChartV2

# # Direct export - no compatibility layer needed
# BaseChart = BaseChartV2


# # api/charts/core/base_chart.py (REPLACE with this)
# """
# BaseChart with modular architecture - fully backward compatible.
# Set use_new_architecture=True to opt-in to new features.
# """
# from api.charts.core.base_chart_compat import BaseChartV2

# # For backward compatibility, BaseChart is now BaseChartV2
# # Existing charts will continue to work
# class BaseChart(BaseChartV2):
#     """
#     Base chart class with modular architecture.
    
#     To use new features, set:
#         self.use_new_architecture = True
    
#     All existing charts work without changes.
#     """
#     pass



# # api/charts/core/base_chart.py

# import pandas as pd
# import matplotlib.pyplot as plt
# import matplotlib.gridspec as gridspec

# from api.schemas import BusinessLogicException
# from api.charts.constants import FIGURE_SIZE_A4_PORTRAIT
# from api.charts.core.mixins import StatisticsMixin
# from api.charts.statistics import add_descriptive_stats_table
# from api.charts.core.table_styling import DEFAULT_TABLE_STYLE, TableStyle



# class BaseChart(StatisticsMixin):
#     request_model = None  
    
#     # Class-level defaults for table styling
#     DEFAULT_TABLE_HEIGHT = 0.35  # 35% for table
#     DEFAULT_TABLE_GAP = 0.09     # 9% gap between plot and table

#     def __init__(self, data: dict):
#         try:
#             validated = self.request_model(**data)

#             self.project = validated.project
#             self.step = validated.step
#             self.config = validated.config
#             self.data = validated.data

#             self.figure = None
#             self.axes = []
#             self.statistics = None
#             self._table_ax = None  # Initialize table axis
            

#         except Exception as e:
#             raise BusinessLogicException(
#                 error_code="error_validation",
#                 field=str(e),
#                 details={"message": str(e)}
#             )

#     # ----------------------------
#     # DATA
#     # ----------------------------

#     def get_dataframe(self):
#         return pd.DataFrame(self.data.values)

#     # ----------------------------
#     # STATISTICS
#     # ----------------------------

#     def compute_and_store_statistics(self, df):
#         self.statistics = self.compute_statistics(df)

#     # ----------------------------
#     # FIGURE FACTORY (UNIFIED)
#     # ----------------------------

#     def create_figure(
#     self,
#     *,
#     layout="single",
#     rows=1,
#     cols=1,
#     with_table=False,
#     table_height=None,  # Proportion for table
#     table_gap=None      # Gap between plot and table (in figure coordinates)
#     ):
#         """
#         Create figure with optional table space.
        
#         Args:
#             table_height: Proportion (0-1) of figure height for table
#                         Recommended: 0.30-0.40 for descriptive stats
#             table_gap: Gap between plot and table (0.02 to 0.10 recommended)
#                     0.05 = 5% of figure height as gap
#         """
#         # Use defaults if not specified
#         if table_height is None:
#             table_height = self.DEFAULT_TABLE_HEIGHT
#         if table_gap is None:
#             table_gap = self.DEFAULT_TABLE_GAP
            
#         self.figure = plt.figure(figsize=FIGURE_SIZE_A4_PORTRAIT)

#         if with_table:
#             # Calculate plot height (1 - table_height - table_gap)
#             plot_height = 1 - table_height - table_gap
            
#             # Create GridSpec with plot above, gap, and table below
#             gs = gridspec.GridSpec(
#                 2, 1,
#                 height_ratios=[plot_height, table_height],
#                 hspace=table_gap,  # ← Gap between subplots
#                 top=0.92,
#                 bottom=0.05
#             )

#             plot_gs = gs[0]
#             self._table_ax = self.figure.add_subplot(gs[1])
#         else:
#             gs = gridspec.GridSpec(1, 1, top=0.95, bottom=0.08)
#             plot_gs = gs[0]
#             self._table_ax = None

#         # ---- Layout handling ----
#         if layout == "single":
#             self.axes = [self.figure.add_subplot(plot_gs)]
#         elif layout == "multipanel":
#             sub_gs = plot_gs.subgridspec(rows, cols, hspace=0.4, wspace=0.3)
#             self.axes = [
#                 self.figure.add_subplot(sub_gs[r, c])
#                 for r in range(rows)
#                 for c in range(cols)
#             ]
#         else:
#             raise ValueError(f"Unknown layout: {layout}")

#         return self.axes
#     # ----------------------------
#     # FINALIZATION
#     # ----------------------------
    
#     # Allow custom styling per chart type
#     table_style: TableStyle = DEFAULT_TABLE_STYLE

#     def finalize(self, *, add_stats=False, dataset_name="Dataset", title_top_margin=None, style=None):
#             """Finalize with optional custom styling"""
#             if add_stats and self.statistics and self._table_ax is not None:
#                 stats_data = (
#                     self.statistics if len(self.statistics) > 1 
#                     else list(self.statistics.values())[0]
#                 )
                
#                 # Use instance style or passed style
#                 final_style = style or self.table_style
                
#                 add_descriptive_stats_table(
#                     self.figure,
#                     stats_data,
#                     dataset_name=dataset_name,
#                     table_ax=self._table_ax,
#                     title_top_margin=title_top_margin,
#                     style=final_style
#                 )
            
#             return self.figure



