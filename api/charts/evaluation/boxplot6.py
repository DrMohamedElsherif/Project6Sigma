import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
from .base_boxplot import BaseBoxplot
from .boxplot_schemas import BoxplotRequest
from api.charts.constants import TITLE_FONT_SIZE


class Boxplot6(BaseBoxplot):
    request_model = BoxplotRequest
    show_stats_table = True

    def process(self):
        df = pd.DataFrame(self.data.values)

        num_columns = 2
        num_datasets = len(df.columns)
        num_rows = num_datasets // 2 + num_datasets % 2

        self.figure = plt.figure(figsize=(11.7, 8.3))

        for idx, column in enumerate(df.columns, 1):
            ax = self.figure.add_subplot(num_rows, num_columns, idx)
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

        plt.suptitle(self.config.title, fontsize=TITLE_FONT_SIZE)
        plt.tight_layout()
        plt.close(self.figure)
        return self.figure

