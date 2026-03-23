# api/charts/statistics.py

import numpy as np
import pandas as pd
from scipy import stats
from api.schemas import BusinessLogicException
from typing import Dict, Any, List, Optional, Union, Tuple
import matplotlib.pyplot as plt
from enum import Enum
from dataclasses import dataclass, field

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
    position: Tuple[float, float] = (0.13, 0.02),
    fontsize: int = 9,
    col_widths: Optional[List[float]] = None,
    include_metrics: Optional[List[str]] = None,
    color_significant: bool = False,
    significant_key: str = "is_significant"
) -> None:
    """
    Unified function to add statistics tables to matplotlib figures.
    
    Args:
        figure: Figure to add table to
        stats_data: Statistics dictionary or dict of column_name -> stats dict
        table_type: Type of statistics table
        dataset_name: Name of the dataset
        title: Optional table title (overrides default)
        position: (x, y) position in figure coordinates
        fontsize: Font size for table
        col_widths: Custom column widths
        include_metrics: Optional list of metric keys to include
        color_significant: Whether to color significant rows
        significant_key: Key to check for significance
    """
    x_pos, y_pos = position
    
    # Prepare table data
    table_data = StatisticsCalculator.prepare_table_data(
        stats_data, table_type, include_metrics
    )
    
    # Build table text
    table_lines = []
    
    # Add title
    if title:
        table_lines.append(f"{title}")
    else:
        table_lines.append(f"Dataset: {dataset_name}")
    
    # Add header separator
    n_cols = len(table_data[0])
    col_width = 14  # Default width
    table_lines.append("-" * (col_width * n_cols))
    
    # Format header
    header = table_data[0]
    table_lines.append("  ".join(f"{h:<{col_width-2}}" for h in header))
    table_lines.append("-" * (col_width * n_cols))
    
    # Add data rows
    for row in table_data[1:]:
        formatted_row = []
        for i, cell in enumerate(row):
            if i == 0:
                formatted_row.append(f"{cell:<{col_width-2}}")
            else:
                formatted_row.append(f"{cell:>{col_width-2}}")
        table_lines.append("  ".join(formatted_row))
    
    # Render table
    figure.text(
        x_pos,
        y_pos,
        "\n".join(table_lines),
        fontsize=fontsize,
        fontfamily="monospace",
        verticalalignment="bottom",
        transform=figure.transFigure,
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.85, 
                  edgecolor='lightgray')
    )

def add_descriptive_stats_table(figure, stats_data, dataset_name="Dataset", **kwargs):
    """Convenience function for descriptive statistics"""
    return add_stats_table(
        figure, stats_data, StatsTableType.DESCRIPTIVE, dataset_name, **kwargs
    )

def add_correlation_stats_table(figure, stats_data, dataset_name="Correlation Analysis", **kwargs):
    """Convenience function for correlation statistics"""
    return add_stats_table(
        figure, stats_data, StatsTableType.CORRELATION, dataset_name, **kwargs
    )





# # api/charts/statistics.py

# import numpy as np
# import pandas as pd
# from scipy import stats
# from api.schemas import BusinessLogicException
# from typing import Dict, Any
# import matplotlib.pyplot as plt


# def calculate_descriptive_stats(data: pd.Series, column_name: str = "") -> Dict[str, Any]:
#     """
#     Berechnet deskriptive Statistiken für eine Datenreihe.
    
#     Args:
#         data: Pandas Series mit numerischen Werten
#         column_name: Name der Spalte für Ausgabe
        
#     Returns:
#         Dictionary mit statistischen Kennzahlen
        
#     Raises:
#         BusinessLogicException: Bei ungültigen Daten
#     """
#     try:
#         clean_data = data.dropna()
#         n = len(clean_data)

#         # Validate dataset size
#         if n == 0:
#             raise BusinessLogicException(
#                 error_code="error_validation",
#                 field="data",
#                 details={"message": "Dataset contains only NaN values or is empty"}
#             )
        
