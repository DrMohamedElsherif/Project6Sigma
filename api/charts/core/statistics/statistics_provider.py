# api/charts/core/statistics/statistics_provider.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import pandas as pd
from .calculators import DescriptiveStatsCalculator

class StatisticsProvider(ABC):
    """Base class for chart-specific statistics providers"""
    
    @abstractmethod
    def compute(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Compute statistics for this chart type"""
        pass

class DescriptiveStatisticsProvider(StatisticsProvider):
    """Provider for descriptive statistics (compatible with existing)"""
    
    def __init__(self, columns: Optional[List[str]] = None):
        self.columns = columns
    
    def compute(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Compute descriptive stats for specified columns"""
        calc = DescriptiveStatsCalculator()
        columns = self.columns or df.columns
        
        if len(columns) == 1:
            # Single column - return dict (not nested) for backward compatibility
            return calc.calculate(df[columns[0]], columns[0])
        else:
            # Multiple columns - return nested dict
            return {
                col: calc.calculate(df[col], col)
                for col in columns
            }

