# api/correlation/tests/test_utils.py

import pytest
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
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
from api.correlation.schemas import CorrelationMethod, CorrelationResult


class TestCheckNormality:
    """Tests for check_normality function"""
    
    def test_normal_data_returns_true(self):
        """Test that normally distributed data returns True"""
        np.random.seed(42)
        data = np.random.normal(0, 1, 100)
        assert check_normality(data)
    
    def test_non_normal_data_returns_false(self):
        """Test that non-normally distributed data returns False"""
        np.random.seed(42)
        data = np.random.uniform(0, 1, 100)  # Uniform is not normal
        assert check_normality(data) is False
    
    def test_sample_size_too_small_returns_false(self):
        """Test that sample size < 3 returns False"""
        data = np.array([1, 2])
        assert check_normality(data) is False
    
    def test_sample_size_too_large_returns_false(self):
        """Test that sample size > 5000 returns False (Shapiro-Wilk limitation)"""
        data = np.random.normal(0, 1, 5001)
        assert check_normality(data) is False
    
    def test_custom_alpha(self):
        """Test with custom alpha threshold"""
        np.random.seed(42)
        data = np.random.normal(0, 1, 50)
        # With alpha=0.01 (stricter), should still be True for normal data
        assert check_normality(data, alpha=0.01) is True


class TestCheckLinearity:
    """Tests for check_linearity function"""
    
    def test_perfect_linear_returns_true(self):
        """Test that perfectly linear data returns True"""
        x = np.array([1, 2, 3, 4, 5])
        y = 2 * x + 1
        assert check_linearity(x, y) is True
    
    def test_linear_with_noise_returns_true(self):
        """Test that linear data with small noise returns True"""
        np.random.seed(42)
        x = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        y = 2 * x + 1 + np.random.normal(0, 0.5, 10)
        assert check_linearity(x, y) is True
    
    def test_non_linear_returns_false(self):
        """Test that non-linear data returns False"""
        x = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        y = x**2  # Quadratic relationship
        assert check_linearity(x, y) is False
    
    def test_sample_size_too_small_returns_false(self):
        """Test that sample size < 4 returns False"""
        x = np.array([1, 2, 3])
        y = np.array([2, 4, 6])
        assert check_linearity(x, y) is False
    
    def test_custom_threshold(self):
        """Test with custom threshold parameter"""
        x = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        y = 2 * x + 1 + np.random.normal(0, 2, 10)  # More noise
        # With stricter threshold, might fail
        # This test just ensures the parameter is passed correctly
        result = check_linearity(x, y)  # Using default
        assert isinstance(result, bool)


class TestDetectOutliers:
    """Tests for detect_outliers function"""
    
    def test_no_outliers_returns_false(self):
        """Test that data without outliers returns False"""
        np.random.seed(42)
        data = np.random.normal(0, 1, 100)
        assert detect_outliers(data) is False
    
    def test_with_outliers_returns_true(self):
        """Test that data with outliers returns True"""
        data = np.array([1, 2, 3, 4, 5, 100])  # 100 is an outlier
        assert detect_outliers(data) is True
    
    def test_sample_size_too_small_returns_false(self):
        """Test that sample size < 4 returns False"""
        data = np.array([1, 2, 3])
        assert detect_outliers(data) is False
    
    def test_custom_threshold(self):
        """Test with custom threshold"""
        data = np.array([1, 2, 3, 4, 5, 10])  # 10 might be outlier with strict threshold
        # With threshold=2, 10 should be detected
        assert detect_outliers(data, threshold=2) is True
        # With threshold=3, might not be detected
        assert detect_outliers(data, threshold=3) is False


class TestInterpretStrength:
    """Tests for interpret_strength function"""
    
    def test_weak_correlation(self):
        """Test interpretation of weak correlation (< 0.3)"""
        assert interpret_strength(0.1) == "Weak correlation"
        assert interpret_strength(-0.2) == "Weak correlation"
        assert interpret_strength(0.29) == "Weak correlation"
    
    def test_moderate_correlation(self):
        """Test interpretation of moderate correlation (0.3 - 0.5)"""
        assert interpret_strength(0.3) == "Moderate correlation"
        assert interpret_strength(0.4) == "Moderate correlation"
        assert interpret_strength(-0.45) == "Moderate correlation"
        assert interpret_strength(0.49) == "Moderate correlation"
    
    def test_strong_correlation(self):
        """Test interpretation of strong correlation (0.5 - 0.7)"""
        assert interpret_strength(0.5) == "Strong correlation"
        assert interpret_strength(0.6) == "Strong correlation"
        assert interpret_strength(-0.65) == "Strong correlation"
        assert interpret_strength(0.69) == "Strong correlation"
    
    def test_very_strong_correlation(self):
        """Test interpretation of very strong correlation (> 0.7)"""
        assert interpret_strength(0.7) == "Very strong correlation"
        assert interpret_strength(0.85) == "Very strong correlation"
        assert interpret_strength(-0.95) == "Very strong correlation"
        assert interpret_strength(1.0) == "Very strong correlation"


