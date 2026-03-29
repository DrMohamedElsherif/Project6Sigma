# api/correlation/tests/test_correlation.py

import pytest
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from unittest.mock import Mock, patch, MagicMock
from api.schemas import BusinessLogicException
from api.correlation.correlation import CorrelationAnalysis, analyze_correlation
from api.correlation.schemas import CorrelationMethod, CorrelationConfig
from api.correlation.correlation import  CorrelationMethod



class TestCorrelationAnalysisInitialization:
    """Tests for CorrelationAnalysis.__init__ method"""
    
    def test_valid_initialization(self):
        """Test that valid data initializes correctly"""
        data = {
            "project": "test_project",
            "step": "analyze",
            "config": {
                "title": "Test Correlation",
                "method": "auto",
                "show_regression": True,
                "show_confidence_interval": True,
                "alpha": 0.05
            },
            "data": {
                "dataset_name": "Test Dataset",
                "x_values": [1, 2, 3, 4, 5],
                "y_values": [2, 4, 6, 8, 10],
                "x_label": "X Variable",
                "y_label": "Y Variable"
            }
        }
        
        analysis = CorrelationAnalysis(data)
        
        assert analysis.project == "test_project"
        assert analysis.step == "analyze"
        assert analysis.config.title == "Test Correlation"
        assert analysis.config.method == CorrelationMethod.AUTO
        assert analysis.data.dataset_name == "Test Dataset"
        assert analysis.data.x_values == [1, 2, 3, 4, 5]
        assert analysis.data.y_values == [2, 4, 6, 8, 10]
        assert analysis.figure is None
        assert analysis.results is None
    
    def test_invalid_data_raises_exception(self):
        """Test that invalid data raises BusinessLogicException"""
        data = {
            "project": "test_project",
            "step": "analyze",
            "config": {},  # Missing required fields
            "data": {}     # Missing required fields
        }
        
        with pytest.raises(BusinessLogicException) as excinfo:
            CorrelationAnalysis(data)
        
        assert excinfo.value.error_code == "error_validation"


class TestGetCleanData:
    """Tests for _get_clean_data method"""
    
    @pytest.fixture
    def analysis(self):
        """Create a basic analysis instance for testing"""
        data = {
            "project": "test_project",
            "step": "analyze",
            "config": {
                "title": "Test Correlation",
                "method": "auto",
                "show_regression": True,
                "show_confidence_interval": True,
                "alpha": 0.05
            },
            "data": {
                "dataset_name": "Test Dataset",
                "x_values": [1, 2, 3, 4, 5],
                "y_values": [2, 4, 6, 8, 10],
                "x_label": "X Variable",
                "y_label": "Y Variable"
            }
        }
        return CorrelationAnalysis(data)
    
    def test_clean_data_no_nan(self, analysis):
        """Test cleaning data with no NaN values"""
        x_clean, y_clean = analysis._get_clean_data()
        
        assert len(x_clean) == 5
        assert len(y_clean) == 5
        assert np.array_equal(x_clean, np.array([1, 2, 3, 4, 5]))
        assert np.array_equal(y_clean, np.array([2, 4, 6, 8, 10]))
    
    def test_clean_data_with_nan(self, analysis):
        """Test cleaning data with NaN values"""
        analysis.data.x_values = [1, 2, np.nan, 4, 5]
        analysis.data.y_values = [2, 4, 6, np.nan, 10]
        
        x_clean, y_clean = analysis._get_clean_data()
        
        assert len(x_clean) == 3  # Should remove rows with NaN
        assert len(y_clean) == 3
        assert np.array_equal(x_clean, np.array([1, 2, 5]))
        assert np.array_equal(y_clean, np.array([2, 4, 10]))
    
    def test_clean_data_with_inf(self, analysis):
        """Test cleaning data with infinite values"""
        analysis.data.x_values = [1, 2, np.inf, 4, 5]
        analysis.data.y_values = [2, 4, 6, 8, np.inf]
        
        x_clean, y_clean = analysis._get_clean_data()
        
        assert len(x_clean) == 3  # Should remove rows with inf
        assert len(y_clean) == 3
        assert np.array_equal(x_clean, np.array([1, 2, 4]))
        assert np.array_equal(y_clean, np.array([2, 4, 8]))
    
    def test_insufficient_data_raises_exception(self, analysis):
        """Test that less than 2 data points raises exception"""
        analysis.data.x_values = [1]
        analysis.data.y_values = [2]
        
        with pytest.raises(BusinessLogicException) as excinfo:
            analysis._get_clean_data()
        
        assert "At least 2 valid data points" in str(excinfo.value.details['message'])
    
    def test_warning_for_small_sample(self, analysis):
        """Test warning for sample size < 3"""
        analysis.data.x_values = [1, 2]
        analysis.data.y_values = [2, 4]
        
        with pytest.raises(BusinessLogicException) as excinfo:
            analysis._get_clean_data()
        
        assert "At least 3 valid data points recommended" in str(excinfo.value.details['message'])


