# api/charts/core/base_chart_compat.py
"""
Backward compatibility layer - NO dependencies on old statistics.py
"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from api.schemas import BusinessLogicException
from api.charts.constants import FIGURE_SIZE_A4_PORTRAIT
from api.charts.core.mixins import StatisticsMixin  # Updated - no old deps
from api.charts.core.table.table_styling import DEFAULT_TABLE_STYLE, TableStyle

# Import new table renderer (not the old one)
from api.charts.core.table.table_renderer import TableRenderer


class BaseChartV2(StatisticsMixin):
    """
    BaseChart implementation with modular architecture.
    NO dependencies on old statistics.py
    """
    
    request_model = None  
    DEFAULT_TABLE_HEIGHT = 0.35
    DEFAULT_TABLE_GAP = 0.09

    def __init__(self, data: dict):
        try:
            validated = self.request_model(**data)
            
            self.project = validated.project
            self.step = validated.step
            self.config = validated.config
            self.data = validated.data
            
            self.figure = None
            self.axes = []
            self.statistics = None
            self._table_ax = None
            self.table_style = DEFAULT_TABLE_STYLE
            
        except Exception as e:
            raise BusinessLogicException(
                error_code="error_validation",
                field=str(e),
                details={"message": str(e)}
            )
    
    def get_dataframe(self):
        return pd.DataFrame(self.data.values)
    
    def compute_and_store_statistics(self, df):
        """Compute and store statistics using new calculator"""
        self.statistics = self.compute_statistics(df)
    
    def create_figure(self, layout="single", rows=1, cols=1, with_table=False, 
                     table_height=None, table_gap=None):
        """Create figure with optional table space"""
        if table_height is None:
            table_height = self.DEFAULT_TABLE_HEIGHT
        if table_gap is None:
            table_gap = self.DEFAULT_TABLE_GAP
            
        self.figure = plt.figure(figsize=FIGURE_SIZE_A4_PORTRAIT)

        if with_table:
            plot_height = 1 - table_height - table_gap
            gs = gridspec.GridSpec(
                2, 1,
                height_ratios=[plot_height, table_height],
                hspace=table_gap,
                top=0.92,
                bottom=0.05
            )
            plot_gs = gs[0]
            self._table_ax = self.figure.add_subplot(gs[1])
        else:
            gs = gridspec.GridSpec(1, 1, top=0.95, bottom=0.08)
            plot_gs = gs[0]
            self._table_ax = None

        if layout == "single":
            self.axes = [self.figure.add_subplot(plot_gs)]
        elif layout == "multipanel":
            sub_gs = plot_gs.subgridspec(rows, cols, hspace=0.4, wspace=0.3)
            self.axes = [
                self.figure.add_subplot(sub_gs[r, c])
                for r in range(rows)
                for c in range(cols)
            ]
        else:
            raise ValueError(f"Unknown layout: {layout}")
        
        return self.axes
    
    def finalize(self, *, add_stats=False, dataset_name="Dataset", 
                title_top_margin=None, style=None):
        """Finalize with table using new TableRenderer"""
        if add_stats and self.statistics and self._table_ax is not None:
            stats_data = (
                self.statistics if len(self.statistics) > 1 
                else list(self.statistics.values())[0]
            )
            
            final_style = style or self.table_style
            
            # Use NEW TableRenderer (not old add_descriptive_stats_table)
            TableRenderer.render_table(
                self.figure,
                stats_data,
                self._table_ax,
                dataset_name=dataset_name,
                style=final_style,
                title_top_margin=title_top_margin
            )
        
        return self.figure




# # ============================================
# # STEP 3: Create compatibility wrapper for old BaseChart
# # ============================================

# # api/charts/core/base_chart_compat.py
# """
# Backward compatibility layer for existing charts.
# This allows gradual migration without breaking existing code.
# """
# import pandas as pd
# import matplotlib.pyplot as plt
# import matplotlib.gridspec as gridspec

# from api.schemas import BusinessLogicException
# from api.charts.constants import FIGURE_SIZE_A4_PORTRAIT
# from api.charts.core.mixins import StatisticsMixin
# from api.charts.core.table.table_renderer import TableRenderer
# from api.charts.core.table_styling import DEFAULT_TABLE_STYLE, TableStyle
# from api.charts.core.layout.presets import LayoutPresets
# from api.charts.core.layout.layout_manager import LayoutManager
# from api.charts.core.layout.layout_regions import RegionType
# from api.charts.core.statistics.statistics_provider import DescriptiveStatisticsProvider

# # Import old functions for backward compatibility
# #from api.charts.statistics import add_descriptive_stats_table


# class BaseChartV2(StatisticsMixin):
#     """
#     New BaseChart implementation with modular architecture.
#     Backward compatible with existing chart implementations.
#     """
    
#     request_model = None  
#     DEFAULT_TABLE_HEIGHT = 0.35
#     DEFAULT_TABLE_GAP = 0.09
    
#     # Flag to enable new architecture (can be set per chart)
#     use_new_architecture = False

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
#             self._table_ax = None
#             self.table_style = DEFAULT_TABLE_STYLE
            
