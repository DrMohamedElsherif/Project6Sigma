# api/charts/core/table/table_builder.py
"""
Table builder - handles tuple values from new calculators
"""
from typing import Dict, Any, List, Union
import matplotlib.pyplot as plt
from api.charts.core.table.table_styling import DEFAULT_TABLE_STYLE, TableStyle


class TableBuilder:
    """Builder class for creating styled statistics tables"""
    
    # Define all available metrics once (updated keys)
    METRICS = [
        ('n', 'Sample Size (n)', '{}'),
        ('average', 'Mean', '{:.2f}'),
        ('median', 'Median', '{:.2f}'),
        ('min', 'Minimum', '{:.2f}'),
        ('max', 'Maximum', '{:.2f}'),
        ('range', 'Range', '{}'),
        ('standard_deviation', 'Std Dev', '{:.2f}'),
        ('ci_95', '95% CI', '{}'),
        ('q1', 'Q1 (25th percentile)', '{:.2f}'),
        ('q3', 'Q3 (75th percentile)', '{:.2f}'),
        ('iqr', 'IQR', '{:.2f}')
    ]
    
    @classmethod
    def _format_value(cls, value: Any, format_str: str) -> str:
        """Format a value for display, handling tuples and None"""
        if value is None:
            return '-'
        
        # Handle range tuple
        if isinstance(value, tuple) and len(value) == 2:
            if format_str == '{}':
                return f"{value[0]:.2f} - {value[1]:.2f}"
            else:
                return f"{format_str.format(value[0])} - {format_str.format(value[1])}"
        
        # Handle regular values
        if isinstance(value, (int, float)):
            if format_str == '{}':
                return str(int(value) if isinstance(value, float) and value.is_integer() else value)
            return format_str.format(value)
        
        return str(value)
    
    @classmethod
    def build_table_data(cls, stats_data: Union[Dict, Dict[str, Dict]], is_multi_column: bool = None) -> List[List]:
        """Build table data from statistics"""
        if is_multi_column is None:
            is_multi_column = all(isinstance(v, dict) for v in stats_data.values()) if isinstance(stats_data, dict) else False
        
        if is_multi_column:
            return cls._build_multi_column_table(stats_data)
        else:
            return cls._build_single_column_table(stats_data)
    
    @classmethod
    def _build_single_column_table(cls, stats_dict: Dict) -> List[List]:
        """Build single column table"""
        rows = [["Metric", "Value"]]
        
        for metric_key, metric_label, format_str in cls.METRICS:
            value = stats_dict.get(metric_key)
            formatted_value = cls._format_value(value, format_str)
            rows.append([metric_label, formatted_value])
        
        return rows
    
    @classmethod
    def _build_multi_column_table(cls, stats_data: Dict[str, Dict]) -> List[List]:
        """Build multi-column table"""
        column_names = list(stats_data.keys())
        rows = [["Metric"] + column_names]
        
        for metric_key, metric_label, format_str in cls.METRICS:
            row = [metric_label]
            for col in column_names:
                value = stats_data[col].get(metric_key)
                formatted_value = cls._format_value(value, format_str)
                row.append(formatted_value)
            rows.append(row)
        
        return rows
    
    @classmethod
    def style_table(cls, table, table_data: List[List], style: TableStyle = None):
        """Apply consistent styling to table"""
        if style is None:
            style = DEFAULT_TABLE_STYLE

        n_rows = len(table_data)
        n_cols = len(table_data[0])

        table.auto_set_font_size(False)
        table.set_fontsize(style.data_fontsize)
        table.scale(style.scale_x, style.scale_y)

        # Remove ALL borders first
        for (i, j), cell in table.get_celld().items():
            cell.set_linewidth(0)
            cell.visible_edges = ""

        # Header styling + bottom border
        for j in range(n_cols):
            cell = table[(0, j)]
            cell.set_facecolor(style.header_color)
            cell.set_text_props(
                weight='bold',
                color=style.header_text_color,
                fontsize=style.header_fontsize
            )
            cell.visible_edges = "B"
            cell.set_linewidth(style.border_width * 3)

        # Data rows
        for i in range(1, n_rows):
            bg_color = style.row_even_color if i % 2 == 0 else style.row_odd_color
            
            for j in range(n_cols):
                cell = table[(i, j)]
                cell.set_facecolor(bg_color)
                
                if j == 0:
                    cell.set_text_props(weight='bold')

        # Bottom border of entire table
        last_row = n_rows - 1
        for j in range(n_cols):
            cell = table[(last_row, j)]
            cell.visible_edges = "B"
            cell.set_linewidth(style.border_width * 3)

        return table

# # api/charts/core/table_builder.py

# from typing import Dict, Any, List, Union
# import matplotlib.pyplot as plt
# from api.charts.core.table_styling import DEFAULT_TABLE_STYLE, TableStyle