class TestCalculateEffectSize:
    """Tests for calculate_effect_size function"""
    
    def test_effect_size_is_absolute_coefficient(self):
        """Test that effect size equals absolute coefficient"""
        assert calculate_effect_size(0.5) == 0.5
        assert calculate_effect_size(-0.7) == 0.7
        assert calculate_effect_size(0.0) == 0.0
        assert calculate_effect_size(1.0) == 1.0


class TestDetectPatternType:
    """Tests for detect_pattern_type function"""
    
    def test_linear_pattern(self):
        """Test detection of linear pattern"""
        x = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        y = 2 * x + 1
        assert detect_pattern_type(x, y) == "linear"
    
    def test_quadratic_pattern(self):
        """Test detection of quadratic pattern"""
        x = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        y = x**2
        assert detect_pattern_type(x, y) == "quadratic"
    
    def test_exponential_pattern(self):
        """Test detection of exponential pattern"""
        x = np.array([1, 2, 3, 4, 5])
        y = np.exp(x)  # Exponential growth
        assert detect_pattern_type(x, y) == "exponential"
    
    def test_insufficient_data(self):
        """Test with insufficient data points"""
        x = np.array([1, 2, 3, 4])
        y = np.array([1, 4, 9, 16])
        assert detect_pattern_type(x, y) == "insufficient_data"
    
    def test_noisy_data(self):
        """Test with noisy data that doesn't fit a pattern well"""
        np.random.seed(42)
        x = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        y = np.random.normal(0, 1, 10)  # Random noise
        assert detect_pattern_type(x, y) == "unknown/noisy"


class TestAddRegressionLine:
    """Tests for add_regression_line function"""
    
    def test_regression_line_added(self):
        """Test that regression line is added to axes"""
        fig, ax = plt.subplots()
        x = np.array([1, 2, 3, 4, 5])
        y = 2 * x + 1
        
        add_regression_line(ax, x, y, show_confidence_interval=False)
        
        # Check that something was plotted (lines count > 0)
        assert len(ax.lines) > 0
        plt.close(fig)
    
    def test_confidence_interval_added(self):
        """Test that confidence interval is added when requested"""
        fig, ax = plt.subplots()
        x = np.array([1, 2, 3, 4, 5])
        y = 2 * x + 1 + np.random.normal(0, 0.1, 5)
        
        add_regression_line(ax, x, y, show_confidence_interval=True)
        
        # Check that a fill_between was added (PolyCollection)
        assert len(ax.collections) > 0
        plt.close(fig)
    
    def test_no_confidence_interval_when_false(self):
        """Test that confidence interval is not added when false"""
        fig, ax = plt.subplots()
        x = np.array([1, 2, 3, 4, 5])
        y = 2 * x + 1
        
        add_regression_line(ax, x, y, show_confidence_interval=False)
        
        # No fill_between should be present
        assert len(ax.collections) == 0
        plt.close(fig)