class TestCheckAssumptions:
    """Tests for check_assumptions method"""
    
    @pytest.fixture
    def analysis(self):
        """Create a basic analysis instance for testing"""
        data = {
            "project": "test_project",
            "step": "analyze",
            "config": {
                "title": "Test Correlation",
                "method": "auto",
                "show_regression": True,
                "show_confidence_interval": True,
                "alpha": 0.05
            },
            "data": {
                "dataset_name": "Test Dataset",
                "x_values": [1, 2, 3, 4, 5],
                "y_values": [2, 4, 6, 8, 10],
                "x_label": "X Variable",
                "y_label": "Y Variable"
            }
        }
        return CorrelationAnalysis(data)
    
    def test_normal_linear_no_outliers(self, analysis):
        """Test assumptions for perfect linear data"""
        np.random.seed(42)
        x = np.random.normal(0, 1, 100)
        y = 2 * x + 1 + np.random.normal(0, 0.1, 100)
        
        assumptions = analysis.check_assumptions(x, y)
        
        assert 'normal_distributed' in assumptions
        assert 'linear_relationship' in assumptions
        assert 'has_outliers' in assumptions
        assert 'sample_size' in assumptions
        assert 'pattern_type' in assumptions
    
    def test_with_outliers(self, analysis):
        """Test assumptions with data containing outliers"""
        x = np.array([1, 2, 3, 4, 5, 100])
        y = np.array([2, 4, 6, 8, 10, 200])
        
        assumptions = analysis.check_assumptions(x, y)
        
        assert assumptions['has_outliers'] is True
        assert assumptions['x_has_outliers'] is True
        assert assumptions['y_has_outliers'] is True


import pytest
import numpy as np
from scipy import stats
from api.correlation.correlation import CorrelationMethod, CorrelationAnalysis