# class TableBuilder:
#     """Builder class for creating styled statistics tables"""
    
#     # Define all available metrics once
#     METRICS = [
#         ('n', 'Sample Size (n)', '{}'),
#         ('average', 'Mean', '{:.2f}'),
#         ('median', 'Median', '{:.2f}'),
#         ('min', 'Minimum', '{:.2f}'),
#         ('max', 'Maximum', '{:.2f}'),
#         ('range', 'Range', '{}'),
#         ('standard_deviation', 'Std Dev', '{:.2f}'),
#         ('ci_95', '95% CI', '{}'),
#         ('q1', 'Q1 (25th percentile)', '{:.2f}'),
#         ('q3', 'Q3 (75th percentile)', '{:.2f}'),
#         ('iqr', 'IQR', '{:.2f}')
#     ]
    
#     @classmethod
#     def build_table_data(cls, stats_data: Union[Dict, Dict[str, Dict]], is_multi_column: bool = None) -> List[List]:
#         """Build table data from statistics"""
#         if is_multi_column is None:
#             is_multi_column = all(isinstance(v, dict) for v in stats_data.values()) if isinstance(stats_data, dict) else False
        
#         if is_multi_column:
#             return cls._build_multi_column_table(stats_data)
#         else:
#             return cls._build_single_column_table(stats_data)
    
#     @classmethod
#     def _build_single_column_table(cls, stats_dict: Dict) -> List[List]:
#         """Build single column table"""
#         return [
#             ["Metric", "Value"],
#             ["Sample Size (n)", str(stats_dict.get('n', '-'))],
#             ["Mean", f"{stats_dict.get('average', 0):.2f}"],
#             ["Median", f"{stats_dict.get('median', 0):.2f}"],
#             ["Minimum", f"{stats_dict.get('min', 0):.2f}"],
#             ["Maximum", f"{stats_dict.get('max', 0):.2f}"],
#             ["Range", stats_dict.get('range', '-')],
#             ["Std Deviation", f"{stats_dict.get('standard_deviation', 0):.2f}"],
#             ["95% CI", stats_dict.get('ci_95', '-')],
#             ["Q1 (25th percentile)", f"{stats_dict.get('q1', 0):.2f}"],
#             ["Q3 (75th percentile)", f"{stats_dict.get('q3', 0):.2f}"],
#             ["IQR", f"{stats_dict.get('iqr', 0):.2f}"],
#         ]
    
#     @classmethod
#     def _build_multi_column_table(cls, stats_data: Dict[str, Dict]) -> List[List]:
#         """Build multi-column table"""
#         column_names = list(stats_data.keys())
#         headers = ["Metric"] + column_names
#         table_data = [headers]
        
#         for metric_key, metric_label, format_str in cls.METRICS:
#             row = [metric_label]
#             for col in column_names:
#                 value = stats_data[col].get(metric_key, '-')
#                 if isinstance(value, (int, float)) and value != '-':
#                     row.append(format_str.format(value) if format_str != '{}' else str(value))
#                 else:
#                     row.append(str(value))
#             table_data.append(row)
        
#         return table_data
    
#     @classmethod
#     def style_table(cls, table, table_data: List[List], style: TableStyle = None):
#         if style is None:
#             style = DEFAULT_TABLE_STYLE

#         n_rows = len(table_data)
#         n_cols = len(table_data[0])

#         table.auto_set_font_size(False)
#         table.set_fontsize(style.data_fontsize)
#         table.scale(style.scale_x, style.scale_y)

#         # ---- Remove ALL borders first ----
#         for (i, j), cell in table.get_celld().items():
#             cell.set_linewidth(0)
#             cell.visible_edges = ""  # no edges at all

#         # ---- Header styling + bottom border ----
#         for j in range(n_cols):
#             cell = table[(0, j)]

#             cell.set_facecolor(style.header_color)
#             cell.set_text_props(
#                 weight='bold',
#                 color=style.header_text_color,
#                 fontsize=style.header_fontsize
#             )

#             # ONLY bottom border
#             cell.visible_edges = "B"
#             cell.set_linewidth(style.border_width * 3)

#         # ---- Data rows ----
#         for i in range(1, n_rows):
#             bg_color = style.row_even_color if i % 2 == 0 else style.row_odd_color

#             for j in range(n_cols):
#                 cell = table[(i, j)]
#                 cell.set_facecolor(bg_color)

#                 if j == 0:
#                     cell.set_text_props(weight='bold')

#         # ---- Bottom border of entire table ----
#         last_row = n_rows - 1
#         for j in range(n_cols):
#             cell = table[(last_row, j)]

#             # ONLY bottom border
#             cell.visible_edges = "B"
#             cell.set_linewidth(style.border_width * 3)

#         return table