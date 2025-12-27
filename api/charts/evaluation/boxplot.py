# boxplot.py

import pandas as pd
from api.charts.evaluation.base_boxplot import BaseBoxplot
from api.charts.evaluation.boxplot_schemas import BoxplotRequest
from api.charts.constants import TITLE_FONT_SIZE


class Boxplot(BaseBoxplot):
    """
    Main Boxplot class handling three variants: single, faceted_by_group, and multipanel_columns.
    Inherits from BaseBoxplot for figure creation, plotting, and statistics integration.

    Attributes:
        request_model (pydantic.BaseModel): Pydantic model for validating input payload (BoxplotRequest).
        statistics (dict): Computed descriptive statistics for each column.
    """
    
    request_model = BoxplotRequest

    def process(self):
        """
        Processes the boxplot generation based on the variant specified in config.

        Steps:
        1. Convert input values to a DataFrame.
        2. Compute descriptive statistics.
        3. Call the appropriate variant-specific plotting method.

        Returns:
            matplotlib.figure.Figure: Final figure with plots and statistics table.

        Raises:
            ValueError: If the variant is unknown.
        """
        df = pd.DataFrame(self.data.values)

        # Compute descriptive statistics for all columns
        self.statistics = self.compute_statistics(df)

        variant = self.config.variant

        # Dispatch to variant-specific plotting method
        if variant == "single":
            return self._single(df)

        if variant == "faceted_by_group":
            return self._faceted_by_group(df)

        if variant == "multipanel_columns":
            return self._multipanel_columns(df)

        raise ValueError(f"Unknown boxplot variant: {variant}")

    # ---------- PLOTS VARIANTS ----------

    def _single(self, df):
        """
        Single boxplot variant.

        Args:
            df (pd.DataFrame): Data to plot.

        Returns:
            matplotlib.figure.Figure: Final figure with plot and statistics table.
        """
        axes = self._create_figure(layout="single")
        ax = axes[0]

        # Draw the boxplot
        self.draw_boxplot(df, ax)
        ax.set_title(self.config.title, fontsize=TITLE_FONT_SIZE)
        ax.grid(True, alpha=0.3)

        return self.finalize()
    
    def _faceted_by_group(self, df):
        """
        Faceted boxplots by row-level group (category-based).

        Behavior:
        - Uses 'categories' from the payload to split the DataFrame into subplots.
        - Each subplot shows boxplots for numeric columns.
        - Categories are NOT used as x-axis values; they only define which data goes into each subplot.

        Args:
            df (pd.DataFrame): Data to plot.

        Returns:
            matplotlib.figure.Figure: Final figure with faceted plots and statistics table.

        Raises:
            ValueError: If categories are missing.
        """
        if not self.data.categories:
            raise ValueError("categories required for by_category variant")

        categories_df = pd.DataFrame(self.data.categories)
        category_col = categories_df.columns[0]
        unique_categories = categories_df[category_col].unique()

        # Create one subplot per unique category
        axes = self._create_figure(
            layout="multipanel",
            rows=1,
            cols=len(unique_categories),
        )
        
        for ax, cat in zip(axes, unique_categories):
            # Filter rows for the current category
            group_data = (
                df.join(categories_df)
                .loc[categories_df[category_col] == cat, df.columns]
            )

            self.draw_boxplot(group_data, ax)
            # ax.set_title(cat)  # Optional: show category name as subplot title
            ax.grid(True, alpha=0.3)

        # Set overall figure title
        self.figure.suptitle(self.config.title, fontsize=TITLE_FONT_SIZE)

        return self.finalize()

    def _multipanel_columns(self, df):
        """
        Multi-panel boxplot where each column in the DataFrame is a separate subplot.

        Layout:
        - 2 columns per row by default.
        - Number of rows determined by the number of columns in the DataFrame.

        Args:
            df (pd.DataFrame): Data to plot.

        Returns:
            matplotlib.figure.Figure: Final figure with multi-panel plots and statistics table.
        """
        num_columns = 2
        num_datasets = len(df.columns)
        num_rows = (num_datasets + 1) // num_columns  # Calculate required rows

        axes = self._create_figure(
            layout="multipanel",
            rows=num_rows,
            cols=num_columns,
        )

        # Draw boxplot for each column in its respective axis
        for ax, column in zip(axes, df.columns):
            self.draw_boxplot(df[[column]], ax)
            ax.set_title(column)
            ax.grid(True, alpha=0.3)

        # Set overall figure title
        self.figure.suptitle(self.config.title, fontsize=TITLE_FONT_SIZE)

        return self.finalize()
