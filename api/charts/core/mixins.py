
# api/charts/core/mixins.py
"""
Statistics mixin using new modular architecture
"""
from typing import Dict, Any
import pandas as pd
from api.charts.core.statistics.calculators import DescriptiveStatsCalculator


class StatisticsMixin:
    """Mixin for statistics calculation - using new architecture"""
    
    def compute_statistics(self, df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """
        Compute statistics for all columns.
        Uses new DescriptiveStatsCalculator (no dependency on old code).
        """
        calculator = DescriptiveStatsCalculator()
        return {
            col: calculator.calculate(df[col], col)
            for col in df.columns
        }
    
    def compute_single_statistics(self, df: pd.DataFrame, column: str) -> Dict[str, Any]:
        """Compute statistics for a single column"""
        calculator = DescriptiveStatsCalculator()
        return calculator.calculate(df[column], column)