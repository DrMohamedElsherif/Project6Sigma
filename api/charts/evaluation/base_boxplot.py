
# base_boxplot.py
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.gridspec as gridspec

from api.schemas import BusinessLogicException
from api.charts.statistics import calculate_descriptive_stats, add_stats_table
from api.charts.constants import FIGURE_SIZE_A4_PORTRAIT, TITLE_FONT_SIZE


class BaseBoxplot:
    request_model = None
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

    # ---------------- FIGURE FACTORY ----------------

    def _create_figure(self, layout="single", *, rows=1, cols=1):
        sns.set_style("whitegrid")

        self.figure = plt.figure(figsize=FIGURE_SIZE_A4_PORTRAIT)

        if self.show_stats_table:
            import matplotlib.gridspec as gridspec

            # Tight vertical coupling: plot + table
            gs = gridspec.GridSpec(
                2, 1,
                height_ratios=[18, 3],  # plot dominates
                hspace=0.01             # 🔑 key line
            )

            plot_gs = gs[0]
            table_ax = self.figure.add_subplot(gs[1])
            table_ax.axis("off")

        else:
            import matplotlib.gridspec as gridspec
            gs = gridspec.GridSpec(1, 1)
            plot_gs = gs[0]

            # ONLY apply margins when no table
            self.figure.subplots_adjust(
                top=0.85,
                bottom=0.15,
                left=0.15,
                right=0.85
            )

        # axes creation
        if layout == "single":
            axes = [self.figure.add_subplot(plot_gs)]

        elif layout == "multipanel":
            sub_gs = plot_gs.subgridspec(rows, cols, hspace=0.4, wspace=0.3)
            axes = [
                self.figure.add_subplot(sub_gs[r, c])
                for r in range(rows)
                for c in range(cols)
            ]
        else:
            raise ValueError(f"Unknown layout: {layout}")

        return axes


    # ---------------- HOOKS ----------------

    def compute_statistics(self, df):
        return {
            col: calculate_descriptive_stats(df[col], column_name=col)
            for col in df.columns
        }

    def draw_boxplot(self, df, ax):
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

    def postprocess(self, axes):
        pass

    # ---------------- MAIN PROCESS ----------------

    def process(self):
        df = pd.DataFrame(self.data.values)

        if self.show_stats_table:
            self.statistics = self.compute_statistics(df)

        axes = self._create_figure(layout="single")
        ax = axes[0]

        self.draw_boxplot(df, ax)

        ax.set_title(self.config.title, fontsize=TITLE_FONT_SIZE, pad=20)
        ax.grid(True, alpha=0.3)

        self.postprocess(axes)

        if self.show_stats_table and self.statistics:
            add_stats_table(
                figure=self.figure,
                stats_data=self.statistics,
                dataset_name=self.data.dataset_name,
                fontsize=9
            )

        plt.close(self.figure)
        return self.figure
    
    def get_statistics(self) -> dict | None:
        """
        Public API for retrieving computed statistics.
        API layer depends on this.
        """
        return self.statistics