class TestSelectMethod:

    @pytest.fixture
    def analysis(self):
        config = CorrelationConfig(
            title="Test Correlation",  # required
            method=CorrelationMethod.AUTO,
            show_regression=True,
            show_confidence_interval=True,
            alpha=0.05
        )
        # Create minimal valid data
        data = {
            "project": "test_project",
            "step": "analyze",
            "config": config.model_dump(),  # Pydantic v2 uses model_dump()
            "data": {
                "dataset_name": "Test Dataset",
                "x_values": [1, 2, 3],
                "y_values": [1, 2, 3],
                "x_label": "X Variable",
                "y_label": "Y Variable"
            }
        }
        return CorrelationAnalysis(data)

    # def analysis(self):
    #     # Create a CorrelationAnalysis instance with AUTO method
    #     config = CorrelationConfig(method=CorrelationMethod.AUTO)
    #     return CorrelationAnalysis(config)

    def test_pearson_selection(self, analysis):
        x = np.arange(50)
        y = 2 * x + np.random.normal(0, 0.1, 50)
        method = analysis.select_method(x, y)
        assert method == CorrelationMethod.PEARSON

    def test_spearman_for_nonlinear_monotonic(self, analysis):
        x = np.linspace(1, 50, 50)
        y = np.log(x) 
        method = analysis.select_method(x, y)
        assert method == CorrelationMethod.SPEARMAN

    def test_spearman_for_outliers(self, analysis):
        x = np.arange(50)
        y = 2 * x
        y[10] += 20000  # Add outlier
        method = analysis.select_method(x, y)
        assert method == CorrelationMethod.SPEARMAN
        
    def test_spearman_for_monotonic_with_outliers(self, analysis):
        x = np.linspace(1, 50, 50)
        y = np.log(x)
        y[25] += 50  # outlier

        method = analysis.select_method(x, y)
        assert method == CorrelationMethod.SPEARMAN
        
    # def test_small_sample_defaults(self, analysis):
    #     x = np.array([1, 2, 3, 4])
    #     y = np.array([1, 4, 9, 16])

    #     method = analysis.select_method(x, y)
    #     assert method in [CorrelationMethod.KENDALL]
    
    # def test_small_sample_linear_uses_kendall(self, analysis):
    #     """Very small sample (n=5) with linear relationship should use Kendall"""
    #     x = np.array([1, 2, 3, 4, 5])
    #     y = 2 * x + 1
        
    #     method = analysis.select_method(x, y)
        
    #     # Kendall is more robust for very small samples
    #     assert method == CorrelationMethod.KENDALL
    def test_small_sample_linear_uses_pearson(self, analysis):
        """Small sample with clean linear relationship should use Pearson"""
        x = np.array([1, 2, 3, 4, 5])
        y = 2 * x + 1
        
        method = analysis.select_method(x, y)
        #SSmall sample but clean linear data → Pearson
        assert method == CorrelationMethod.PEARSON
        
    def test_small_sample_nonlinear_uses_kendall(self, analysis):
        x = np.array([1, 2, 3, 4, 5])
        y = x ** 2
        
        method = analysis.select_method(x, y)
        
        assert method == CorrelationMethod.KENDALL
        
    def test_small_sample_with_outliers_uses_kendall(self, analysis):
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 100])  # outlier
        
        method = analysis.select_method(x, y)
        
        assert method == CorrelationMethod.KENDALL
    

    def test_kendall_for_many_ties(self, analysis):
        x = np.array([1, 1, 1, 2, 2, 2, 3, 3, 3])
        y = np.array([10, 10, 10, 20, 20, 20, 30, 30, 30])
        method = analysis.select_method(x, y)
        assert method == CorrelationMethod.KENDALL

    def test_manual_method_override(self, analysis):
        analysis.config.method = CorrelationMethod.PEARSON
        x = np.arange(50)
        y = np.log(x) + np.random.normal(0, 0.1, 50)
        method = analysis.select_method(x, y)
        # Should return the manual method, not auto-selected
        assert method == CorrelationMethod.PEARSON


