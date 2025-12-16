# boxplot1.py

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import pandas as pd
import seaborn as sns
from api.charts.statistics import calculate_descriptive_stats, add_stats_table
from .base_boxplot import BaseBoxplot
from .boxplot_schemas import BoxplotRequest
from ..constants import FIGURE_SIZE_A4_PORTRAIT, TITLE_FONT_SIZE


class Boxplot1(BaseBoxplot):
    request_model = BoxplotRequest
    show_stats_table = True


