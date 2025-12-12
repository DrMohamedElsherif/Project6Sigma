from api.charts.boxplots.base_boxplot import BaseBoxplot
from api.charts.schemas.boxplot_schemas import BoxplotRequest
from api.charts.statistics import calculate_descriptive_stats, add_stats_table

class Boxplot1(BaseBoxplot):
    request_model = BoxplotRequest

    def compute_statistics(self, df):
        key = df.columns[0]
        return calculate_descriptive_stats(df[key], key)

    def postprocess(self, ax):
        add_stats_table(
            figure=self.figure,
            stats_data=self.statistics,
            position=(0.15, 0.19),
            fontsize=9
        )