#             # New architecture components
#             self._layout = None
#             self._axes_map = None
#             self._statistics_provider = DescriptiveStatisticsProvider()
            
#         except Exception as e:
#             raise BusinessLogicException(
#                 error_code="error_validation",
#                 field=str(e),
#                 details={"message": str(e)}
#             )
    
#     def get_dataframe(self):
#         return pd.DataFrame(self.data.values)
    
#     def compute_and_store_statistics(self, df):
#         """Legacy method - maintained for compatibility"""
#         if self.use_new_architecture:
#             self.statistics = self._statistics_provider.compute(df)
#         else:
#             self.statistics = self.compute_statistics(df)
    
#     def create_figure_legacy(self, layout="single", rows=1, cols=1, with_table=False, 
#                             table_height=None, table_gap=None):
#         """
#         Original create_figure implementation (kept for backward compatibility)
#         """
#         if table_height is None:
#             table_height = self.DEFAULT_TABLE_HEIGHT
#         if table_gap is None:
#             table_gap = self.DEFAULT_TABLE_GAP
            
#         self.figure = plt.figure(figsize=FIGURE_SIZE_A4_PORTRAIT)

#         if with_table:
#             plot_height = 1 - table_height - table_gap
#             gs = gridspec.GridSpec(
#                 2, 1,
#                 height_ratios=[plot_height, table_height],
#                 hspace=table_gap,
#                 top=0.92,
#                 bottom=0.05
#             )
#             plot_gs = gs[0]
#             self._table_ax = self.figure.add_subplot(gs[1])
#         else:
#             gs = gridspec.GridSpec(1, 1, top=0.95, bottom=0.08)
#             plot_gs = gs[0]
#             self._table_ax = None

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
    
#     def create_figure(self, layout="single", rows=1, cols=1, with_table=False, 
#                      table_height=None, table_gap=None):
#         """
#         Unified create_figure that can use either legacy or new architecture.
#         """
#         if not self.use_new_architecture:
#             return self.create_figure_legacy(layout, rows, cols, with_table, table_height, table_gap)
        
#         # New architecture implementation
#         if table_height is None:
#             table_height = self.DEFAULT_TABLE_HEIGHT
#         if table_gap is None:
#             table_gap = self.DEFAULT_TABLE_GAP
        
#         # Build layout based on parameters
#         if with_table:
#             if layout == "single":
#                 self._layout = LayoutPresets.single_plot_with_table(table_height, table_gap)
#             else:  # multipanel
#                 self._layout = LayoutPresets.multipanel_with_table(rows, cols, table_height, table_gap)
#         else:
#             if layout == "single":
#                 self._layout = LayoutPresets.single_plot_no_table()
#             else:
#                 self._layout = LayoutPresets.multipanel_no_table(rows, cols)
        
#         # Create figure using LayoutManager
#         self.figure, self._axes_map = LayoutManager.create_figure(
#             self._layout, FIGURE_SIZE_A4_PORTRAIT
#         )
        
#         # Extract axes for backward compatibility
#         plot_axes = self._axes_map.get(RegionType.PLOT, [])
#         table_axes = self._axes_map.get(RegionType.TABLE, [])
        
#         if plot_axes:
#             if layout == "single":
#                 self.axes = plot_axes
#             else:  # multipanel - need to create subgridspec structure
#                 # Handle multipanel layout within the plot region
#                 rows = self._layout.metadata.get("grid_rows", rows)
#                 cols = self._layout.metadata.get("grid_cols", cols)
                
#                 # Use the first plot axis and create subgridspec within it
#                 plot_ax = plot_axes[0]
#                 plot_ax.remove()  # Remove the placeholder
#                 sub_gs = gridspec.GridSpec(rows, cols, figure=self.figure, 
#                                           hspace=0.4, wspace=0.3)
#                 self.axes = [
#                     self.figure.add_subplot(sub_gs[r, c])
#                     for r in range(rows)
#                     for c in range(cols)
#                 ]
        
#         if table_axes:
#             self._table_ax = table_axes[0]
#         else:
#             self._table_ax = None
        
#         return self.axes
    
#     def finalize(self, *, add_stats=False, dataset_name="Dataset", 
#                 title_top_margin=None, style=None):
#         """
#         Finalize with table - works with both legacy and new architecture.
#         """
#         if add_stats and self.statistics and self._table_ax is not None:
#             stats_data = (
#                 self.statistics if len(self.statistics) > 1 
#                 else list(self.statistics.values())[0]
#             )
            
#             final_style = style or self.table_style
            
#             if self.use_new_architecture:
#                 # Use new TableRenderer
#                 TableRenderer.render_table(
#                     self.figure,
#                     stats_data,
#                     self._table_ax,
#                     dataset_name=dataset_name,
#                     style=final_style,
#                     title_top_margin=title_top_margin
#                 )
#             else:
#                 # Use legacy function
#                 add_descriptive_stats_table(
#                     self.figure,
#                     stats_data,
#                     dataset_name=dataset_name,
#                     table_ax=self._table_ax,
#                     title_top_margin=title_top_margin,
#                     style=final_style
#                 )
        
#         return self.figure


# # ============================================
# # STEP 4: Create updated BaseChart that defaults to new architecture
# # ============================================

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