# api/charts/core/layout/layout_regions.py
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

class RegionType(str, Enum):
    """Types of regions that can appear in a layout"""
    PLOT = "plot"
    TABLE = "table"
    TITLE = "title"
    LEGEND = "legend"
    COLORBAR = "colorbar"
    CUSTOM = "custom"

@dataclass
class LayoutRegion:
    """Definition of a single region in the layout"""
    type: RegionType
    height_ratio: float = 1.0  # For vertical layouts
    width_ratio: float = 1.0   # For horizontal layouts
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class FigureLayout:
    """Complete layout specification for a figure"""
    regions: list
    orientation: str = "vertical"  # "vertical" or "horizontal"
    spacing: float = 0.05  # Gap between regions
    top_margin: float = 0.95
    bottom_margin: float = 0.05
    left_margin: float = 0.08
    right_margin: float = 0.95
    metadata: Dict[str, Any] = field(default_factory=dict)
