# api/correlation/utils.py

import numpy as np
from scipy import stats
from typing import Tuple, Dict, Any, Optional
import matplotlib.pyplot as plt
import pandas as pd
from api.correlation.schemas import CorrelationMethod, CorrelationResult


def check_normality(data: np.ndarray, alpha: float = 0.05) -> bool:
    """
    Check if data is normally distributed using Shapiro-Wilk test.
    SS
    Args:
        data: Input array
        alpha: Significance level
        
    Returns:
        True if data appears normally distributed
    """
    if len(data) < 3 or len(data) > 5000:  # Shapiro-Wilk limitations
        return False
    
    statistic, p_value = stats.shapiro(data)
    return bool(p_value > alpha)  # Convert to Python bool


def check_linearity(x: np.ndarray, y: np.ndarray, alpha: float = 0.05) -> bool:
    """
    Determine if the relationship between x and y is approximately linear.

    Returns
    -------
    True  -> linear relationship likely
    False -> non-linear relationship likely
    """

    if len(x) < 5:
        return False

    # Pearson correlation
    r, p_r = stats.pearsonr(x, y)

    # Spearman correlation
    rho, p_rho = stats.spearmanr(x, y)

    # If Spearman much stronger -> monotonic non-linear
    if abs(rho) - abs(r) > 0.1:
        return False

    # Quadratic model check
    X = np.column_stack([x, x**2])
    X = np.column_stack([np.ones(len(x)), X])

    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    y_pred = X @ beta

    residuals = y - y_pred
    rss_quad = np.sum(residuals**2)

    # Linear model
    slope, intercept, *_ = stats.linregress(x, y)
    y_lin = slope * x + intercept
    rss_lin = np.sum((y - y_lin)**2)

    # F-test
    df1 = 1
    df2 = len(x) - 3

    f_stat = ((rss_lin - rss_quad) / df1) / (rss_quad / df2)
    p_value = 1 - stats.f.cdf(f_stat, df1, df2)

    if p_value < alpha:
        return False

    return True

def detect_outliers(data: np.ndarray, threshold: float = 3) -> bool:
    """
    Detect outliers using Z-score / MAD method.
    Returns True only if a meaningful proportion of outliers exist.
    """
    if len(data) < 4:
        return False
    
    # Handle constant data
    if np.all(data == data[0]):
        return False
    
    # Small datasets → MAD
    if len(data) < 10:
        median = np.median(data)
        mad = np.median(np.abs(data - median))
        if mad == 0:
            return False
        
        modified_z_scores = 0.6745 * (data - median) / mad
        outliers = np.abs(modified_z_scores) > threshold
    
    else:
        # Large datasets → Z-score
        z_scores = np.abs(stats.zscore(data))
        outliers = z_scores > threshold

    # ✅ NEW: require meaningful proportion
    outlier_count = np.mean(outliers)
    return bool(outlier_count > 0.05)  # Only flag if >5% are outliers
    # return bool(np.any(outliers))


def interpret_strength(coefficient: float) -> str:
    """
    Interpret correlation strength based on absolute value.
    """
    abs_coef = abs(coefficient)
    
    if abs_coef < 0.3:
        return "Weak correlation"
    elif abs_coef < 0.5:
        return "Moderate correlation"
    elif abs_coef < 0.7:
        return "Strong correlation"
    else:
        return "Very strong correlation"


def calculate_effect_size(coefficient: float) -> float:
    """
    Calculate effect size (Cohen's convention: r itself is effect size).
    
    Returns:
        Effect size (small: 0.1, medium: 0.3, large: 0.5)
    """
    return abs(coefficient)


def detect_pattern_type(x: np.ndarray, y: np.ndarray) -> str:
    """
    Detect pattern type in data (linear, quadratic, exponential, etc.).
    Uses proper R² calculation based on sum of squares.
    """

    if len(x) < 5:
        return "insufficient_data"

    # Prevent division by zero if y is constant
    ss_tot = np.sum((y - np.mean(y))**2)
    if ss_tot == 0:
        return "unknown/noisy"

    # ---- Linear fit ----
    slope, intercept, *_ = stats.linregress(x, y)
    y_pred_linear = slope * x + intercept

    ss_res_linear = np.sum((y - y_pred_linear) ** 2)
    r_squared_linear = 1 - ss_res_linear / ss_tot

    # ---- Quadratic fit ----
    coeffs = np.polyfit(x, y, 2)
    y_pred_quad = np.polyval(coeffs, x)

    ss_res_quad = np.sum((y - y_pred_quad) ** 2)
    r_squared_quad = 1 - ss_res_quad / ss_tot

    # ---- Exponential fit (if valid) ----
    if np.all(y > 0):
        try:
            log_y = np.log(y)
            slope_exp, intercept_exp, *_ = stats.linregress(x, log_y)

            y_pred_exp = np.exp(intercept_exp + slope_exp * x)

            ss_res_exp = np.sum((y - y_pred_exp) ** 2)
            r_squared_exp = 1 - ss_res_exp / ss_tot

        except Exception:
            r_squared_exp = 0
    else:
        r_squared_exp = 0

    # ---- Determine best fit ----
    best_r2 = max(r_squared_linear, r_squared_quad, r_squared_exp)

    if best_r2 == r_squared_linear and r_squared_linear > 0.7:
        return "linear"
    elif best_r2 == r_squared_quad and r_squared_quad > 0.7:
        return "quadratic"
    elif best_r2 == r_squared_exp and r_squared_exp > 0.7:
        return "exponential"
    else:
        return "unknown/noisy"


