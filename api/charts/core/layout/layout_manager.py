# api/charts/core/layout/layout_manager.py
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from typing import Tuple, Dict, List
from .layout_regions import FigureLayout, RegionType

class LayoutManager:
    """Manages figure layout creation"""
    
    @staticmethod
    def create_figure(layout: FigureLayout, figsize: Tuple[float, float]) -> Tuple[plt.Figure, Dict[str, List[plt.Axes]]]:
        """
        Create figure with specified layout.
        
        Returns:
            Tuple of (figure, dict mapping region_type to list of axes)
        """
        fig = plt.figure(figsize=figsize)
        
        if layout.orientation == "vertical":
            return LayoutManager._create_vertical_layout(fig, layout)
        else:
            return LayoutManager._create_horizontal_layout(fig, layout)
    
    @staticmethod
    def _create_vertical_layout(fig: plt.Figure, layout: FigureLayout) -> Tuple[plt.Figure, Dict[str, List[plt.Axes]]]:
        """Create vertical layout (regions stacked vertically)"""
        # Normalize height ratios
        total_ratios = sum(r.height_ratio for r in layout.regions)
        normalized_ratios = [r.height_ratio / total_ratios for r in layout.regions]
        
        # Create GridSpec
        gs = gridspec.GridSpec(
            len(layout.regions), 1,
            height_ratios=normalized_ratios,
            hspace=layout.spacing,
            top=layout.top_margin,
            bottom=layout.bottom_margin,
            left=layout.left_margin,
            right=layout.right_margin
        )
        
        # Create axes for each region
        axes_map = {}
        for idx, region in enumerate(layout.regions):
            if region.type not in axes_map:
                axes_map[region.type] = []
            
            ax = fig.add_subplot(gs[idx])
            ax.region_type = region.type
            ax.region_metadata = region.metadata
            axes_map[region.type].append(ax)
        
        return fig, axes_map
    
    @staticmethod
    def _create_horizontal_layout(fig: plt.Figure, layout: FigureLayout) -> Tuple[plt.Figure, Dict[str, List[plt.Axes]]]:
        """Create horizontal layout (regions side by side)"""
        total_ratios = sum(r.width_ratio for r in layout.regions)
        normalized_ratios = [r.width_ratio / total_ratios for r in layout.regions]
        
        gs = gridspec.GridSpec(
            1, len(layout.regions),
            width_ratios=normalized_ratios,
            wspace=layout.spacing,
            top=layout.top_margin,
            bottom=layout.bottom_margin,
            left=layout.left_margin,
            right=layout.right_margin
        )
        
        axes_map = {}
        for idx, region in enumerate(layout.regions):
            if region.type not in axes_map:
                axes_map[region.type] = []
            
            ax = fig.add_subplot(gs[idx])
            ax.region_type = region.type
            ax.region_metadata = region.metadata
            axes_map[region.type].append(ax)
        
        return fig, axes_map