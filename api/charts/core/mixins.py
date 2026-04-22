# /api/charts/core/mixins.py



from api.charts.statistics import StatisticsCalculator

class StatisticsMixin:
    def compute_statistics(self, df):
        return {
            col: StatisticsCalculator.calculate_descriptive_stats(df[col], col)
            for col in df.columns
        }