def add_regression_line(ax: plt.Axes, x: np.ndarray, y: np.ndarray,
                       show_confidence_interval: bool = True) -> None:
    """
    Add regression line with confidence interval to plot.
    
    Args:
        ax: Matplotlib axes object
        x: X values
        y: Y values
        show_confidence_interval: Whether to show confidence interval
    """
    # Calculate regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    
    # Create regression line
    x_line = np.linspace(min(x), max(x), 100)
    y_line = slope * x_line + intercept
    
    # Plot regression line
    ax.plot(x_line, y_line, color='red', linewidth=2,
            label=f'Regression (y = {slope:.2f}x + {intercept:.2f})')
    
    # Add confidence interval if configured
    if show_confidence_interval:
        # Calculate prediction interval (95% confidence)
        y_pred = slope * x + intercept
        residuals = y - y_pred
        std_residuals = np.std(residuals, ddof=2)  # Unbiased estimator
        
        # 95% confidence interval for prediction
        ci_upper = y_line + 1.96 * std_residuals
        ci_lower = y_line - 1.96 * std_residuals
        
        ax.fill_between(x_line, ci_lower, ci_upper, color='red', alpha=0.2,
                        label='95% Prediction Interval')


def prepare_stats_data(method: CorrelationMethod, coefficient: float,
                      p_value: float, n: int, assumptions: Dict[str, Any],
                      alpha: float = 0.05) -> Dict[str, Any]:
    """
    Prepare statistics data for the unified stats table.

    Returns:
        Dictionary with all correlation statistics
    """
    return {
        "method_used": method.value.capitalize(),
        "sample_size": n,
        "coefficient": coefficient,
        "p_value": p_value,
        "is_significant": bool(p_value < alpha),  # Use alpha parameter, not self
        "strength_interpretation": interpret_strength(coefficient),
        "r_squared": coefficient ** 2 if method == CorrelationMethod.PEARSON else None,
        "effect_size": calculate_effect_size(coefficient),
        "normality_assumption": "✓" if assumptions.get('normal_distributed', False) else "✗",
        "linearity_assumption": "✓" if assumptions.get('linear_relationship', False) else "✗",
        "outliers_detected": "✓" if assumptions.get('has_outliers', False) else "✗",
        "pattern_detected": assumptions.get('pattern_type', 'unknown').capitalize()
    }


def get_results_summary(results) -> Dict[str, Any]:
    """
    Get a summary of the correlation analysis results.
    
    Returns:
        Dictionary with key results and interpretations
        
    Raises:
        ValueError: If process() hasn't been called yet
    """
    if results is None:
        raise ValueError("No results available. Call process() first.")
    
    return {
        "method": results.method_used.value,
        "coefficient": results.coefficient,
        "p_value": results.p_value,
        "significant": results.is_significant,
        "interpretation": results.strength_interpretation,
        "sample_size": results.sample_size,
        "r_squared": results.r_squared,
        "assumptions": results.assumptions_checked
    }


def export_data(analysis_instance) -> Dict[str, Any]:
    """
    Export all data and results for external use.
    
    Returns:
        Complete dictionary with input data, assumptions, and results
    """
    if analysis_instance.results is None:
        raise ValueError("No results available. Call process() first.")
    
    return {
        "metadata": {
            "project": analysis_instance.project,
            "step": analysis_instance.step,
            "timestamp": pd.Timestamp.now().isoformat()
        },
        "input_data": {
            "dataset_name": analysis_instance.data.dataset_name,
            "x_label": analysis_instance.data.x_label,
            "y_label": analysis_instance.data.y_label,
            "x_values": analysis_instance.data.x_values,
            "y_values": analysis_instance.data.y_values
        },
        "clean_data": {
            "x": analysis_instance.clean_x.tolist() if analysis_instance.clean_x is not None else None,
            "y": analysis_instance.clean_y.tolist() if analysis_instance.clean_y is not None else None
        },
        "assumptions": analysis_instance.results.assumptions_checked,
        "results": {
            "method": analysis_instance.results.method_used.value,
            "coefficient": analysis_instance.results.coefficient,
            "p_value": analysis_instance.results.p_value,
            "significant": analysis_instance.results.is_significant,
            "interpretation": analysis_instance.results.strength_interpretation,
            "r_squared": analysis_instance.results.r_squared,
            "effect_size": calculate_effect_size(analysis_instance.results.coefficient)
        }
    }