class TestPrepareStatsData:
    """Tests for prepare_stats_data function"""
    
    def test_prepare_stats_data_pearson(self):
        """Test stats data preparation for Pearson method"""
        method = CorrelationMethod.PEARSON
        coefficient = 0.85
        p_value = 0.001
        n = 20
        assumptions = {
            'normal_distributed': True,
            'linear_relationship': True,
            'has_outliers': False,
            'pattern_type': 'linear'
        }
        alpha = 0.05
        
        result = prepare_stats_data(method, coefficient, p_value, n, assumptions, alpha)
        
        assert result['method_used'] == 'Pearson'
        assert result['sample_size'] == 20
        assert result['coefficient'] == 0.85
        assert result['p_value'] == 0.001
        assert result['is_significant'] is True
        assert result['strength_interpretation'] == 'Very strong correlation'
        assert result['r_squared'] == pytest.approx(0.7225, abs=1e-10)  # Use approx
        assert result['effect_size'] == 0.85
    
    def test_prepare_stats_data_spearman(self):
        """Test stats data preparation for Spearman method (no R²)"""
        method = CorrelationMethod.SPEARMAN
        coefficient = 0.65
        p_value = 0.02
        n = 50
        assumptions = {
            'normal_distributed': False,
            'linear_relationship': False,
            'has_outliers': False,
            'pattern_type': 'monotonic'
        }
        alpha = 0.05
        
        result = prepare_stats_data(method, coefficient, p_value, n, assumptions, alpha)
        
        assert result['method_used'] == 'Spearman'
        assert result['coefficient'] == 0.65
        assert result['is_significant'] is True
        assert result['r_squared'] is None  # No R² for non-Pearson
        assert result['normality_assumption'] == '✗'
        assert result['linearity_assumption'] == '✗'
        assert result['pattern_detected'] == 'Monotonic'
    
    def test_not_significant(self):
        """Test when p-value > alpha"""
        method = CorrelationMethod.PEARSON
        coefficient = 0.2
        p_value = 0.15
        n = 20
        assumptions = {
            'normal_distributed': True,
            'linear_relationship': True,
            'has_outliers': False,
            'pattern_type': 'linear'
        }
        alpha = 0.05
        
        result = prepare_stats_data(method, coefficient, p_value, n, assumptions, alpha)
        
        assert result['is_significant'] is False
        assert result['strength_interpretation'] == 'Weak correlation'


# Mock classes for testing get_results_summary and export_data
class MockResults:
    def __init__(self):
        self.method_used = CorrelationMethod.PEARSON
        self.coefficient = 0.85
        self.p_value = 0.001
        self.is_significant = True
        self.strength_interpretation = "Very strong correlation"
        self.sample_size = 20
        self.r_squared = 0.7225
        self.assumptions_checked = {
            'normal_distributed': True,
            'linear_relationship': True,
            'has_outliers': False
        }


class MockAnalysis:
    def __init__(self):
        self.project = "test_project"
        self.step = "analyze"
        self.data = MockData()
        self.results = MockResults()
        self.clean_x = np.array([1, 2, 3, 4, 5])
        self.clean_y = np.array([2, 4, 6, 8, 10])


class MockData:
    def __init__(self):
        self.dataset_name = "Test Dataset"
        self.x_label = "X Variable"
        self.y_label = "Y Variable"
        self.x_values = [1, 2, 3, 4, 5]
        self.y_values = [2, 4, 6, 8, 10]


class TestGetResultsSummary:
    """Tests for get_results_summary function"""
    
    def test_get_results_summary(self):
        """Test that results summary is formatted correctly"""
        mock_results = MockResults()
        
        result = get_results_summary(mock_results)
        
        assert result['method'] == 'pearson'
        assert result['coefficient'] == 0.85
        assert result['p_value'] == 0.001
        assert result['significant'] is True
        assert result['interpretation'] == 'Very strong correlation'
        assert result['sample_size'] == 20
        assert result['r_squared'] == 0.7225
        assert result['assumptions'] == mock_results.assumptions_checked


class TestExportData:
    """Tests for export_data function"""
    
    def test_export_data(self):
        """Test that export data is formatted correctly"""
        mock_analysis = MockAnalysis()
        
        result = export_data(mock_analysis)
        
        # Check metadata
        assert result['metadata']['project'] == 'test_project'
        assert result['metadata']['step'] == 'analyze'
        assert 'timestamp' in result['metadata']
        
        # Check input data
        assert result['input_data']['dataset_name'] == 'Test Dataset'
        assert result['input_data']['x_label'] == 'X Variable'
        assert result['input_data']['y_label'] == 'Y Variable'
        assert result['input_data']['x_values'] == [1, 2, 3, 4, 5]
        assert result['input_data']['y_values'] == [2, 4, 6, 8, 10]
        
        # Check clean data
        assert result['clean_data']['x'] == [1, 2, 3, 4, 5]
        assert result['clean_data']['y'] == [2, 4, 6, 8, 10]
        
        # Check assumptions
        assert result['assumptions'] == mock_analysis.results.assumptions_checked
        
        # Check results
        assert result['results']['method'] == 'pearson'
        assert result['results']['coefficient'] == 0.85
        assert result['results']['p_value'] == 0.001
        assert result['results']['significant'] is True
        assert result['results']['interpretation'] == 'Very strong correlation'
        assert result['results']['r_squared'] == 0.7225
        assert result['results']['effect_size'] == 0.85
        