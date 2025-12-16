import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
from .base_boxplot import BaseBoxplot
from .boxplot_schemas import BoxplotRequest
from api.charts.constants import TITLE_FONT_SIZE

class Boxplot5(BaseBoxplot):
    request_model = BoxplotRequest
    show_stats_table = True

    def process(self):
        sns.set_style("whitegrid")

        df = pd.DataFrame(self.data.values)
        categories = self.data.categories

        # compute statistics
        self.statistics = self.compute_statistics(df)

        if categories:
            categories_df = pd.DataFrame(categories)
            unique_categories = categories_df.iloc[:, 0].unique()
            count = len(unique_categories)

            import matplotlib.gridspec as gridspec

            self.figure = plt.figure(figsize=FIGURE_SIZE_A4_PORTRAIT)
            gs = gridspec.GridSpec(2, 1, height_ratios=[15, 2], hspace=0.05)

            plot_gs = gs[0].subgridspec(1, count, wspace=0.2)
            axes = [self.figure.add_subplot(plot_gs[0, i]) for i in range(count)]

            for i, (_, data) in enumerate(
                df.join(categories_df).groupby(categories_df.columns[0])
            ):
                sns.boxplot(
                    data=data,
                    ax=axes[i],
                    color="#a1d111",
                    linewidth=1,
                    showcaps=False,
                    flierprops={"marker": "x"}
                )
                axes[i].set_xlabel(unique_categories[i])
                axes[i].grid(True, alpha=0.3)

            self.figure.suptitle(self.config.title, fontsize=TITLE_FONT_SIZE)

            add_stats_table(
                figure=self.figure,
                stats_data=self.statistics,
                dataset_name=self.data.dataset_name,
                fontsize=9
            )

            plt.close(self.figure)
            return self.figure

        # fallback to default BaseBoxplot behavior
        return super().process()









