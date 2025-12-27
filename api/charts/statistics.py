# statistics.py

import numpy as np
import pandas as pd
from scipy import stats
from api.schemas import BusinessLogicException
from typing import Dict, Any
import matplotlib.pyplot as plt


def calculate_descriptive_stats(data: pd.Series, column_name: str = "") -> Dict[str, Any]:
    """
    Berechnet deskriptive Statistiken für eine Datenreihe.
    
    Args:
        data: Pandas Series mit numerischen Werten
        column_name: Name der Spalte für Ausgabe
        
    Returns:
        Dictionary mit statistischen Kennzahlen
        
    Raises:
        BusinessLogicException: Bei ungültigen Daten
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
        # Non-numeric or invalid data
        raise BusinessLogicException(
            error_code="error_validation",
            field=column_name or "data",
            details={"message": f"Invalid numeric data: {str(e)}"}
        )
    except Exception as e:
        # Catch-all for unexpected errors
        raise BusinessLogicException(
            error_code="error_calculation",
            field="statistics",
            details={"message": f"Unexpected error calculating statistics: {str(e)}"}
        )
        
def add_stats_table(
    figure,
    stats_data: Dict[str, Any],
    dataset_name: str = "Dataset",
    position: tuple = (0.13, 0.02),
    fontsize: int = 9
) -> None:
    """
    Adds a statistics table to a Matplotlib figure.

    The table is column-oriented, with each dataset column displayed side-by-side.
    Common metrics such as n, average, median, range, std deviation, quartiles, IQR,
    and 95% confidence interval are included.

    Args:
        figure (matplotlib.figure.Figure): Figure to add the table to.
        stats_data (dict): Dictionary with statistics per column (output of calculate_descriptive_stats).
        dataset_name (str): Optional name of the dataset for labeling.
        position (tuple): (x, y) coordinates for the table's lower-left corner in figure coordinates.
        fontsize (int): Font size for the table text.

    Returns:
        None: Modifies the figure in-place.
    """
    x_pos, y_pos = position

    # Define metrics to include in the table
    metrics = [
        ("n", "n"),
        ("average", "Average"),
        ("median", "Median"),
        ("range", "Range"),
        ("standard_deviation", "Std Dev"),
        ("ci_95", "95% CI"),
        ("q1", "Q1"),
        ("q3", "Q3"),
        ("iqr", "IQR"),
    ]

    column_names = list(stats_data.keys())

    # Build table header and separator lines
    header = ["Metric"] + column_names
    table_lines = [
        f"Dataset: {dataset_name}",
        "-" * (14 * (len(column_names) + 1)),
        "  ".join(f"{h:<12}" for h in header),
        "-" * (14 * (len(column_names) + 1)),
    ]

    # Build table rows
    for key, label in metrics:
        row = [f"{label:<12}"]
        for col in column_names:
            value = stats_data[col].get(key, "")
            if isinstance(value, float):
                row.append(f"{value:<12.2f}")
            else:
                row.append(f"{str(value):<12}")
        table_lines.append("  ".join(row))

    # Render the table as text on the figure
    figure.text(
        x_pos,
        y_pos,
        "\n".join(table_lines),
        fontsize=fontsize,
        fontfamily="monospace",
        verticalalignment="bottom",
        transform=figure.transFigure,
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.85)
    )
    
    

