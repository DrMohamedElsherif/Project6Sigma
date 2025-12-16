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
        df = pd.DataFrame(self.data.values)
        categories = self.data.categories

        if categories:
            categories_df = pd.DataFrame(categories)
            unique_categories = categories_df.iloc[:, 0].unique()
            count = len(unique_categories)

            self.figure, axes = plt.subplots(
                1, count, figsize=(11.7, 8.3), sharex=True, sharey=True
            )

            for i, (category, data) in enumerate(
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

            self.figure.suptitle(self.config.title, fontsize=TITLE_FONT_SIZE)
            plt.tight_layout()
            plt.close(self.figure)
            return self.figure

        # fallback to default behavior
        return super().process()



