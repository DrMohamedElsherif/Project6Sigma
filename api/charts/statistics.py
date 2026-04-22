# api/charts/statistics.py

import numpy as np
import pandas as pd
from scipy import stats
from api.schemas import BusinessLogicException
from typing import Dict, Any, List, Optional, Union, Tuple
import matplotlib.pyplot as plt
from enum import Enum
from dataclasses import dataclass, field

from api.charts.core.table_builder import TableBuilder
from api.charts.core.table_styling import DEFAULT_TABLE_STYLE

##############################################
class StatsTableType(str, Enum):
    """Types of statistics tables available"""
    DESCRIPTIVE = "descriptive"      # Basic descriptive stats (mean, median, etc.)
    CORRELATION = "correlation"       # Correlation-specific stats
    CAPABILITY = "capability"         # Process capability stats
    HYPOTHESIS = "hypothesis"         # Hypothesis test results
    CONTROL_CHART = "control_chart"   # Control chart statistics
    CUSTOM = "custom"                  # Custom table definition

@dataclass
class StatsMetric:
    """Definition of a single metric in a statistics table"""
    key: str                           # Dictionary key to access value
    label: str                          # Display label in table
    format: str = "{:.2f}"              # Format string for floats
    condition: Optional[callable] = None  # Optional condition to include metric
    depends_on: Optional[List[str]] = None  # Other metrics this depends on
    
