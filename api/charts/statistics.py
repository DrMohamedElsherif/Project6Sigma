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

def add_stats_table(
    figure,
    stats_data: Dict[str, Any],
    dataset_name: str = "Dataset",
    position: tuple = (0.13, 0.01), 
    fontsize: int = 10
) -> None:
    """
    Fügt Statistik-Textblock unter/über einem Matplotlib-Figure hinzu.

    Args:
        figure: Matplotlib figure object
        stats_data: Dictionary von calculate_descriptive_stats()
        position: (x, y) tuple, figure-relative position des Textes
        fontsize: Font size
    """
    x_pos, y_pos = position
    text_lines = [f"Dataset: {dataset_name}", "-" * 50]

    # Loop through columns
    for col_name, col_stats in stats_data.items():
        text_lines.append(f"\nColumn: {col_name}")
        text_lines.append(f"n : {col_stats['n']}")
        text_lines.append(f"Average : {col_stats['average']:.2f}")
        text_lines.append(f"Median : {col_stats['median']:.2f}")
        text_lines.append(f"Range : {col_stats['range']}")
        text_lines.append(f"Std Dev : {col_stats['standard_deviation']:.2f}")
        text_lines.append(f"95% CI : {col_stats['ci_95']}")

    figure.text(
        x_pos,
        y_pos,
        "\n".join(text_lines),
        fontsize=fontsize,
        fontfamily='monospace',
        verticalalignment='bottom',
        transform=figure.transFigure,
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8)
    )

