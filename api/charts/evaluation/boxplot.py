
# api/charts/evaluation/boxplot.py

from api.charts.core.base_chart import BaseChart
from api.charts.evaluation.boxplot_schemas import BoxplotRequest
from api.charts.core.styling import draw_histogram

class Boxplot(BaseChart):

    request_model = BoxplotRequest

    def process(self):
        df = self.get_dataframe()

        self.compute_and_store_statistics(df)

        variant = self.config.variant

        if variant == "single":
            return self._single(df)

        if variant == "faceted_by_group":
            return self._faceted(df)

        if variant == "multipanel_columns":
            return self._multipanel(df)

        raise ValueError(f"Unknown variant: {variant}")

    def _single(self, df):
        ax = self.create_figure(layout="single", with_table=True)[0]

        import seaborn as sns
        sns.boxplot(data=df, ax=ax)

        
        ax.set_title(self.config.title)

        return self.finalize(add_stats=True)

    def _faceted(self, df):
        if not self.data.categories:
            raise ValueError("categories required")

        import pandas as pd
        categories_df = pd.DataFrame(self.data.categories)
        cat_col = categories_df.columns[0]
        unique = categories_df[cat_col].unique()

        axes = self.create_figure(
            layout="multipanel",
            rows=1,
            cols=len(unique),
            with_table=True
        )

        import seaborn as sns
        for ax, cat in zip(axes, unique):
            subset = (
                df.join(categories_df)
                .loc[categories_df[cat_col] == cat, df.columns]
            )

            sns.boxplot(data=subset, ax=ax)
            

        self.figure.suptitle(self.config.title)

        return self.finalize(add_stats=True)

    def _multipanel(self, df):
        cols = 2
        rows = (len(df.columns) + 1) // 2

        axes = self.create_figure(
            layout="multipanel",
            rows=rows,
            cols=cols,
            with_table=True
        )

        import seaborn as sns
        for ax, col in zip(axes, df.columns):
            sns.boxplot(data=df[[col]], ax=ax)
            ax.set_title(col)
           

        self.figure.suptitle(self.config.title)

        return self.finalize(add_stats=True)
    

#############################################################################################################

# # api/charts/evaluation/boxplot.py

# import pandas as pd
# from api.charts.evaluation.base_boxplot import BaseBoxplot
# from api.charts.evaluation.boxplot_schemas import BoxplotRequest
# from api.charts.constants import TITLE_FONT_SIZE
# from api.charts.core.styling import style_axis

# class Boxplot(BaseBoxplot):
#     """
#     Main Boxplot class handling three variants: single, faceted_by_group, and multipanel_columns.
#     Inherits from BaseBoxplot for figure creation, plotting, and statistics integration.

#     Attributes:
#         request_model (pydantic.BaseModel): Pydantic model for validating input payload (BoxplotRequest).
#         statistics (dict): Computed descriptive statistics for each column.
#     """
    
#     request_model = BoxplotRequest

#     def process(self):
#         """
#         Processes the boxplot generation based on the variant specified in config.

#         Steps:
#         1. Convert input values to a DataFrame.
#         2. Compute descriptive statistics.
#         3. Call the appropriate variant-specific plotting method.

#         Returns:
#             matplotlib.figure.Figure: Final figure with plots and statistics table.

#         Raises:
#             ValueError: If the variant is unknown.
#         """
#         df = pd.DataFrame(self.data.values)

#         # Compute descriptive statistics for all columns
#         self.statistics = self.compute_statistics(df)

#         variant = self.config.variant

#         # Dispatch to variant-specific plotting method
#         if variant == "single":
#             return self._single(df)

#         if variant == "faceted_by_group":
#             return self._faceted_by_group(df)

#         if variant == "multipanel_columns":
#             return self._multipanel_columns(df)

#         raise ValueError(f"Unknown boxplot variant: {variant}")

#     # ---------- PLOTS VARIANTS ----------

#     def _single(self, df):
#         """
#         Single boxplot variant.

#         Args:
#             df (pd.DataFrame): Data to plot.

#         Returns:
#             matplotlib.figure.Figure: Final figure with plot and statistics table.
#         """
#         axes = self._create_figure(layout="single")
#         ax = axes[0]

#         # Draw the boxplot
#         self.draw_boxplot(df, ax)
#         ax.set_title(self.config.title, fontsize=TITLE_FONT_SIZE)
#         #ax.grid(True, alpha=0.3)
#         style_axis(ax)

#         return self.finalize()
    
#     def _faceted_by_group(self, df):
#         """
#         Faceted boxplots by row-level group (category-based).

#         Behavior:
#         - Uses 'categories' from the payload to split the DataFrame into subplots.
#         - Each subplot shows boxplots for numeric columns.
#         - Categories are NOT used as x-axis values; they only define which data goes into each subplot.

#         Args:
#             df (pd.DataFrame): Data to plot.

#         Returns:
#             matplotlib.figure.Figure: Final figure with faceted plots and statistics table.

#         Raises:
#             ValueError: If categories are missing.
#         """
#         if not self.data.categories:
#             raise ValueError("categories required for by_category variant")

#         categories_df = pd.DataFrame(self.data.categories)
#         category_col = categories_df.columns[0]
#         unique_categories = categories_df[category_col].unique()

#         # Create one subplot per unique category
#         axes = self._create_figure(
#             layout="multipanel",
#             rows=1,
#             cols=len(unique_categories),
#         )
        
#         for ax, cat in zip(axes, unique_categories):
#             # Filter rows for the current category
#             group_data = (
#                 df.join(categories_df)
#                 .loc[categories_df[category_col] == cat, df.columns]
#             )

#             self.draw_boxplot(group_data, ax)
#             # ax.set_title(cat)  # Optional: show category name as subplot title
#             ax.grid(True, alpha=0.3)

#         # Set overall figure title
#         self.figure.suptitle(self.config.title, fontsize=TITLE_FONT_SIZE)

#         return self.finalize()

#     def _multipanel_columns(self, df):
#         """
#         Multi-panel boxplot where each column in the DataFrame is a separate subplot.

#         Layout:
#         - 2 columns per row by default.
#         - Number of rows determined by the number of columns in the DataFrame.

#         Args:
#             df (pd.DataFrame): Data to plot.

#         Returns:
#             matplotlib.figure.Figure: Final figure with multi-panel plots and statistics table.
#         """
#         num_columns = 2
#         num_datasets = len(df.columns)
#         num_rows = (num_datasets + 1) // num_columns  # Calculate required rows

#         axes = self._create_figure(
#             layout="multipanel",
#             rows=num_rows,
#             cols=num_columns,
#         )

#         # Draw boxplot for each column in its respective axis
#         for ax, column in zip(axes, df.columns):
#             self.draw_boxplot(df[[column]], ax)
#             ax.set_title(column)
#             ax.grid(True, alpha=0.3)

#         # Set overall figure title
#         self.figure.suptitle(self.config.title, fontsize=TITLE_FONT_SIZE)

#         return self.finalize()
