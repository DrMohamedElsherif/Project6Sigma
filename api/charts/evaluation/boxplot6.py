import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
from .base_boxplot import BaseBoxplot
from .boxplot_schemas import BoxplotRequest
from api.charts.constants import FIGURE_SIZE_A4_PORTRAIT, TITLE_FONT_SIZE
from api.charts.statistics import calculate_descriptive_stats, add_stats_table


class Boxplot6(BaseBoxplot):
    request_model = BoxplotRequest
    show_stats_table = True

    def process(self):
        df = pd.DataFrame(self.data.values)

        self.statistics = self.compute_statistics(df)

        num_columns = 2
        num_datasets = len(df.columns)
        num_rows = num_datasets // 2 + num_datasets % 2

        axes = self._create_figure(
            layout="multipanel",
            rows=num_rows,
            cols=num_columns
        )

        for ax, column in zip(axes, df.columns):
            sns.boxplot(
                data=df[column],
                ax=ax,
                color="#a1d111",
                linewidth=1,
                showcaps=False,
                flierprops={"marker": "x"}
            )
            ax.set_title(column)
            ax.grid(True, alpha=0.3)

        self.figure.suptitle(self.config.title, fontsize=TITLE_FONT_SIZE)

        add_stats_table(
            figure=self.figure,
            stats_data=self.statistics,
            dataset_name=self.data.dataset_name,
            fontsize=9
        )

        plt.close(self.figure)
        return self.figure