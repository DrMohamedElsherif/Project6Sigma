# base_boxplot.py

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from api.schemas import BusinessLogicException
from api.charts.statistics import calculate_descriptive_stats, add_stats_table
from api.charts.constants import FIGURE_SIZE_A4_PORTRAIT, TITLE_FONT_SIZE

class BaseBoxplot:
    """
    Base class with common logic for all boxplots.
    Subclasses override:
        - compute_statistics()
        - draw_boxplot()
        - postprocess()
    """

    request_model = None  # subclasses must set this
    show_stats_table = False

    def __init__(self, data: dict):
        try:
            validated = self.request_model(**data)
            self.project = validated.project
            self.step = validated.step
            self.config = validated.config
            self.data = validated.data
            self.figure = None
            self.statistics = None
        except Exception as e:
            raise BusinessLogicException(
                error_code="error_validation",
                field=str(e),
                details={"message": str(e)}
            )

    # ------------------ HOOKS ------------------

    def compute_statistics(self, df):
        """
        Compute descriptive statistics for each column.
        Returns a dict keyed by column names.
        """
        stats_dict = {}
        for col in df.columns:
            stats_dict[col] = calculate_descriptive_stats(df[col], column_name=col)
        return stats_dict


    def draw_boxplot(self, df, ax):
        """Default horizontal boxplot."""
        sns.boxplot(
            data=df,
            ax=ax,
            color="#a1d111",
            linecolor="black",
            showcaps=False,
            linewidth=1,
            flierprops={"marker": "x"},
            width=0.3
        )

    def postprocess(self, ax):
        """Override for extra decorations."""
        pass

    # -------------------------------------------
    
    def process(self):

        dataset_name = getattr(self.data, "dataset_name", "Dataset")
        df = pd.DataFrame(self.data.values)

        # compute statistics only if enabled
        if self.show_stats_table:
            self.statistics = self.compute_statistics(df)
        else:
            self.statistics = None

        # create figure
        if self.show_stats_table:
            import matplotlib.gridspec as gridspec

            self.figure = plt.figure(figsize=FIGURE_SIZE_A4_PORTRAIT)
            gs = gridspec.GridSpec(2, 1, height_ratios=[15, 2], hspace=0.05)

            ax = self.figure.add_subplot(gs[0])
            table_ax = self.figure.add_subplot(gs[1])
            table_ax.axis("off")
        else:
            self.figure = plt.figure(figsize=FIGURE_SIZE_A4_PORTRAIT)
            ax = self.figure.add_subplot(111)

        # draw boxplot
        self.draw_boxplot(df, ax)

        # styling
        ax.set_title(self.config.title, fontsize=TITLE_FONT_SIZE, pad=20)
        ax.grid(True, alpha=0.3)

        # hooks
        self.postprocess(ax)

        # add statistics table
        if self.show_stats_table and self.statistics:
            add_stats_table(
                figure=self.figure,
                stats_data=self.statistics,
                dataset_name=dataset_name,
                fontsize=9
            )

        plt.close(self.figure)
        return self.figure
    
    def get_statistics(self):
        return self.statistics