#         if n == 1:
#             raise BusinessLogicException(
#                 error_code="error_validation",
#                 field="data",
#                 details={
#                     "message": "At least two valid data points are required to calculate statistics"
#                 }
#             )
#         # Compute basic statistics       
#         average = np.mean(clean_data)
#         median = np.median(clean_data)
#         minimum = np.min(clean_data)
#         maximum = np.max(clean_data)
#         std_dev = np.std(clean_data, ddof=1)

#         q1 = np.percentile(clean_data, 25)
#         q3 = np.percentile(clean_data, 75)
#         iqr = q3 - q1

#         ci_lower, ci_upper = stats.t.interval(
#             confidence=0.95,
#             df=n-1,
#             loc=average,
#             scale=std_dev/np.sqrt(n)
#         )

#         # Return all metrics in a dictionary
#         return {
#             "column_name": column_name,
#             "n": n,
#             "average": float(average),
#             "median": float(median),
#             "min": float(minimum),
#             "max": float(maximum),
#             "range": f"{minimum:.2f} - {maximum:.2f}",
#             "standard_deviation": float(std_dev),
#             "ci_95_lower": float(ci_lower),
#             "ci_95_upper": float(ci_upper),
#             "ci_95": f"[{ci_lower:.2f}, {ci_upper:.2f}]",
#             "q1": float(q1),
#             "q3": float(q3),
#             "iqr": float(iqr)
#         }

#     except BusinessLogicException:
#         raise
#     except ValueError as e:
#         # Non-numeric or invalid data
#         raise BusinessLogicException(
#             error_code="error_validation",
#             field=column_name or "data",
#             details={"message": f"Invalid numeric data: {str(e)}"}
#         )
#     except Exception as e:
#         # Catch-all for unexpected errors
#         raise BusinessLogicException(
#             error_code="error_calculation",
#             field="statistics",
#             details={"message": f"Unexpected error calculating statistics: {str(e)}"}
#         )
        
# def add_stats_table(
#     figure,
#     stats_data: Dict[str, Any],
#     dataset_name: str = "Dataset",
#     position: tuple = (0.13, 0.02),
#     fontsize: int = 9
# ) -> None:
#     """
#     Adds a statistics table to a Matplotlib figure.

#     The table is column-oriented, with each dataset column displayed side-by-side.
#     Common metrics such as n, average, median, range, std deviation, quartiles, IQR,
#     and 95% confidence interval are included.

#     Args:
#         figure (matplotlib.figure.Figure): Figure to add the table to.
#         stats_data (dict): Dictionary with statistics per column (output of calculate_descriptive_stats).
#         dataset_name (str): Optional name of the dataset for labeling.
#         position (tuple): (x, y) coordinates for the table's lower-left corner in figure coordinates.
#         fontsize (int): Font size for the table text.

#     Returns:
#         None: Modifies the figure in-place.
#     """
#     x_pos, y_pos = position

#     # Define metrics to include in the table
#     metrics = [
#         ("n", "n"),
#         ("average", "Average"),
#         ("median", "Median"),
#         ("range", "Range"),
#         ("standard_deviation", "Std Dev"),
#         ("ci_95", "95% CI"),
#         ("q1", "Q1"),
#         ("q3", "Q3"),
#         ("iqr", "IQR"),
#     ]

#     column_names = list(stats_data.keys())

#     # Build table header and separator lines
#     header = ["Metric"] + column_names
#     table_lines = [
#         f"Dataset: {dataset_name}",
#         "-" * (14 * (len(column_names) + 1)),
#         "  ".join(f"{h:<12}" for h in header),
#         "-" * (14 * (len(column_names) + 1)),
#     ]

#     # Build table rows
#     for key, label in metrics:
#         row = [f"{label:<12}"]
#         for col in column_names:
#             value = stats_data[col].get(key, "")
#             if isinstance(value, float):
#                 row.append(f"{value:<12.2f}")
#             else:
#                 row.append(f"{str(value):<12}")
#         table_lines.append("  ".join(row))

#     # Render the table as text on the figure
#     figure.text(
#         x_pos,
#         y_pos,
#         "\n".join(table_lines),
#         fontsize=fontsize,
#         fontfamily="monospace",
#         verticalalignment="bottom",
#         transform=figure.transFigure,
#         bbox=dict(boxstyle="round", facecolor="white", alpha=0.85)
#     )
    
    

