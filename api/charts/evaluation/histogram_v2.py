

# api/charts/evaluation/histogram_v2.py 
"""
Migrated histogram using new architecture.
Keep old histogram.py for backward compatibility.
"""
# from api.charts.core.base_chart import BaseChart 
from api.charts.core.base_chart_compat import BaseChartV2
from api.charts.evaluation.histogram_schemas import HistogramRequest
from api.charts.core.styling import draw_histogram

class HistogramV2(BaseChartV2):
    """Histogram with new architecture - better table handling"""
    
    request_model = HistogramRequest
    use_new_architecture = True  # Enable new features
    
    DEFAULT_TITLE_TOP_MARGIN = 0.92
    
    def process(self):
        df = self.get_dataframe()
        self.compute_and_store_statistics(df)
        
        mode = self.config.mode
        
        if mode == "single":
            self._single(df)
        elif mode == "stacked":
            self._stacked(df)
        elif mode == "subplots":
            self._subplots(df)
        else:
            raise ValueError(f"Unsupported histogram mode: {mode}")
        
        return self.finalize(
            add_stats=self.config.show_stats,
            dataset_name="Histogram Data",
            title_top_margin=self.DEFAULT_TITLE_TOP_MARGIN
        )
    
    def _single(self, df):
        if self.config.show_stats:
            ax = self.create_figure(
                layout="single", 
                with_table=True,
                table_height=self.DEFAULT_TABLE_HEIGHT,
                table_gap=self.DEFAULT_TABLE_GAP
            )[0]
        else:
            ax = self.create_figure(layout="single")[0]
        
        draw_histogram(ax, df, bins=self.config.bins, x=df.columns[0])
        ax.set_title(self.config.title)
        ax.set_xlabel(self.config.labelx)
        ax.set_ylabel(self.config.labely)
    
    def _stacked(self, df):
        if self.config.show_stats:
            ax = self.create_figure(
                layout="single", 
                with_table=True,
                table_height=self.DEFAULT_TABLE_HEIGHT,
                table_gap=self.DEFAULT_TABLE_GAP
            )[0]
        else:
            ax = self.create_figure(layout="single")[0]
        
        melted = df.melt(var_name="variable", value_name="value")
        draw_histogram(ax, melted, bins=self.config.bins, multiple="stack",
                      x="value", hue="variable")
        ax.set_title(self.config.title)
    
    def _subplots(self, df):
        n = len(df.columns)
        cols = 2
        rows = (n + 1) // 2
        
        if self.config.show_stats:
            axes = self.create_figure(
                layout="multipanel",
                rows=rows,
                cols=cols,
                with_table=True,
                table_height=self.DEFAULT_TABLE_HEIGHT,
                table_gap=self.DEFAULT_TABLE_GAP
            )
        else:
            axes = self.create_figure(
                layout="multipanel",
                rows=rows,
                cols=cols
            )
        
        for ax, col in zip(axes, df.columns):
            draw_histogram(ax, df[col], bins=self.config.bins)
            ax.set_title(col)
            ax.set_xlabel(self.config.labelx)
            ax.set_ylabel(self.config.labely)
        
        for ax in axes[len(df.columns):]:
            ax.remove()
