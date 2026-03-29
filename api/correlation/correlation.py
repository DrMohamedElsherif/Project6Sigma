# api/correlation/correlation.py

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import matplotlib.gridspec as gridspec
from typing import Tuple, Dict, Any, Optional
from api.schemas import BusinessLogicException
from api.charts.constants import FIGURE_SIZE_A4_PORTRAIT, TITLE_FONT_SIZE
from api.correlation.schemas import CorrelationRequest, CorrelationMethod, CorrelationResult

from api.correlation.utils import (
    check_normality,
    check_linearity,
    detect_outliers,
    interpret_strength,
    calculate_effect_size,
    detect_pattern_type,
    add_regression_line,           
    prepare_stats_data,             
    get_results_summary,            
    export_data  
)
from api.charts.statistics import (
    StatisticsCalculator,
    add_correlation_stats_table,
    StatsTableType
)
from api.correlation.utils import has_many_ties


class CorrelationAnalysis:
    """
    Main class for correlation analysis.
    Supports Pearson, Spearman, Kendall-Tau with automatic method selection.
    
    Features:
    - Automatic method selection based on data assumptions
    - Multiple correlation methods (Pearson, Spearman, Kendall)
    - Comprehensive visualization with scatter plot and regression line
    - Statistical table with all relevant metrics
    - Pattern detection for non-linear relationships
    """
    
    def __init__(self, data: dict):
        """
        Initialize with validated request data.
        
        Args:
            data: Raw request dictionary
            
        Raises:
            BusinessLogicException: If validation fails
        """
        try:
            validated = CorrelationRequest(**data)
            self.project = validated.project
            self.step = validated.step
            self.config = validated.config
            self.data = validated.data
            self.figure = None
            self.results = None
            self.clean_x = None
            self.clean_y = None
        except Exception as e:
            raise BusinessLogicException(
                error_code="error_validation",
                field=str(e),
                details={"message": str(e)}
            )
    
    def _get_clean_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Clean and prepare data by removing NaN/infinite values.
        
        Returns:
            Tuple of cleaned x and y arrays
            
        Raises:
            BusinessLogicException: If insufficient data points remain
        """
        x = np.array(self.data.x_values, dtype=float)
        y = np.array(self.data.y_values, dtype=float)
        
        # Remove NaN or infinite values
        mask = ~(np.isnan(x) | np.isnan(y) | np.isinf(x) | np.isinf(y))
        x_clean = x[mask]
        y_clean = y[mask]
        
        if len(x_clean) < 2:
            raise BusinessLogicException(
                error_code="error_validation",
                field="data",
                details={"message": "At least 2 valid data points required for correlation analysis"}
            )
        
        if len(x_clean) < 3:
            raise BusinessLogicException(
                error_code="error_validation",
                field="data",
                details={"message": "At least 3 valid data points recommended for meaningful correlation analysis"}
            )
            
        # ✅ NEW: Constant variance check
        if np.std(x_clean) == 0:
            raise BusinessLogicException(
                error_code="error_validation",
                field="x_values",
                details={"message": "X variable has zero variance (all values are identical). Correlation is undefined."}
            )

        if np.std(y_clean) == 0:
            raise BusinessLogicException(
                error_code="error_validation",
                field="y_values",
                details={"message": "Y variable has zero variance (all values are identical). Correlation is undefined."}
            )
        
        # Store cleaned data for later use
        self.clean_x = x_clean
        self.clean_y = y_clean
            
        return x_clean, y_clean
    
    def check_assumptions(self, x: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """
        Check statistical assumptions for method selection.
        
        Evaluates:
        - Normality (Shapiro-Wilk test)
        - Linearity (comparison of Pearson and Spearman coefficients)
        - Outliers (Z-score method)
        
        Returns:
            Dictionary with assumption check results
        """
        # Normality check
        is_x_normal = check_normality(x)
        is_y_normal = check_normality(y)
        # is_normal = is_x_normal and is_y_normal
        if is_x_normal is None or is_y_normal is None:
            is_normal = None
        else:
            is_normal = is_x_normal and is_y_normal
        
        # Linearity check - compare Pearson and Spearman
        is_linear = check_linearity(x, y)
        
        # Outlier detection
        has_x_outliers = detect_outliers(x)
        has_y_outliers = detect_outliers(y)
        has_outliers = has_x_outliers or has_y_outliers
        
        # Additional diagnostics
        pattern_type = detect_pattern_type(x, y)
        
        return {
            # Normality (diagnostic only)
            # 'normal_distributed': is_normal,
            'normal_distributed': (
                is_normal if is_normal is not None else "unknown"
            ),
            'x_normal': is_x_normal if is_x_normal is not None else "unknown",
            'y_normal': is_y_normal if is_y_normal is not None else "unknown",
            # 'x_normal': is_x_normal,
            # 'y_normal': is_y_normal,

            # Core assumptions
            'linear_relationship': is_linear,
            'has_outliers': has_outliers,
            'x_has_outliers': has_x_outliers,
            'y_has_outliers': has_y_outliers,

            # Pattern analysis
            'pattern_type': pattern_type,

            # Metadata
            'sample_size': len(x)
        }
    
    def select_method(self, x: np.ndarray, y: np.ndarray) -> CorrelationMethod:
        """
        Statistically grounded automatic selection of correlation method.
        
        Decision logic:
        1. Kendall → many ties, OR small sample (< 30), OR ordinal data
        2. Spearman → monotonic non-linear OR outliers present
        3. Pearson → linear, clean data, sufficient sample size
        """
        
        # 1. Manual override
        if self.config.method != CorrelationMethod.AUTO:
            return self.config.method
        
        n = len(x)
        
        # 2. Assumptions
        assumptions = self.check_assumptions(x, y)
        
        has_outliers = assumptions.get("has_outliers", False)
        is_linear = assumptions.get("linear_relationship", False)
        
        # 3. Tie detection (important for Kendall)
        # unique_ratio_x = len(np.unique(x)) / n
        # unique_ratio_y = len(np.unique(y)) / n
        # many_ties = (unique_ratio_x < 0.7) or (unique_ratio_y < 0.7)

        many_ties = has_many_ties(x) or has_many_ties(y)
        
        # 4. Small sample detection (Kendall is robust for small n)
        is_small_sample = n < 30 # Common threshold for small sample size in correlation analysis        
        # 5. Correlations (for monotonicity check)
        r, _ = stats.pearsonr(x, y)
        rho, _ = stats.spearmanr(x, y)
        
        # 6. Detect monotonic but non-linear relationship
        monotonic = abs(rho) > 0.7
        nonlinear = not is_linear
        nonlinear_monotonic = monotonic and nonlinear
        
        # =========================
        # DECISION TREE (UPDATED)
        # =========================
        
        # 🔴 1. Many ties → Kendall (ordinal data)
        if many_ties:
            return CorrelationMethod.KENDALL
        
        # 🟠 2. Small sample → Kendall (robust for small n)
        # if is_small_sample:
        #     return CorrelationMethod.KENDALL
        if is_small_sample:
            if is_linear and not has_outliers:
                return CorrelationMethod.PEARSON
            return CorrelationMethod.KENDALL

        
        # 🟡 3. Nonlinear monotonic → Spearman
        if nonlinear_monotonic:
            return CorrelationMethod.SPEARMAN
        
        # 🟡 4. Outliers → Spearman (robust default)
        if has_outliers:
            return CorrelationMethod.SPEARMAN
        
        # 🟢 5. Linear & clean & sufficient sample → Pearson
        if is_linear and n >= 30:
            return CorrelationMethod.PEARSON
        
        # 🟡 6. Fallback → Spearman (safe default)
        return CorrelationMethod.SPEARMAN
    
    def calculate_correlation(self, x: np.ndarray, y: np.ndarray, 
                             method: CorrelationMethod) -> Tuple[float, float]:
        """
        Calculate correlation coefficient and p-value using selected method.
        
        Args:
            x: First variable array
            y: Second variable array
            method: Correlation method to use
            
        Returns:
            Tuple of (correlation coefficient, p-value)
            
        Raises:
            ValueError: If unknown method is specified
        """
        if method == CorrelationMethod.PEARSON:
            coef, p_val = stats.pearsonr(x, y)
        elif method == CorrelationMethod.SPEARMAN:
            coef, p_val = stats.spearmanr(x, y)
        elif method == CorrelationMethod.KENDALL:
            coef, p_val = stats.kendalltau(x, y)
        else:
            raise ValueError(f"Unknown correlation method: {method}")
            
        return float(coef), float(p_val)
    

    def _create_visualization(self, x: np.ndarray, y: np.ndarray,
                          method: CorrelationMethod,
                          coefficient: float, p_value: float,
                          assumptions: Dict[str, Any]):
        """
        Create complete visualization with scatter plot and statistics.
        
        Args:
            x: X values
            y: Y values
            method: Correlation method used
            coefficient: Correlation coefficient
            p_value: P-value
            assumptions: Assumption check results
        """
        # Set style
        sns.set_style("whitegrid")
        self.figure = plt.figure(figsize=FIGURE_SIZE_A4_PORTRAIT)
        
        # Create a GridSpec with two rows: one for plot, one for stats table
        # Using similar proportions as boxplot (18:3 ratio)
        gs = gridspec.GridSpec(
            2, 1,
            height_ratios=[18, 3],  # Match boxplot ratio
            hspace=0.19 # Minimal space between plot and table
        )
        
        # Main plot area
        ax = self.figure.add_subplot(gs[0])
        
        # Hide axes for stats table area (we'll add text table directly to figure)
        table_ax = self.figure.add_subplot(gs[1])
        table_ax.axis("off")
        
        # Scatter plot
        ax.scatter(x, y, color='#a1d111', marker='x', s=100, alpha=0.6, 
                label=f'Data points (n={len(x)})')
        
        # Add regression line if configured
        if self.config.show_regression:
            add_regression_line(ax, x, y, self.config.show_confidence_interval)
        
        # Create title with results
        strength = interpret_strength(coefficient)
        significance = "p < 0.05" if p_value < self.config.alpha else "p ≥ 0.05"
        
        title_lines = [
            f"{self.config.title}",
            f"Method: {method.value.capitalize()} | r = {coefficient:.3f} (p = {p_value:.4f})",
            f"{strength} | {significance}",
            f"Pattern: {assumptions['pattern_type'].capitalize()}"
        ]
        ax.set_title('\n'.join(title_lines), fontsize=TITLE_FONT_SIZE, pad=20)
        
        # Labels and grid
        ax.set_xlabel(self.data.x_label or 'X Variable', fontsize=11)
        ax.set_ylabel(self.data.y_label or 'Y Variable', fontsize=11)
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.legend(loc='best', framealpha=0.9)
        
        # Prepare statistics data for table
        stats_data = prepare_stats_data(  
        method, coefficient, p_value, len(x), assumptions, self.config.alpha
    )
        
        # Add statistics table using unified function
        add_correlation_stats_table(
            figure=self.figure,
            stats_data=stats_data,
            dataset_name=self.data.dataset_name or "Correlation Analysis",
            title="Correlation Statistics",
            position=(0.15, 0.08),  # Slightly higher position within the table area
            fontsize=9,
            color_significant=True,
            significant_key="is_significant"
        )
        
        # Don't use tight_layout with rect as it interferes with GridSpec
        # Just do a simple tight_layout
        plt.tight_layout()
    
    def process(self) -> plt.Figure:
        """
        Execute complete correlation analysis workflow.
        
        Steps:
        1. Clean and validate input data
        2. Check statistical assumptions
        3. Select optimal correlation method
        4. Calculate correlation coefficient and p-value
        5. Store results
        6. Create visualization with statistics table
        
        Returns:
            Matplotlib figure with complete visualization
            
        Raises:
            BusinessLogicException: If any error occurs during processing
        """
        try:
            # 1. Clean data
            x, y = self._get_clean_data()
            
            # 2. Check assumptions
            assumptions = self.check_assumptions(x, y)
            
            # 3. Select method
            method = self.select_method(x, y)
            
            # 4. Calculate correlation
            coefficient, p_value = self.calculate_correlation(x, y, method)
            
            # 5. Store results with all metadata
            self.results = CorrelationResult(
                method_used=method,
                coefficient=coefficient,
                p_value=p_value,
                is_significant=p_value < self.config.alpha,
                strength_interpretation=interpret_strength(coefficient),
                sample_size=len(x),
                r_squared=coefficient ** 2 if method == CorrelationMethod.PEARSON else None,
                assumptions_checked=assumptions
            )
            
            # 6. Create visualization
            self._create_visualization(x, y, method, coefficient, p_value, assumptions)
            
            # Prevent display in notebook environments
            plt.close('all')
            
            return self.figure
            
        except BusinessLogicException:
            # Re-raise business logic exceptions
            raise
        except Exception as e:
            # Wrap unexpected errors
            raise BusinessLogicException(
                error_code="correlation_error",
                field="process",
                details={"message": f"Correlation analysis failed: {str(e)}"}
            )
    

# Convenience function for quick correlation analysis
def analyze_correlation(x_values: list, y_values: list, 
                       method: CorrelationMethod = CorrelationMethod.AUTO,
                       title: str = "Correlation Analysis",
                       **kwargs) -> plt.Figure:
    """
    Quick correlation analysis with minimal configuration.
    
    Args:
        x_values: List of x values
        y_values: List of y values
        method: Correlation method (default: AUTO)
        title: Plot title
        **kwargs: Additional configuration parameters
        
    Returns:
        Matplotlib figure with correlation analysis
    """
    from api.correlation.schemas import CorrelationConfig, CorrelationData
    
    # Create minimal request
    request = {
        "project": kwargs.get("project", "quick_analysis"),
        "step": kwargs.get("step", "analyze"),
        "config": CorrelationConfig(
            title=title,
            method=method,
            show_regression=kwargs.get("show_regression", True),
            show_confidence_interval=kwargs.get("show_confidence_interval", True),
            alpha=kwargs.get("alpha", 0.05)
        ).dict(),
        "data": CorrelationData(
            dataset_name=kwargs.get("dataset_name", "Dataset"),
            x_values=x_values,
            y_values=y_values,
            x_label=kwargs.get("x_label", "X Variable"),
            y_label=kwargs.get("y_label", "Y Variable")
        ).dict()
    }
    
    # Run analysis
    analyzer = CorrelationAnalysis(request)
    return analyzer.process()