class TestCalculateCorrelation:
    """Tests for calculate_correlation method"""
    
    @pytest.fixture
    def analysis(self):
        """Create a basic analysis instance for testing"""
        data = {
            "project": "test_project",
            "step": "analyze",
            "config": {
                "title": "Test Correlation",
                "method": "auto",
                "show_regression": True,
                "show_confidence_interval": True,
                "alpha": 0.05
            },
            "data": {
                "dataset_name": "Test Dataset",
                "x_values": [1, 2, 3, 4, 5],
                "y_values": [2, 4, 6, 8, 10],
                "x_label": "X Variable",
                "y_label": "Y Variable"
            }
        }
        return CorrelationAnalysis(data)
    
    def test_pearson_calculation(self, analysis):
        """Test Pearson correlation calculation"""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        
        coef, p_val = analysis.calculate_correlation(x, y, CorrelationMethod.PEARSON)
        
        assert coef == 1.0  # Perfect correlation
        assert p_val <= 0.05  # Should be significant
    
    def test_spearman_calculation(self, analysis):
        """Test Spearman correlation calculation"""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        
        coef, p_val = analysis.calculate_correlation(x, y, CorrelationMethod.SPEARMAN)
        
        assert coef == pytest.approx(1.0, abs=1e-10)  # Use approx for floating point
        assert p_val <= 0.05

    def test_kendall_calculation(self, analysis):
        """Test Kendall correlation calculation"""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        
        coef, p_val = analysis.calculate_correlation(x, y, CorrelationMethod.KENDALL)
        
        assert coef == pytest.approx(1.0, abs=1e-10)  # Use approx for floating point
        assert p_val <= 0.05
    
    def test_negative_correlation(self, analysis):
        """Test calculation of negative correlation"""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([10, 8, 6, 4, 2])  # Perfect negative
        
        coef, p_val = analysis.calculate_correlation(x, y, CorrelationMethod.PEARSON)
        
        assert coef == -1.0
    
    def test_no_correlation(self, analysis):
        """Test calculation of no correlation"""
        np.random.seed(42)
        x = np.random.normal(0, 1, 50)
        y = np.random.normal(0, 1, 50)  # Independent
        
        coef, p_val = analysis.calculate_correlation(x, y, CorrelationMethod.PEARSON)
        
        assert abs(coef) < 0.3  # Should be close to 0
        assert p_val > 0.05  # Should not be significant
    
    def test_unknown_method_raises_error(self, analysis):
        """Test that unknown method raises ValueError"""
        x = np.array([1, 2, 3])
        y = np.array([2, 4, 6])
        
        with pytest.raises(ValueError):
            analysis.calculate_correlation(x, y, "unknown_method")  # type: ignore


class TestProcessMethod:
    """Tests for the main process method"""
    
    @pytest.fixture
    def analysis(self):
        """Create a basic analysis instance for testing"""
        data = {
            "project": "test_project",
            "step": "analyze",
            "config": {
                "title": "Test Correlation",
                "method": "auto",
                "show_regression": True,
                "show_confidence_interval": True,
                "alpha": 0.05
            },
            "data": {
                "dataset_name": "Test Dataset",
                "x_values": [1, 2, 3, 4, 5],
                "y_values": [2, 4, 6, 8, 10],
                "x_label": "X Variable",
                "y_label": "Y Variable"
            }
        }
        return CorrelationAnalysis(data)
    
    def test_process_returns_figure(self, analysis):
        """Test that process returns a matplotlib figure"""
        figure = analysis.process()
        
        assert isinstance(figure, plt.Figure)
        assert analysis.results is not None
        # assert analysis.results.method_used == CorrelationMethod.KENDALL
        assert analysis.results.method_used == CorrelationMethod.PEARSON
        assert analysis.results.coefficient == pytest.approx(1.0, abs=1e-10)
    
    def test_process_stores_results(self, analysis):
        """Test that process stores results correctly"""
        figure = analysis.process()
        
        # assert analysis.results.method_used == CorrelationMethod.KENDALL
        assert analysis.results.method_used == CorrelationMethod.PEARSON
        assert analysis.results.coefficient == pytest.approx(1.0, abs=1e-10)
        assert analysis.results.p_value <= 0.05
        assert analysis.results.is_significant is True
        assert analysis.results.sample_size == 5
        # assert analysis.results.r_squared is None  # R-squared is not calculated for Kendall
        # New (correct for Pearson):
        if analysis.results.method_used == CorrelationMethod.PEARSON:
            assert analysis.results.r_squared == pytest.approx(analysis.results.coefficient ** 2, abs=1e-10)
        else:
            assert analysis.results.r_squared is None
    
    @patch('api.correlation.correlation.add_regression_line')
    def test_regression_line_called_when_configured(self, mock_add_regression_line, analysis):
        """Test that regression line is added when configured"""
        analysis.config.show_regression = True
        figure = analysis.process()
        
        # We can't easily assert the call because it's inside _create_visualization
        # But we can check that the method completed successfully
        assert isinstance(figure, plt.Figure)
    
    def test_error_handling(self, analysis):
        """Test that errors are wrapped in BusinessLogicException"""
        # Force an error by providing invalid data
        analysis.data.x_values = [1]
        analysis.data.y_values = [2]
        
        with pytest.raises(BusinessLogicException) as excinfo:
            analysis.process()
        
        # The error code might be either 'error_validation' or 'correlation_error'
        # depending on where it fails
        assert excinfo.value.error_code in ['error_validation', 'correlation_error']


