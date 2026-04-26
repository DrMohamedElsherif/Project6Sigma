# api/charts/evaluation/boxplot_v2.py
"""
Migrated boxplot using new architecture.
Keep old boxplot.py for backward compatibility.
"""
import pandas as pd
from api.charts.core.base_chart_compat import BaseChartV2
from api.charts.evaluation.boxplot_schemas import BoxplotRequest
from api.charts.core.styling import draw_boxplot


class BoxplotV2(BaseChartV2):
    """Boxplot with new architecture - better table handling"""
    
    request_model = BoxplotRequest
    use_new_architecture = True  # Enable new features
    
    DEFAULT_TITLE_TOP_MARGIN = 0.92
    
    def process(self):
        df = self.get_dataframe()
        self.compute_and_store_statistics(df)
        
        variant = self.config.variant
        
        if variant == "single":
            return self._single(df)
        
        if variant == "faceted_by_group":
            return self._faceted(df)
        
        if variant == "multipanel_columns":
            return self._multipanel(df)
        
        raise ValueError(f"Unknown variant: {variant}")
    
    def _single(self, df):
        # Control both table size and gap
        ax = self.create_figure(
            layout="single", 
            with_table=True,
            table_height=self.DEFAULT_TABLE_HEIGHT,
            table_gap=self.DEFAULT_TABLE_GAP
        )[0]
        
        draw_boxplot(ax, df)
        ax.set_title(self.config.title)
        
        return self.finalize(
            add_stats=True, 
            dataset_name=self.config.title or "Dataset", 
            title_top_margin=self.DEFAULT_TITLE_TOP_MARGIN
        )
    
    def _faceted(self, df):
        if not self.data.categories:
            raise ValueError("categories required")
        
        categories_df = pd.DataFrame(self.data.categories)
        cat_col = categories_df.columns[0]
        unique = categories_df[cat_col].unique()
        
        # Create faceted plot with table
        axes = self.create_figure(
            layout="multipanel",
            rows=1,
            cols=len(unique),
            with_table=True,
            table_height=self.DEFAULT_TABLE_HEIGHT,
            table_gap=self.DEFAULT_TABLE_GAP
        )
        
        for ax, cat in zip(axes, unique):
            subset = (
                df.join(categories_df)
                .loc[categories_df[cat_col] == cat, df.columns]
            )
            
            draw_boxplot(ax, subset)
            ax.set_title(f"Group: {cat}")
        
        self.figure.suptitle(self.config.title, y=0.98)
        
        return self.finalize(
            add_stats=True, 
            dataset_name=self.config.title or "Dataset", 
            title_top_margin=self.DEFAULT_TITLE_TOP_MARGIN
        )
    
    def _multipanel(self, df):
        cols = 2
        rows = (len(df.columns) + 1) // 2
        
        # Create multipanel plot with table
        axes = self.create_figure(
            layout="multipanel",
            rows=rows,
            cols=cols,
            with_table=True,
            table_height=self.DEFAULT_TABLE_HEIGHT,
            table_gap=self.DEFAULT_TABLE_GAP
        )
        
        for ax, col in zip(axes, df.columns):
            draw_boxplot(ax, df[[col]])
            ax.set_title(col)
        
        # Remove unused subplots
        for ax in axes[len(df.columns):]:
            ax.remove()
        
        self.figure.suptitle(self.config.title, y=0.98)
        
        return self.finalize(
            add_stats=True, 
            dataset_name=self.config.title or "Dataset", 
            title_top_margin=self.DEFAULT_TITLE_TOP_MARGIN
        )