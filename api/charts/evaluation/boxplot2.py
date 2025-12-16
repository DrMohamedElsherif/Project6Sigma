from .base_boxplot import BaseBoxplot
from .boxplot_schemas import BoxplotRequest


class Boxplot2(BaseBoxplot):
    request_model = BoxplotRequest
    show_stats_table = True

    
    