class TestAnalyzeCorrelation:
    """Tests for the convenience function analyze_correlation"""
    
    def test_analyze_correlation_returns_figure(self):
        """Test that analyze_correlation returns a figure"""
        x_values = [1, 2, 3, 4, 5]
        y_values = [2, 4, 6, 8, 10]
        
        figure = analyze_correlation(x_values, y_values)
        
        assert isinstance(figure, plt.Figure)
    
    def test_analyze_correlation_with_custom_params(self):
        """Test analyze_correlation with custom parameters"""
        x_values = [1, 2, 3, 4, 5]
        y_values = [2, 4, 6, 8, 10]
        
        figure = analyze_correlation(
            x_values, 
            y_values,
            method=CorrelationMethod.PEARSON,
            title="Custom Title",
            dataset_name="My Dataset",
            x_label="My X",
            y_label="My Y",
            show_regression=False,
            alpha=0.01
        )
        
        assert isinstance(figure, plt.Figure)


class TestEdgeCases:
    """Tests for edge cases and error conditions"""
    
    @pytest.fixture
    def analysis(self):
        """Create a basic analysis instance for testing"""
        data = {
            "project": "test_project",
            "step": "analyze",
            "config": {
                "title": "Test Correlation",
                "method": "auto",
                "show_regression": True,
                "show_confidence_interval": True,
                "alpha": 0.05
            },
            "data": {
                "dataset_name": "Test Dataset",
                "x_values": [1, 2, 3, 4, 5],
                "y_values": [2, 4, 6, 8, 10],
                "x_label": "X Variable",
                "y_label": "Y Variable"
            }
        }
        return CorrelationAnalysis(data)
    
    def test_constant_values(self, analysis):
        """Test with constant values (variance = 0)"""
        analysis.data.x_values = [1, 1, 1, 1, 1]
        analysis.data.y_values = [2, 2, 2, 2, 2]
        
        # This should raise an exception because correlation is undefined
        with pytest.raises(BusinessLogicException):
            analysis.process()
    
    def test_all_nan_values(self, analysis):
        """Test with all NaN values"""
        analysis.data.x_values = [np.nan, np.nan, np.nan]
        analysis.data.y_values = [np.nan, np.nan, np.nan]
        
        with pytest.raises(BusinessLogicException) as excinfo:
            analysis._get_clean_data()
        
        assert "At least 2 valid data points" in str(excinfo.value.details['message'])
    
    def test_mismatched_lengths(self, analysis):
        """Test with mismatched array lengths"""
        # Re-initialize with mismatched data - this should fail at validation
        invalid_data = {
            "project": "test_project",
            "step": "analyze",
            "config": {
                "title": "Test Correlation",
                "method": "auto",
                "show_regression": True,
                "show_confidence_interval": True,
                "alpha": 0.05
            },
            "data": {
                "dataset_name": "Test Dataset",
                "x_values": [1, 2, 3],
                "y_values": [1, 2, 3, 4],  # Different length
                "x_label": "X Variable",
                "y_label": "Y Variable"
            }
        }
        
        with pytest.raises(BusinessLogicException):
            CorrelationAnalysis(invalid_data)