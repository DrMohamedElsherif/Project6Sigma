
# api/charts/core/table_styling.py - Corporate Style


from dataclasses import dataclass
from typing import Dict, List


@dataclass
class TableStyle:
    """Professional corporate styling"""
    # Colors - Modern corporate palette
    header_color: str = '#1B4F72'  # Deep corporate blue
    header_text_color: str = 'black'
    row_even_color: str = '#E8F0FE'  # Very light blue
    row_odd_color: str = '#FFFFFF'  # White
    hover_color: str = '#D4E6F1'  # For potential hover effects
    
    # Font settings - Better readability
    header_fontsize: int = 10
    header_fontweight: str = 'bold'
    data_fontsize: int = 9
    title_fontsize: int = 11
    title_fontweight: str = 'bold'
    
    # Table dimensions
    scale_x: float = 1.0
    scale_y: float = 1.4  # More vertical breathing
    title_top_margin: float = 0.94  # Tighter title spacing
    
    # Column widths (relative)
    single_col_widths: Dict[str, float] = None
    multi_col_metric_width: float = 0.28  # Slightly narrower metric column
    
    # Borders
    border_width: float = 0.5
    border_color: str = '#BDC3C7'  # Soft gray border
    
    def __post_init__(self):
        if self.single_col_widths is None:
            self.single_col_widths = {'metric': 0.38, 'value': 0.32}


@dataclass
class DashboardStyle(TableStyle):
    """Style for analytical dashboards"""
    header_color: str = '#E74C3C'  # Accent red
    header_text_color: str = 'white'
    row_even_color: str = '#FADBD8'  # Light red tint
    row_odd_color: str = '#FFFFFF'
    
    # Highlight key metrics
    highlight_metrics: List[str] = None  # ['Mean', 'Std Dev']
    highlight_color: str = '#FFF3CD'  # Yellow highlight
    
    # Larger, more readable
    header_fontsize: int = 11
    data_fontsize: int = 10
    scale_y: float = 1.5
    
    def __post_init__(self):
        super().__post_init__()
        if self.highlight_metrics is None:
            self.highlight_metrics = ['Mean', 'Std Dev']


DEFAULT_TABLE_STYLE = TableStyle()

