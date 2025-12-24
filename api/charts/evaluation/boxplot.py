
# boxplot.py

import pandas as pd
from api.charts.evaluation.base_boxplot import BaseBoxplot
from api.charts.evaluation.boxplot_schemas import BoxplotRequest
from api.charts.constants import TITLE_FONT_SIZE


class Boxplot(BaseBoxplot):
    request_model = BoxplotRequest

    def process(self):
        df = pd.DataFrame(self.data.values)

        # stats computed
        self.statistics = self.compute_statistics(df)

        variant = self.config.variant

        if variant == "single":
            return self._single(df)

        if variant == "by_category":
            return self._by_category(df)

        if variant == "multipanel_columns":
            return self._multipanel_columns(df)

        raise ValueError(f"Unknown boxplot variant: {variant}")

    # ---------- PLOTS VARIANTS ----------

    def _single(self, df):
        axes = self._create_figure(layout="single")
        ax = axes[0]

        self.draw_boxplot(df, ax)
        ax.set_title(self.config.title, fontsize=TITLE_FONT_SIZE)
        ax.grid(True, alpha=0.3)

        return self.finalize()

    def _by_category(self, df):
        if not self.data.categories:
            raise ValueError("categories required for by_category variant")

        categories_df = pd.DataFrame(self.data.categories)
        category_col = categories_df.columns[0]
        unique_categories = categories_df[category_col].unique()

        axes = self._create_figure(
            layout="multipanel",
            rows=1,
            cols=len(unique_categories),
        )

        for ax, cat in zip(axes, unique_categories):
            group_data = df.join(categories_df)[categories_df[category_col] == cat]
            self.draw_boxplot(group_data, ax)
            ax.set_xlabel(cat)
            ax.grid(True, alpha=0.3)

        self.figure.suptitle(self.config.title, fontsize=TITLE_FONT_SIZE)

        return self.finalize()

    def _multipanel_columns(self, df):
        num_columns = 2
        num_datasets = len(df.columns)
        num_rows = (num_datasets + 1) // num_columns

        axes = self._create_figure(
            layout="multipanel",
            rows=num_rows,
            cols=num_columns,
        )

        for ax, column in zip(axes, df.columns):
            self.draw_boxplot(df[[column]], ax)
            ax.set_title(column)
            ax.grid(True, alpha=0.3)

        self.figure.suptitle(self.config.title, fontsize=TITLE_FONT_SIZE)

        return self.finalize()