class StatisticsCalculator:
    """
    Unified statistics calculator that can generate different types of statistical summaries.
    Follows DRY principle by centralizing common calculations.
    """
    
    # Metric definitions for different table types
    METRIC_DEFINITIONS = {
        StatsTableType.DESCRIPTIVE: [
            StatsMetric("n", "n", "{}"),
            StatsMetric("average", "Average", "{:.2f}"),
            StatsMetric("median", "Median", "{:.2f}"),
            StatsMetric("min", "Min", "{:.2f}"),
            StatsMetric("max", "Max", "{:.2f}"),
            StatsMetric("range", "Range", "{}"),
            StatsMetric("standard_deviation", "Std Dev", "{:.2f}"),
            StatsMetric("ci_95", "95% CI", "{}"),
            StatsMetric("q1", "Q1", "{:.2f}"),
            StatsMetric("q3", "Q3", "{:.2f}"),
            StatsMetric("iqr", "IQR", "{:.2f}"),
        ],
        
        StatsTableType.CORRELATION: [
            StatsMetric("method_used", "Method", "{}"),
            StatsMetric("sample_size", "n", "{}"),
            StatsMetric("coefficient", "Coefficient (r)", "{:.4f}"),
            StatsMetric("correlation_CI", "95% CI", "{}", condition=None),
            StatsMetric("p_value", "p-value", "{:.4f}"),
            StatsMetric("is_significant", "Significant (α=0.05)", "{}"),
            StatsMetric("strength_interpretation", "Interpretation", "{}"),  
            StatsMetric("r_squared", "R²", "{:.4f}", 
                       condition=lambda d: d.get("method_used") == "pearson"),
            StatsMetric("effect_size", "Effect Size", "{:.3f}"),
        ],
        
        StatsTableType.CAPABILITY: [
            StatsMetric("n", "Sample Size", "{}"),
            StatsMetric("mean", "Mean", "{:.2f}"),
            StatsMetric("std_dev", "Std Dev", "{:.2f}"),
            StatsMetric("cp", "Cp", "{:.3f}"),
            StatsMetric("cpk", "Cpk", "{:.3f}"),
            StatsMetric("pp", "Pp", "{:.3f}"),
            StatsMetric("ppk", "Ppk", "{:.3f}"),
            StatsMetric("defect_rate", "Defect Rate", "{:.4f}"),
            StatsMetric("sigma_level", "Sigma Level", "{:.2f}"),
        ],
        
        StatsTableType.HYPOTHESIS: [
            StatsMetric("test_type", "Test Type", "{}"),
            StatsMetric("n", "Sample Size", "{}"),
            StatsMetric("test_statistic", "Test Statistic", "{:.4f}"),
            StatsMetric("p_value", "p-value", "{:.4f}"),
            StatsMetric("alpha", "α Level", "{:.3f}"),
            StatsMetric("is_significant", "Significant", "{}"),
            StatsMetric("effect_size", "Effect Size", "{:.3f}"),
            StatsMetric("power", "Power", "{:.3f}"),
        ],
        
        StatsTableType.CONTROL_CHART: [
            StatsMetric("n", "Subgroups", "{}"),
            StatsMetric("total_points", "Total Points", "{}"),
            StatsMetric("mean", "Mean", "{:.2f}"),
            StatsMetric("ucl", "UCL", "{:.2f}"),
            StatsMetric("lcl", "LCL", "{:.2f}"),
            StatsMetric("center_line", "Center Line", "{:.2f}"),
            StatsMetric("points_outside", "Points Outside", "{}"),
            StatsMetric("violations", "Rules Violations", "{}"),
        ],
    }
    
    @staticmethod
    def calculate_descriptive_stats(data: pd.Series, column_name: str = "") -> Dict[str, Any]:
        """
        Calculate descriptive statistics for a data series.
        """
        try:
            clean_data = data.dropna()
            n = len(clean_data)

            # Validate dataset size
            if n == 0:
                raise BusinessLogicException(
                    error_code="error_validation",
                    field="data",
                    details={"message": "Dataset contains only NaN values or is empty"}
                )
            
            if n == 1:
                raise BusinessLogicException(
                    error_code="error_validation",
                    field="data",
                    details={
                        "message": "At least two valid data points are required to calculate statistics"
                    }
                )
            
            # Compute basic statistics
            average = np.mean(clean_data)
            median = np.median(clean_data)
            minimum = np.min(clean_data)
            maximum = np.max(clean_data)
            std_dev = np.std(clean_data, ddof=1)

            q1 = np.percentile(clean_data, 25)
            q3 = np.percentile(clean_data, 75)
            iqr = q3 - q1

            ci_lower, ci_upper = stats.t.interval(
                confidence=0.95,
                df=n-1,
                loc=average,
                scale=std_dev/np.sqrt(n)
            )

            # Return all metrics in a dictionary
            return {
                "column_name": column_name,
                "n": n,
                "average": float(average),
                "median": float(median),
                "min": float(minimum),
                "max": float(maximum),
                "range": f"{minimum:.2f} - {maximum:.2f}",
                "standard_deviation": float(std_dev),
                "ci_95_lower": float(ci_lower),
                "ci_95_upper": float(ci_upper),
                "ci_95": f"[{ci_lower:.2f}, {ci_upper:.2f}]",
                "q1": float(q1),
                "q3": float(q3),
                "iqr": float(iqr)
            }

        except BusinessLogicException:
            raise
        except ValueError as e:
            raise BusinessLogicException(
                error_code="error_validation",
                field=column_name or "data",
                details={"message": f"Invalid numeric data: {str(e)}"}
            )
        except Exception as e:
            raise BusinessLogicException(
                error_code="error_calculation",
                field="statistics",
                details={"message": f"Unexpected error calculating statistics: {str(e)}"}
            )
    
    @classmethod
    def format_value(cls, value: Any, metric: StatsMetric) -> str:
        """Format a value according to metric definition"""
        if value is None:
            return "-"
        if isinstance(value, float):
            return metric.format.format(value)
        if isinstance(value, bool):
            return "✓ Yes" if value else "✗ No"
        return str(value)
    
    @classmethod
    def prepare_table_data(cls, 
                          stats_dict: Union[Dict[str, Any], Dict[str, Dict[str, Any]]], 
                          table_type: StatsTableType,
                          include_metrics: Optional[List[str]] = None) -> List[List[str]]:
        """
        Prepare data for statistics table based on type.
        
        Args:
            stats_dict: Single stats dict or dict of column_name -> stats dict
            table_type: Type of statistics table
            include_metrics: Optional list of metric keys to include (overrides defaults)
            
        Returns:
            List of [header_row, data_row1, data_row2, ...]
        """
        # Get metrics for this table type
        if include_metrics:
            metrics = [m for m in cls.METRIC_DEFINITIONS[table_type] if m.key in include_metrics]
        else:
            metrics = cls.METRIC_DEFINITIONS[table_type]
        
        # Check if we have multiple columns or single
        is_multi_column = all(isinstance(v, dict) for v in stats_dict.values())
        
        if is_multi_column:
            # Multi-column table
            column_names = list(stats_dict.keys())
            header = ["Metric"] + column_names
            rows = []
            
            for metric in metrics:
                # Check condition
                if metric.condition and not any(metric.condition(stats_dict[col]) for col in column_names):
                    continue
                    
                row = [metric.label]
                for col in column_names:
                    value = stats_dict[col].get(metric.key)
                    row.append(cls.format_value(value, metric))
                rows.append(row)
            
            return [header] + rows
        else:
            # Single column table
            header = ["Metric", "Value"]
            rows = []
            
            for metric in metrics:
                if metric.condition and not metric.condition(stats_dict):
                    continue
                value = stats_dict.get(metric.key)
                rows.append([metric.label, cls.format_value(value, metric)])
            
            return [header] + rows


