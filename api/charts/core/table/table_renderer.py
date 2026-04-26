# api/charts/core/table/table_renderer.py
"""
Table renderer - NO dependencies on old statistics.py
"""
import matplotlib.pyplot as plt
from typing import Optional, List, Union, Dict, Any

# Import from new modules only
from api.charts.core.table.table_builder import TableBuilder
from api.charts.core.table.table_styling import TableStyle, DEFAULT_TABLE_STYLE


class TableRenderer:
    """Handles rendering of statistics tables to matplotlib figures"""
    
    @staticmethod
    def render_table(
        fig: plt.Figure,
        stats_data: Union[Dict[str, Any], Dict[str, Dict[str, Any]]],
        table_ax: plt.Axes,
        dataset_name: str = "Dataset",
        style: Optional[TableStyle] = None,
        title_top_margin: Optional[float] = None
    ) -> plt.Axes:
        """Render a statistics table to a dedicated axis"""
        if style is None:
            style = DEFAULT_TABLE_STYLE
        
        if title_top_margin is None:
            title_top_margin = style.title_top_margin
        
        # Clear and setup axis
        table_ax.clear()
        table_ax.axis('off')
        table_ax.set_frame_on(False)
        
        # Add title
        table_ax.text(
            0.5, title_top_margin,
            f"Statistics: {dataset_name}",
            transform=table_ax.transAxes,
            ha='center',
            va='top',
            fontsize=style.title_fontsize,
            fontweight='bold'
        )
        
        # Build table data (using existing TableBuilder)
        is_multi_column = all(isinstance(v, dict) for v in stats_data.values()) if isinstance(stats_data, dict) else False
        table_data = TableBuilder.build_table_data(stats_data, is_multi_column)
        
        # Determine column widths
        if is_multi_column:
            n_cols = len(table_data[0])
            col_widths = [style.multi_col_metric_width] + [(1 - style.multi_col_metric_width) / (n_cols - 1)] * (n_cols - 1)
            cell_loc = 'center'
        else:
            col_widths = [style.single_col_widths['metric'], style.single_col_widths['value']]
            cell_loc = 'left'
        
        # Create table
        table = table_ax.table(
            cellText=table_data,
            loc='center',
            cellLoc=cell_loc,
            colWidths=col_widths
        )
        
        # Apply styling
        TableBuilder.style_table(table, table_data, style)
        
        return table_ax



# # api/charts/core/table/table_renderer.py
# import matplotlib.pyplot as plt
# from typing import Optional, List, Union, Dict, Any
# from api.charts.core.table_builder import TableBuilder
# from api.charts.core.table_styling import TableStyle, DEFAULT_TABLE_STYLE

# class TableRenderer:
#     """Handles rendering of statistics tables to matplotlib figures"""
    
#     @staticmethod
#     def render_table(
#         fig: plt.Figure,
#         stats_data: Union[Dict[str, Any], Dict[str, Dict[str, Any]]],
#         table_ax: plt.Axes,
#         dataset_name: str = "Dataset",
#         style: Optional[TableStyle] = None,
#         title_top_margin: Optional[float] = None
#     ) -> plt.Axes:
#         """
#         Render a statistics table to a dedicated axis.
#         This is compatible with the existing add_descriptive_stats_table function.
#         """
#         if style is None:
#             style = DEFAULT_TABLE_STYLE
        
#         if title_top_margin is None:
#             title_top_margin = style.title_top_margin
        
#         # Clear and setup axis
#         table_ax.clear()
#         table_ax.axis('off')
#         table_ax.set_frame_on(False)
        
#         # Add title
#         table_ax.text(
#             0.5, title_top_margin,
#             f"Statistics: {dataset_name}",
#             transform=table_ax.transAxes,
#             ha='center',
#             va='top',
#             fontsize=style.title_fontsize,
#             fontweight='bold'
#         )
        
#         # Build table data (using existing TableBuilder)
#         is_multi_column = all(isinstance(v, dict) for v in stats_data.values()) if isinstance(stats_data, dict) else False
#         table_data = TableBuilder.build_table_data(stats_data, is_multi_column)
        
#         # Determine column widths
#         if is_multi_column:
#             n_cols = len(table_data[0])
#             col_widths = [style.multi_col_metric_width] + [(1 - style.multi_col_metric_width) / (n_cols - 1)] * (n_cols - 1)
#             cell_loc = 'center'
#         else:
#             col_widths = [style.single_col_widths['metric'], style.single_col_widths['value']]
#             cell_loc = 'left'
        
#         # Create table
#         table = table_ax.table(
#             cellText=table_data,
#             loc='center',
#             cellLoc=cell_loc,
#             colWidths=col_widths
#         )
        
#         # Apply styling
#         TableBuilder.style_table(table, table_data, style)
        
#         return table_ax