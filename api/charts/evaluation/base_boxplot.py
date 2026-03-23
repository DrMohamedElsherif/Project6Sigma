# api/charts/evaluation/base_boxplot.py
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.gridspec as gridspec

from api.schemas import BusinessLogicException
from api.charts.statistics import StatisticsCalculator, add_descriptive_stats_table
from api.charts.constants import FIGURE_SIZE_A4_PORTRAIT, TITLE_FONT_SIZE


class BaseBoxplot:
    """
    Base class for all Boxplot variants. Handles data validation, figure creation,
    statistics calculation, and rendering of boxplots with an integrated statistics table.

    Attributes:
        request_model (pydantic.BaseModel): Pydantic model for validating input payload.
        project (str): Project name from validated data.
        step (str): Step identifier from validated data.
        config (dict): Configuration dictionary from validated data.
        data (dict): Input dataset after validation.
        figure (matplotlib.figure.Figure): Figure object for the boxplot.
        statistics (dict): Computed descriptive statistics for each column.
    """
    
    request_model = None  # Override in child classes with specific Pydantic model

    def __init__(self, data: dict):
        """
        Initializes the BaseBoxplot instance with validated data.

        Args:
            data (dict): Input payload containing project, step, config, and data.

        Raises:
            BusinessLogicException: If validation fails.
        """
        try:
            validated = self.request_model(**data)
            self.project = validated.project
            self.step = validated.step
            self.config = validated.config
            self.data = validated.data
            self.figure = None
            self.statistics = None
            # Add column_names attribute if not present
            if not hasattr(self.data, 'column_names') or not self.data.column_names:
                self.column_names = [f"Column {i+1}" for i in range(len(self.data.values))]
            else:
                self.column_names = self.data.column_names
        except Exception as e:
            raise BusinessLogicException(
                error_code="error_validation",
                field=str(e),
                details={"message": str(e)}
            )

    # ---------------- FIGURE FACTORY ----------------

    def _create_figure(self, layout="single", *, rows=1, cols=1):
        """
        Creates a Matplotlib figure with specified layout and reserves space
        for both plots and statistics table.

        Args:
            layout (str): Layout type ('single' or 'multipanel').
            rows (int): Number of rows for multipanel layout.
            cols (int): Number of columns for multipanel layout.

        Returns:
            list: List of axes for plotting.
        """
        sns.set_style("whitegrid")  # Apply seaborn styling
        self.figure = plt.figure(figsize=FIGURE_SIZE_A4_PORTRAIT)

        # Create a GridSpec with two rows: one for plot, one for stats table
        gs = gridspec.GridSpec(
            2, 1,
            height_ratios=[18, 3],
            hspace=0.01
        )

        plot_gs = gs[0]  # Main plotting area
        table_ax = self.figure.add_subplot(gs[1])
        table_ax.axis("off")  # Hide axes for stats table

        # Single boxplot layout
        if layout == "single":
            axes = [self.figure.add_subplot(plot_gs)]

        # Multipanel layout (subplots for each column)
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
        """
        Compute descriptive statistics for each column in the DataFrame using StatisticsCalculator.

        Args:
            df (pd.DataFrame): DataFrame with columns to analyze.

        Returns:
            dict: Dictionary mapping column names to statistics.
        """
        stats_dict = {}
        for col in df.columns:
            stats_dict[col] = StatisticsCalculator.calculate_descriptive_stats(
                df[col], 
                column_name=col
            )
        return stats_dict

    def draw_boxplot(self, df, ax):
        """
        Draws a boxplot on the specified axis using seaborn.

        Args:
            df (pd.DataFrame): DataFrame containing the data to plot.
            ax (matplotlib.axes.Axes): Axis to draw the boxplot on.
        """
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
        
    def _add_statistics_table(self):
        """Add descriptive statistics table using unified stats module."""
        # Calculate stats for each column if not already computed
        if self.statistics is None:
            df = pd.DataFrame(self.data.values, columns=self.column_names)
            self.statistics = self.compute_statistics(df)
        
        # Add table to figure using the unified function
        add_descriptive_stats_table(
            figure=self.figure,
            stats_data=self.statistics,  # Multi-column format
            dataset_name=self.config.title or "Boxplot Analysis",
            position=(0.13, 0.02),
            fontsize=8
        )

    # ---------------- MAIN PROCESS ----------------

    def finalize(self):
        """
        Adds the statistics table to the figure and closes the plot to avoid display.
        
        Returns:
            matplotlib.figure.Figure: Final figure with plots and statistics table.
        """
        self._add_statistics_table()
        plt.close(self.figure)
        return self.figure




