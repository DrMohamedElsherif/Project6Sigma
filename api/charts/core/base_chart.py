# api/charts/core/base_chart.py
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from api.schemas import BusinessLogicException
from api.charts.constants import FIGURE_SIZE_A4_PORTRAIT
from api.charts.core.mixins import StatisticsMixin
from api.charts.statistics import add_descriptive_stats_table


class BaseChart(StatisticsMixin):
    request_model = None  # override in subclasses

    def __init__(self, data: dict):
        try:
            validated = self.request_model(**data)

            self.project = validated.project
            self.step = validated.step
            self.config = validated.config
            self.data = validated.data

            self.figure = None
            self.axes = []
            self.statistics = None

        except Exception as e:
            raise BusinessLogicException(
                error_code="error_validation",
                field=str(e),
                details={"message": str(e)}
            )

    # ----------------------------
    # DATA
    # ----------------------------

    def get_dataframe(self):
        return pd.DataFrame(self.data.values)

    # ----------------------------
    # STATISTICS
    # ----------------------------

    def compute_and_store_statistics(self, df):
        self.statistics = self.compute_statistics(df)

    # ----------------------------
    # FIGURE FACTORY (UNIFIED)
    # ----------------------------

    def create_figure(
        self,
        *,
        layout="single",
        rows=1,
        cols=1,
        with_table=False
    ):
        self.figure = plt.figure(figsize=FIGURE_SIZE_A4_PORTRAIT)

        if with_table:
            gs = gridspec.GridSpec(
                2, 1,
                height_ratios=[18, 3],
                hspace=0.02
            )

            plot_gs = gs[0]
            table_ax = self.figure.add_subplot(gs[1])
            table_ax.axis("off")
        else:
            plot_gs = gridspec.GridSpec(1, 1)[0]

        # ---- Layout handling ----
        if layout == "single":
            self.axes = [self.figure.add_subplot(plot_gs)]

        elif layout == "multipanel":
            sub_gs = plot_gs.subgridspec(rows, cols, hspace=0.4, wspace=0.3)
            self.axes = [
                self.figure.add_subplot(sub_gs[r, c])
                for r in range(rows)
                for c in range(cols)
            ]
        else:
            raise ValueError(f"Unknown layout: {layout}")

        return self.axes

    # ----------------------------
    # FINALIZATION
    # ----------------------------

    def finalize(self, *, add_stats=False, dataset_name="Dataset"):
        if add_stats and self.statistics:
            add_descriptive_stats_table(
                self.figure,
                self.statistics if len(self.statistics) > 1
                else list(self.statistics.values())[0],
                dataset_name=dataset_name
            )

        plt.close(self.figure)
        return self.figure