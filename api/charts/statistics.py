# statistics.py 

"""Helper functions for statistical calculations"""
import numpy as np
import pandas as pd
from scipy import stats
from api.schemas import BusinessLogicException
import matplotlib.pyplot as plt
from typing import Dict, Any


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

        if n == 0:
            raise BusinessLogicException(
                error_code="error_validation",
                field="data",
                details={"message": "Dataset contains only NaN values or is empty"}
            )

        if n == 1:
            single_value = float(clean_data.iloc[0])
            return {
                "column_name": column_name,
                "n": 1,
                "average": single_value,
                "median": single_value,
                "min": single_value,
                "max": single_value,
                "range": f"{single_value:.2f} - {single_value:.2f}",
                "standard_deviation": 0.0,
                "ci_95_lower": single_value,
                "ci_95_upper": single_value,
                "ci_95": f"[{single_value:.2f}, {single_value:.2f}]",
                "q1": single_value,
                "q3": single_value,
                "iqr": 0.0
            }

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


def add_stats_table(figure, stats_data: Dict[str, Any], 
                    position: tuple = (0.15, 0.02), 
                    fontsize: int = 10) -> None:
    """
    Fügt Statistik-Textblock unter/über einem Matplotlib-Figure hinzu.

    Args:
        figure: Matplotlib figure object
        stats_data: Dictionary von calculate_descriptive_stats()
        position: (x, y) tuple, figure-relative position des Textes
        fontsize: Font size
    """
    column_name = stats_data.get("column_name", "Dataset")
    n = stats_data.get("n", 0)
    average = stats_data.get("average", 0.0)
    median = stats_data.get("median", 0.0)
    range_str = stats_data.get("range", "0.00 - 0.00")
    std_dev = stats_data.get("standard_deviation", 0.0)
    ci_str = stats_data.get("ci_95", "[0.00, 0.00]")

    separator = "─" * 40
    stats_text = (
        f"Dataset: {column_name}\n"
        f"{separator}\n"
        f"n : {n}\n"
        f"Average : {average:.2f}\n"
        f"Median : {median:.2f}\n"
        f"Range : {range_str}\n"
        f"Standard dev. : {std_dev:.2f}\n"
        f"95% CI : {ci_str}"
    )

    x_position, y_position = position
    figure.text(
        x_position,
        y_position,
        stats_text,
        fontsize=fontsize,
        fontfamily='monospace',
        verticalalignment='bottom',
        transform=figure.transFigure,
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8)
    )