def add_stats_table(
    figure: plt.Figure,
    stats_data: Union[Dict[str, Any], Dict[str, Dict[str, Any]]],
    table_type: StatsTableType = StatsTableType.DESCRIPTIVE,
    dataset_name: str = "Dataset",
    title: Optional[str] = None,
    position: Optional[Tuple[float, float]] = None,
    fontsize: int = 9,
    col_widths: Optional[List[float]] = None,
    include_metrics: Optional[List[str]] = None,
    color_significant: bool = False,
    significant_key: str = "is_significant",
    auto_position: bool = True
) -> None:
    """
    Unified function to add statistics tables to matplotlib figures.
    
    Args:
        auto_position: If True, automatically positions table below plots.
                      If False, uses manual position parameter.
    """
    
    # Prepare table data (same as before)
    table_data = StatisticsCalculator.prepare_table_data(
        stats_data, table_type, include_metrics
    )
    
    # Build table text (same as before)
    table_lines = []
    if title:
        table_lines.append(f"{title}")
    else:
        table_lines.append(f"Dataset: {dataset_name}")
    
    n_cols = len(table_data[0])
    col_width = 14
    table_lines.append("-" * (col_width * n_cols))
    
    header = table_data[0]
    table_lines.append("  ".join(f"{h:<{col_width-2}}" for h in header))
    table_lines.append("-" * (col_width * n_cols))
    
    for row in table_data[1:]:
        formatted_row = []
        for i, cell in enumerate(row):
            if i == 0:
                formatted_row.append(f"{cell:<{col_width-2}}")
            else:
                formatted_row.append(f"{cell:>{col_width-2}}")
        table_lines.append("  ".join(formatted_row))
    
    # Position the table
    if auto_position and position is None:
        # Auto-position
        x_pos, y_pos = TablePositioner.calculate_table_position(figure)
    elif position is not None:
        # Manual position (backward compatible)
        x_pos, y_pos = position
    else:
        # Default position
        x_pos, y_pos = (0.13, 0.02)
    
    # Render table
    figure.text(
        x_pos,
        y_pos,
        "\n".join(table_lines),
        fontsize=fontsize,
        fontfamily="monospace",
        verticalalignment="bottom",
        transform=figure.transFigure,
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.95, 
                  edgecolor='lightgray')
    )


def add_descriptive_stats_table(
    figure, 
    stats_data, 
    dataset_name="Dataset", 
    table_ax=None, 
    title_top_margin=None,  # Now optional
    style=None,  # Allow custom styling
    **kwargs
):
    """Add statistics table using a dedicated axis - DRY implementation"""
    
    if style is None:
        style = DEFAULT_TABLE_STYLE
    
    if title_top_margin is None:
        title_top_margin = style.title_top_margin
    
    if table_ax is None:
        table_ax = figure.add_axes([0.1, 0.02, 0.8, 0.15])
    
    # Clear and setup axis
    table_ax.clear()
    table_ax.axis('off')
    table_ax.set_frame_on(False)
    
    # Add title
    table_ax.text(
        0.5, title_top_margin,
        f"Statistics: {dataset_name}",
        transform=table_ax.transAxes, ha='center', va='top',
        fontsize=style.title_fontsize, fontweight='bold'
    )
    
    # Build table data (DRY - single method)
    is_multi_column = all(isinstance(v, dict) for v in stats_data.values()) if isinstance(stats_data, dict) else False
    table_data = TableBuilder.build_table_data(stats_data, is_multi_column)
    
    # Create table with appropriate column widths
    if is_multi_column:
        n_cols = len(table_data[0])
        col_widths = [style.multi_col_metric_width] + [(1 - style.multi_col_metric_width) / (n_cols - 1)] * (n_cols - 1)
        cell_loc = 'center'
    else:
        col_widths = [style.single_col_widths['metric'], style.single_col_widths['value']]
        cell_loc = 'left'
    
    table = table_ax.table(
        cellText=table_data,
        loc='center',
        cellLoc=cell_loc,
        colWidths=col_widths
    )
    
    # Apply consistent styling
    TableBuilder.style_table(table, table_data, style)
    
    return table


