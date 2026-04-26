# api/charts/core/statistics/calculators.py
import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, Any, Tuple
from api.schemas import BusinessLogicException

class DescriptiveStatsCalculator:
    """Pure statistical calculator - NO formatting or table logic"""
    
    @staticmethod
    def calculate(data: pd.Series, column_name: str = "") -> Dict[str, Any]:
        """Calculate raw descriptive statistics"""
        clean_data = data.dropna()
        n = len(clean_data)
        
        if n == 0:
            raise BusinessLogicException(
                error_code="error_validation",
                field=column_name or "data",
                details={"message": "Dataset contains only NaN values or is empty"}
            )
        
        if n == 1:
            raise BusinessLogicException(
                error_code="error_validation",
                field=column_name or "data",
                details={"message": "At least two valid data points are required"}
            )
        
        # Calculate statistics
        mean = np.mean(clean_data)
        median = np.median(clean_data)
        std = np.std(clean_data, ddof=1)
        min_val = np.min(clean_data)
        max_val = np.max(clean_data)
        q1 = np.percentile(clean_data, 25)
        q3 = np.percentile(clean_data, 75)
        iqr = q3 - q1
        
        ci_lower, ci_upper = stats.t.interval(
            0.95, n-1, loc=mean, scale=std/np.sqrt(n)
        )
        
        # Return raw values (NO formatting)
        return {
            "column_name": column_name,
            "n": n,
            "average": float(mean),
            "median": float(median),
            "min": float(min_val),
            "max": float(max_val),
            "range": (float(min_val), float(max_val)),  # Store as tuple
            "standard_deviation": float(std),
            "ci_95_lower": float(ci_lower),
            "ci_95_upper": float(ci_upper),
            "q1": float(q1),
            "q3": float(q3),
            "iqr": float(iqr)
        }