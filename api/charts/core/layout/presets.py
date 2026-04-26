# api/charts/core/layout/presets.py
from .layout_regions import FigureLayout, LayoutRegion, RegionType

class LayoutPresets:
    """Predefined layout templates for common chart types"""
    
    @staticmethod
    def single_plot_with_table(table_height: float = 0.35, gap: float = 0.09) -> FigureLayout:
        """Standard layout: plot above, table below (compatible with existing)"""
        return FigureLayout(
            regions=[
                LayoutRegion(RegionType.PLOT, height_ratio=1.0 - table_height - gap),
                LayoutRegion(RegionType.TABLE, height_ratio=table_height),
            ],
            orientation="vertical",
            spacing=gap,
            top_margin=0.92,
            bottom_margin=0.05
        )
    
    @staticmethod
    def single_plot_no_table() -> FigureLayout:
        """Simple layout: just a plot"""
        return FigureLayout(
            regions=[
                LayoutRegion(RegionType.PLOT, height_ratio=1.0),
            ],
            orientation="vertical",
            spacing=0,
            top_margin=0.95,
            bottom_margin=0.08
        )
    
    @staticmethod
    def multipanel_with_table(rows: int, cols: int, table_height: float = 0.35, gap: float = 0.09) -> FigureLayout:
        """Grid of subplots with table below"""
        layout = LayoutPresets.single_plot_with_table(table_height, gap)
        layout.metadata = {"grid_rows": rows, "grid_cols": cols}
        return layout
    
    @staticmethod
    def multipanel_no_table(rows: int, cols: int) -> FigureLayout:
        """Grid of subplots without table"""
        layout = LayoutPresets.single_plot_no_table()
        layout.metadata = {"grid_rows": rows, "grid_cols": cols}
        return layout