# def add_correlation_stats_table(figure, stats_data, dataset_name="Correlation Analysis", **kwargs):
#     """Convenience function for correlation statistics"""
#     return add_stats_table(
#         figure, stats_data, StatsTableType.CORRELATION, dataset_name, **kwargs
#     )

import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from typing import Dict, Optional

def add_colored_correlation_table(
    ax: plt.Axes,
    stats_data: Dict[str, any],
    fontsize: int = 10,
    color_strength: bool = True
):
    """
    Compact, professional styled correlation table.

    Improvements:
    - Fixed column widths (prevents excessive stretching)
    - Centered values
    - Compact layout (Power BI style)
    """

    ax.clear()
    ax.axis("off")

    # ---- Prepare data ----
    metrics_def = StatisticsCalculator.METRIC_DEFINITIONS[StatsTableType.CORRELATION]

    table_data = []
    metric_keys = []

    for metric in metrics_def:
        if metric.key == "is_significant":
            continue

        value = stats_data.get(metric.key)
        formatted = StatisticsCalculator.format_value(value, metric)

        table_data.append([metric.label, formatted])
        metric_keys.append(metric.key)

    # ---- Create table (IMPORTANT: control width here) ----
    table = ax.table(
        cellText=table_data,
        colLabels=["Metric", "Value"],
        loc='center',
        cellLoc='center',   # ✅ center everything by default
        colLoc='center',
        colWidths=[0.25, 0.35],              
    )

    table.auto_set_font_size(False)
    table.set_fontsize(fontsize)

    # Compact scaling (less horizontal stretch, more vertical breathing)
    table.scale(0.9, 1.4)


    # ---- Styling ----
    header_color = "#2F5597"
    zebra_light = "#f7f9fc"
    zebra_white = "#ffffff"
    text_color = "#222222"

    for (row, col), cell in table.get_celld().items():

        # HEADER
        if row == 0:
            cell.set_facecolor(header_color)
            cell.set_text_props(color="white", weight="bold", ha="center")
            cell.set_edgecolor(header_color)
            continue

        # ZEBRA STRIPES
        cell.set_facecolor(zebra_light if row % 2 == 0 else zebra_white)

        # CLEAN LOOK (no gridlines)
        cell.set_edgecolor("#ffffff")

        # ALIGNMENT
        if col == 0:
            cell.set_text_props(ha='left', color=text_color)
        else:
            cell.set_text_props(ha='center', color=text_color)  # ✅ centered values

        # PADDING (tight but readable)
        cell.PAD = 0.015

    # ---- Helper ----
    def find_row_index(key_name):
        return metric_keys.index(key_name) + 1 if key_name in metric_keys else None

    # 🎨 Correlation strength coloring
    if color_strength and "coefficient" in stats_data:
        coef = stats_data["coefficient"]
        abs_coef = abs(coef)

        if abs_coef < 0.3:
            color = "#f4cccc"
        elif abs_coef < 0.5:
            color = "#ffe599"
        elif abs_coef < 0.7:
            color = "#d9ead3"
        else:
            color = "#93c47d"

        row_idx = find_row_index("strength_interpretation")
        if row_idx:
            table[(row_idx, 1)].set_facecolor(color)
            table[(row_idx, 1)].set_text_props(weight='bold')

    # 🎯 p-value coloring
    if "p_value" in stats_data:
        p_val = stats_data["p_value"]
        row_idx = find_row_index("p_value")

        if row_idx:
            table[(row_idx, 1)].set_facecolor(
                "#d9ead3" if p_val < 0.05 else "#f4cccc"
            )

    return table