# # base_boxplot.py
# import pandas as pd
# import matplotlib.pyplot as plt
# import seaborn as sns
# import matplotlib.gridspec as gridspec

# from api.schemas import BusinessLogicException
# from api.charts.statistics import calculate_descriptive_stats, add_stats_table
# from api.charts.constants import FIGURE_SIZE_A4_PORTRAIT, TITLE_FONT_SIZE


# class BaseBoxplot:
#     """
#     Base class for all Boxplot variants. Handles data validation, figure creation,
#     statistics calculation, and rendering of boxplots with an integrated statistics table.

#     Attributes:
#         request_model (pydantic.BaseModel): Pydantic model for validating input payload.
#         project (str): Project name from validated data.
#         step (str): Step identifier from validated data.
#         config (dict): Configuration dictionary from validated data.
#         data (dict): Input dataset after validation.
#         figure (matplotlib.figure.Figure): Figure object for the boxplot.
#         statistics (dict): Computed descriptive statistics for each column.
#     """
    
#     request_model = None  # Override in child classes with specific Pydantic model

#     def __init__(self, data: dict):
#         """
#         Initializes the BaseBoxplot instance with validated data.

#         Args:
#             data (dict): Input payload containing project, step, config, and data.

#         Raises:
#             BusinessLogicException: If validation fails.
#         """
#         try:
#             validated = self.request_model(**data)
#             self.project = validated.project
#             self.step = validated.step
#             self.config = validated.config
#             self.data = validated.data
#             self.figure = None
#             self.statistics = None
#         except Exception as e:
#             raise BusinessLogicException(
#                 error_code="error_validation",
#                 field=str(e),
#                 details={"message": str(e)}
#             )

#     # ---------------- FIGURE FACTORY ----------------

#     def _create_figure(self, layout="single", *, rows=1, cols=1):
#         """
#         Creates a Matplotlib figure with specified layout and reserves space
#         for both plots and statistics table.

#         Args:
#             layout (str): Layout type ('single' or 'multipanel').
#             rows (int): Number of rows for multipanel layout.
#             cols (int): Number of columns for multipanel layout.

#         Returns:
#             list: List of axes for plotting.
#         """
#         sns.set_style("whitegrid")  # Apply seaborn styling
#         self.figure = plt.figure(figsize=FIGURE_SIZE_A4_PORTRAIT)

#         # Create a GridSpec with two rows: one for plot, one for stats table
#         gs = gridspec.GridSpec(
#             2, 1,
#             height_ratios=[18, 3],
#             hspace=0.01
#         )

#         plot_gs = gs[0]  # Main plotting area
#         table_ax = self.figure.add_subplot(gs[1])
#         table_ax.axis("off")  # Hide axes for stats table

#         # Single boxplot layout
#         if layout == "single":
#             axes = [self.figure.add_subplot(plot_gs)]

#         # Multipanel layout (subplots for each column)
#         elif layout == "multipanel":
#             sub_gs = plot_gs.subgridspec(rows, cols, hspace=0.4, wspace=0.3)
#             axes = [
#                 self.figure.add_subplot(sub_gs[r, c])
#                 for r in range(rows)
#                 for c in range(cols)
#             ]
        
#         else:
#             raise ValueError(f"Unknown layout: {layout}")

#         return axes

#     # ---------------- HOOKS ----------------

#     def compute_statistics(self, df):
#         """
#         Compute descriptive statistics for each column in the DataFrame.

#         Args:
#             df (pd.DataFrame): DataFrame with columns to analyze.

#         Returns:
#             dict: Dictionary mapping column names to statistics.
#         """
#         return {
#             col: calculate_descriptive_stats(df[col], column_name=col)
#             for col in df.columns
#         }

#     def draw_boxplot(self, df, ax):
#         """
#         Draws a boxplot on the specified axis using seaborn.

#         Args:
#             df (pd.DataFrame): DataFrame containing the data to plot.
#             ax (matplotlib.axes.Axes): Axis to draw the boxplot on.
#         """
#         sns.boxplot(
#             data=df,
#             ax=ax,
#             color="#a1d111",
#             linecolor="black",
#             showcaps=False,
#             linewidth=1,
#             flierprops={"marker": "x"},
#             width=0.3
#         )

#     # ---------------- MAIN PROCESS ----------------

#     def finalize(self):
#         """
#         Adds the statistics table to the figure and closes the plot to avoid display.
        
#         Returns:
#             matplotlib.figure.Figure: Final figure with plots and statistics table.
#         """
#         add_stats_table(
#             figure=self.figure,
#             stats_data=self.statistics,
#             dataset_name=self.data.dataset_name,
#             fontsize=9
#         )
#         plt.close(self.figure)
#         return self.figure
