import io
import math
import numpy as np
import pandas as pd
import scipy.stats as stats
import scipy.optimize as optimize
import matplotlib.pyplot as plt
import seaborn as sns
from pydantic import BaseModel, Field, conlist, field_validator
from matplotlib.backends.backend_pdf import PdfPages
from typing import List, Dict, Optional, Union
from api.schemas import BusinessLogicException

from ...utils.pdf_utils import add_header_or_footer_to_a4_portrait

header_image_path = 'assets/img/Header.png'
footer_image_path = 'assets/img/Footer.png'

from ...utils.mpl_table_utils import merge_mpl_table_cells as mergecells

class TwoFtestConfig(BaseModel):
    title: str
    alphalevel: float
    power: Optional[float] = None

class TwoFtestDataSeparate(BaseModel):
    """
    Data in separate columns, e.g.:
    {
      "values": {
        "Group1": [1.01, 1.02, ...],
        "Group2": [1.03, 1.04, ...]
      }
    }
    """
    values: Dict[str, conlist(float, min_length=1)] = Field(..., min_length=1) # type: ignore

    @field_validator('values')
    def check_two_groups_only(cls, v):
        if len(v.keys()) != 2:
            raise BusinessLogicException(
                error_code="error_data_size",
                field="values",
                details={"message": "Exactly two data series are required"}
            )
        # Check each dataset for finite values
        for group, arr in v.items():
            if any(not np.isfinite(x) for x in arr):
                raise ValueError(f"Group '{group}' contains NaN or infinite values.")
        return v

class TwoFtestDataCombined(BaseModel):
    """
    Data in one column + group labels in another column, e.g.:
    {
      "values": [1.02, 1.03, ...],
      "groups": ["Group1", "Group2", ...]
    }
    """
    values: conlist(float, min_length=1) # type: ignore
    groups: conlist(str, min_length=1) # type: ignore

    @field_validator('groups')
    def check_same_length(cls, groups, values):
        if 'values' not in values:
            return groups
        if len(groups) != len(values['values']):
            raise BusinessLogicException(
                error_code="error_column_length",
                field="values",
                details={"message": "Values and groups must have the same length"}
            )
        return groups

    @field_validator('groups')
    def check_two_distinct_groups(cls, groups):
        distinct_groups = set(groups)
        if len(distinct_groups) != 2:
            raise BusinessLogicException(
                error_code="error_group_identifiers",
                field="groups",
                details={"message": "Exactly two different group identifiers are required"}
            )
        return groups

    @field_validator('values')
    def check_finite_values(cls, v):
        if any(not np.isfinite(x) for x in v):
            raise ValueError("Values contain NaN or infinite values.")
        return v

TwoFtestDataUnion = Union[TwoFtestDataSeparate, TwoFtestDataCombined]

class TwoFtestRequest(BaseModel):
    project: str
    projectNumber: Optional[str] = None
    step: str
    config: TwoFtestConfig
    data: TwoFtestDataUnion

class TwoFtest:
    """
    TwoFtest class for performing F-tests to compare variances between two data sources.
    This class handles the validation, processing, and visualization of F-test results
    comparing the standard deviations (variances) of two data sets. It generates a comprehensive
    PDF report with statistical analysis, visualizations, and power calculations.
    Parameters
    ----------
    data : dict
        A dictionary containing the following keys:
        - project: Project information
        - step: Step information
        - config: Configuration settings including title, alpha level, and power
        - data: The datasets to compare with their respective values
    Attributes
    ----------
    project : dict
        Project information from the input data
    step : dict
        Step information from the input data
    config : dict
        Configuration settings including title, alpha level, and power
    data : dict
        The datasets to be analyzed
    Methods
    -------
    process() -> io.BytesIO
        Processes the data, performs F-tests, and generates a PDF report with:
        - F-test results (Bonett and Levene methods)
        - Descriptive statistics for both datasets
        - Time series plots with outliers highlighted
        - Power analysis and detectable differences
        - Histograms, error bars, and box plots
        Returns:
            io.BytesIO: A BytesIO object containing the generated PDF report
    Raises
    ------
    BusinessLogicException
        If the input data validation fails
    """
    def __init__(self, data:dict):
        try:
            validated_data = TwoFtestRequest(**data)
            self.project = validated_data.project
            self.step = validated_data.step
            self.config = validated_data.config
            self.data = validated_data.data
            self.projectNumber = validated_data.projectNumber
        except Exception as e:
            raise BusinessLogicException(
                error_code="error_validation",
                field=str(e),
                details={"message": f"Invalid or missing field: {str(e)}"}
            )
        
    def _convert_combined_to_separate(self, combined: TwoFtestDataCombined) -> TwoFtestDataSeparate:
        """
        Converts combined data into the separate format for easier analysis.
        """
        group_map: Dict[str, List[float]] = {}
        for val, grp in zip(combined.values, combined.groups):
            if grp not in group_map:
                group_map[grp] = []
            group_map[grp].append(val)
        return TwoFtestDataSeparate(values=group_map)

    def process(self):
        title = self.config.title
        alpha = self.config.alphalevel
        power = self.config.power
        source_1 = list(self.data.values.keys())[0]
        source_2 = list(self.data.values.keys())[1]
        # Create two dataframes for the two sources
        data_keys = list(self.data.values.keys())
        df1 = pd.DataFrame(self.data.values[source_1], columns=[data_keys[0]])
        df2 = pd.DataFrame(self.data.values[source_2], columns=[data_keys[1]])
        # Combine the two dataframes
        df_combined = pd.concat([df2, df1], axis=1)
        projectNumber = self.projectNumber

        descriptive_statistics, f_statistics = _calculate_f_statistics(df1, source_1, df2, source_2, alpha)

        detectable_differences = _calculate_detectable_stddev_ratio(descriptive_statistics["N"][0], descriptive_statistics["N"][1], alpha=alpha)

        if power is not None:
            required_sample_sizes = _sample_size_f_test(power, alpha)
            power_sample_size = _calculate_power_variance_test(n=descriptive_statistics['N'][1], expected_stddev=descriptive_statistics['StDev'][0], target_stddev=descriptive_statistics['StDev'][1], alpha = alpha)

        if f_statistics["Bonett"]['lower_ci'] <= 1.0 <= f_statistics["Bonett"]['upper_ci']:
            difference_string = f"The standard deviation from ”{source_1}” is\nnot significantly different from ”{source_2}”."
            difference_color = "#d6ed5f"
        else:
            difference_string = f"The standard deviation from ”{source_1}” is\n significantly different from ”{source_2}”."
            difference_color = "#9cc563"

        pdf_io = io.BytesIO()

        with PdfPages(pdf_io) as pdf:
            # NEW PDF PAGE - T-Test results, Descriptive Statistics, Data Time Series
            fig, axes = plt.subplot_mosaic([
                ["T-Test Results", "T-Test Results"],
                ["Descriptive Statistics", "Descriptive Statistics"],
                ["TS1", "TS2"],         # Time Series Plots for each dataset
                ["Chance", "Detectable"]],    # Chance and Detectable Difference
                figsize=(8.27, 11.69), dpi=300)  # A4 size in inches
            #fig.subplots_adjust(hspace=0.4)  # Increase hspace to add more space between charts
            fig.suptitle(title, fontsize=14, y=0.92, ha='left', x=0.1)

            add_header_or_footer_to_a4_portrait(fig, header_image_path, position='header')
            add_header_or_footer_to_a4_portrait(fig, footer_image_path, position='footer', page_number=1, total_pages=2, projectNumber=projectNumber)

            # Define the colors + font size
            edgecolor = "#7c7c7c"
            grey = "#e7e6e6"
            green_table = "#9cc563"
            lightgreen_table = "#d6ed5f"
            font_size=7


            # T-Test Results
            ax = axes["T-Test Results"]
            ax.axis("off")
            # Define table data
            cellText = [
                ["Configuration", "", "Hypothesis", "", "", "", ""],
                ["Each sample in its own column", "", f"$H_{0}: \sigma_{1}$ / $\sigma_{2}$ = 1", "Method*", "Test statistic", "df", "p-Value*"],
                ["\nTest-Setup", "\nDifferent", f"\n$H_{0}: \sigma_{1}$ / $\sigma_{2}$ ≠ 1", "Bonett", f"{f_statistics['Bonett']['test_statistic']:.2f}", "-", f"{f_statistics['Bonett']['p_value']:.3f}"],
                ["", "", "", "Levene", f"{f_statistics['Levene']['test_statistic']:.2f}", f"{f_statistics['deg_freedom']}", f"{f_statistics['Levene']['p_value']:.3f}"],
                ["Sample 1", f"{source_1}", "", "", "", "", ""],
                ["Sample 2", f"{source_2}", "", "", "", "", ""],
                ["\nα-Level", f"\n {alpha}", "", "", "Bonett CI", "", f"({f_statistics['Bonett']['lower_ci']};{f_statistics['Bonett']['upper_ci']})"],
                ["", "", "", "", "", "", ""],
                ["Interested\ndifference**", "-", "", f"{difference_string}", "", "", ""],
                ["", "", "", "", "", "", ""]
            ]
            # Define column widths
            col_widths = [0.15, 0.2, 0.15, 0.1, 0.15, 0.1, 0.15]
            # Background color for the table
            bg_colors = [
                ["#e7e6e6", "#e7e6e6", "#e7e6e6", "#e7e6e6", "#e7e6e6", "#e7e6e6", "#e7e6e6"],
                ["#ffffff", "#ffffff", lightgreen_table, grey, grey, grey, grey],
                ["#ffffff", "#ffffff", green_table, "#ffffff", "#ffffff", "#ffffff", difference_color],
                ["#ffffff", "#ffffff", green_table, "#ffffff", "#ffffff", "#ffffff", difference_color],
                ["#ffffff", "#ffffff", "#ffffff", grey, grey, grey, grey],
                ["#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff"],
                ["#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff"],
                ["#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff"],
                ["#ffffff", "#ffffff", "#ffffff", difference_color, difference_color, difference_color, difference_color],
                ["#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff"]
            ]

            # Create table with background colors only and remove edgecolor
            table_bg = ax.table(bbox=[0, 0, 1, 1], cellColours=bg_colors, colWidths=col_widths)
            for cell in table_bg._cells.values():
                cell.set_edgecolor("none")

            # Adjust row heights for background color table
            row_heights = {2: 0.05, 3: 0.05, 6: 0.05, 7: 0.05, 8: 0.1, 9: 0.1}
            for row, height in row_heights.items():
                for col in range(7):
                    table_bg[(row, col)].set_height(height)

            # Recreate the table layout with "none" as the color
            bg_none = [
                ["none", "none", "none", "none", "none", "none", "none"],
                ["none", "none", "none", "none", "none", "none", "none"],
                ["none", "none", "none", "none", "none", "none", "none"],
                ["none", "none", "none", "none", "none", "none", "none"],
                ["none", "none", "none", "none", "none", "none", "none"],
                ["none", "none", "none", "none", "none", "none", "none"],
                ["none", "none", "none", "none", "none", "none", "none"],
                ["none", "none", "none", "none", "none", "none", "none"],
                ["none", "none", "none", "none", "none", "none", "none"],
                ["none", "none", "none", "none", "none", "none", "none"]
            ]

            # Create the table with the data + "none" as the color
            table = ax.table(
                bbox=[0, 0, 1, 1],
                cellText=cellText,
                colWidths=col_widths,
                loc='upper left',
                cellLoc='center',
                cellColours=bg_none          
            )
            # Set the font size for the table
            table.auto_set_font_size(False)
            table.set_fontsize(font_size)

            # Change edgecolor of table
            for cell in table._cells.values():
                cell.set_edgecolor("#7c7c7c")
                cell.set_linewidth(0.5)
            # Merge the cells of the table
            mergecells(table, [(0, 0), (0, 1)]) #Passt
            mergecells(table, [(0, 3), (0, 4), (0, 5), (0, 6)]) #Passt
            mergecells(table, [(2, 0), (3, 0)]) #Passt
            mergecells(table, [(2, 1), (3, 1)]) #Passt
            mergecells(table, [(1, 0), (1, 1)]) #Passt
            mergecells(table, [(2, 2), (3, 2)])
            mergecells(table, [(6, 0) , (7, 0)])
            mergecells(table, [(6, 1) , (7, 1)])
            mergecells(table, [(4, 2), (5, 2), (6, 2), (7, 2), (8, 2)])
            mergecells(table, [(4, 3), (4, 4), (4, 5), (4, 6)])
            mergecells(table, [(5, 3), (5, 4)])
            mergecells(table, [(5, 5), (5, 6)])
            mergecells(table, [(6, 3), (6, 4)])
            mergecells(table, [(6, 5), (6, 6)])
            mergecells(table, [(7, 3), (7, 4)])
            mergecells(table, [(7, 5), (7, 6)])
            mergecells(table, [(8, 3), (8, 4), (8, 5), (8, 6)])
            mergecells(table, [(9, 0), (9, 1), (9, 2), (9, 3), (9, 4), (9, 5), (9, 6)])

            # Fix the cells, that cannot be defined before mergecells
            table.get_celld()[9, 0].set_fontsize(5)
            
            
            for row, height in row_heights.items():
                for col in range(7):
                    table[(row, col)].set_height(height)

            # Add text to the table
            cell_text_centered_1 = table.get_celld()[(0, 4)]
            cell_text_centered_1.set_text_props(
                text='Results',
                x=1.5,
                y=0.5,
                visible=True,
                ha='center'
            )
            cell_text_centered_2 = table.get_celld()[(5, 4)]
            cell_text_centered_2.set_text_props(
                text=r"$\sigma_{1}$ / $\sigma_{2}$ ",
                x=1.5,
                y=0.5,
                visible=True,
                ha='right'
            )
            cell_text_centered_3 = table.get_celld()[(5, 5)]
            cell_text_centered_3.set_text_props(
                text=f"{f_statistics['ratio_sigma']:.5f}",
                x=1.5,
                y=0.5,
                visible=True,
                ha='right'
            )
            cell_text_centered_4 = table.get_celld()[(6, 4)]
            cell_text_centered_4.set_text_props(
                text='90% CI (Bonett)',
                x=1.5,
                y=0.5,
                visible=True,
                ha='right'
            )
            cell_text_centered_5 = table.get_celld()[(7, 4)]
            cell_text_centered_5.set_text_props(
                text='90% CI (Levene)',
                x=1.5,
                y=0.5,
                visible=True,
                ha='right'
            )
            cell_text_centered_6 = table.get_celld()[(6, 5)]
            cell_text_centered_6.set_text_props(
                text=f"({f_statistics['Bonett']['lower_ci']:.3f};{f_statistics['Bonett']['upper_ci']:.3f})",
                x=1.5,
                y=0.5,
                visible=True,
                ha='left'
            )
            cell_text_centered_7 = table.get_celld()[(7, 5)]
            cell_text_centered_7.set_text_props(
                text=f"({f_statistics['Levene']['lower_ci']:.3f};{f_statistics['Levene']['lower_ci']:.3f})",
                x=1.5,
                y=0.5,
                visible=True,
                ha='left'
            )
            cell_text_small = table.get_celld()[(9, 0)]
            cell_text_small.set_text_props(
                text= '* Method: The Bonett method is valid for any continuous distribution, while the chi-square method is valid only for the normal distribution.\n** If the p-value is less than the α-level, then H0 is to be rejected and the alternative hypothesis H1 is to be accepted\n*** Optional: What difference between the two standard deviations has a practical value? (Power and sample size)',
                visible=True,
                color='grey',
                ha='left'
            )
            bold_text = [(1, 3), (1, 4), (1, 5), (1, 6), (2, 1)]
            for row, col in bold_text:
                cell = table.get_celld()[(row, col)]
                cell.set_text_props(weight='bold')

            left_text = [(1, 0), (5, 3), (6, 3), (8, 3)]
            for row, col in left_text:
                cell = table.get_celld()[(row, col)]
                cell.set_text_props(ha='left')

            right_text = [(0, 0), (4, 3)]
            for row, col in right_text:
                cell = table.get_celld()[(row, col)]
                cell.set_text_props(ha='right')

            # Modify specific cell edges to be invisible
            power_and_detected = axes["Chance"]
            for key, cell in table.get_celld().items():
                row, col = key
                # Define rows and columns where we need to remove borders
                border_pairs = [
                    # Format: (row1, row2, col, border_to_remove_from_row1, border_to_remove_from_row2)
                    (5, 6, 0, 'B', 'T'),
                    (6, 7, 0, 'B', 'T'),
                    (5, 6, 3, 'B', 'T'),
                    (6, 7, 3, 'B', 'T'),
                    (5, 6, 4, 'B', 'T'),
                    (6, 7, 4, 'B', 'T'),
                    (5, 6, 5, 'B', 'T'),
                    (6, 7, 5, 'B', 'T'),
                    (5, 6, 6, 'B', 'T'),
                    (6, 7, 6, 'B', 'T')
                ]

                # Apply border removals
                for row1, row2, col, border1, border2 in border_pairs:
                    if (row1, col) in table.get_celld():
                        cell = table.get_celld()[(row1, col)]
                        cell.visible_edges = cell.visible_edges.replace(border1, '')
                    
                    if (row2, col) in table.get_celld():
                        cell = table.get_celld()[(row2, col)]
                        cell.visible_edges = cell.visible_edges.replace(border2, '')

            # Descriptive Statistics
            ax = axes["Descriptive Statistics"]
            ax.axis("off")
            ax.set_title("Descriptive Statistics", loc="left", pad=-50, y=1.02)
            descriptive_table_widths = [0.18, 0.06, 0.11, 0.11, 0.19]
            cellText = list(zip(*descriptive_statistics.values()))
            descriptive_table = ax.table(
                cellText=cellText,
                colLabels=list(descriptive_statistics.keys()),
                cellLoc="center",
                loc="upper left",
                colWidths=descriptive_table_widths,
                bbox=[0, 0.3, 0.6, 0.3]
            )
            # Set the font size for the table
            descriptive_table.auto_set_font_size(False)
            descriptive_table.set_fontsize(font_size)

            # Change edgecolor of table
            for cell in descriptive_table._cells.values():
                cell.set_edgecolor(edgecolor)
                cell.set_linewidth(0.5)
            
            # Set the top row color to #e7e6e6
            for cell in descriptive_table._cells:
                if cell[0] == 0:
                    descriptive_table._cells[cell].set_facecolor(grey)



            # Time Series Plots
            # Time Series 1
            ax = axes["TS1"]
            ax.plot(df1, color='black', marker='o', linewidth=0.5)
            ax.set_title("Data Time Series", loc='left')
            ax.hlines(descriptive_statistics['Mean'][0], 0, descriptive_statistics['N'][0], colors='grey', linestyles='dashed', alpha=0.7)
            ax.text(0.2, 0.1, source_1, transform=ax.transAxes, fontsize=font_size, verticalalignment='top', horizontalalignment='center')

            # Mark outliers of TS1 data
            Q1_TS1 = df1.quantile(0.25)
            Q3_TS1 = df1.quantile(0.75)
            IQR_TS1 = Q3_TS1 - Q1_TS1
            lower_bound_TS1 = Q1_TS1 - 1.5 * IQR_TS1
            upper_bound_TS1 = Q3_TS1 + 1.5 * IQR_TS1

            for i, value in enumerate(df1.values):
                if value < lower_bound_TS1.values or value > upper_bound_TS1.values:
                    ax.plot(i, value, color='red', marker='s')

            # Time Series 2
            ax = axes["TS2"]
            ax.plot(df2, color='black', marker='o', linewidth=0.5)
            ax.hlines(descriptive_statistics['Mean'][1], 0, descriptive_statistics['N'][1], colors='grey', linestyles='dashed', alpha=0.7)
            ax.set_yticks([])
            ax.text(0.2, 0.1, source_2, transform=ax.transAxes, fontsize=font_size, verticalalignment='top', horizontalalignment='center')

            # Mark outliers of TS2 data
            Q1_TS2 = df2.quantile(0.25)
            Q3_TS2 = df2.quantile(0.75)
            IQR_TS2 = Q3_TS2 - Q1_TS2
            lower_bound_TS2 = Q1_TS2 - 1.5 * IQR_TS2
            upper_bound_TS2 = Q3_TS2 + 1.5 * IQR_TS2

            for i, value in enumerate(df2.values):
                if value < lower_bound_TS2.values or value > upper_bound_TS2.values:
                    ax.plot(i, value, color='red', marker='s')

            # Set y-limits for both plots
            max_y = max(df1.max().values[0], df2.max().values[0])
            min_y = min(df1.min().values[0], df2.min().values[0])
            y_margin = 0.2 * (max_y - min_y)
            axes["TS1"].set_ylim(min_y - y_margin, max_y + y_margin)
            axes["TS2"].set_ylim(min_y - y_margin, max_y + y_margin)

            # Chance of Detecting a Difference table
            ax = axes["Chance"]
            ax.axis("off")
            ax.set_title("Power and Detectable Differences", loc='left', pad=-50, y=1.2)

            if power is not None:
                ax.set_title(f"What is the chance of detecting a difference of {power}?", pad=-70, y=1.02, fontsize=font_size)

                if power_sample_size < 0.60:
                    observed_difference_color = "#c00000"
                    observed_difference_text_color = "#ffffff"
                elif 0.60 <= power_sample_size <= 0.90:
                    observed_difference_color = "#f9b002"
                    observed_difference_text_color = "#000000"
                else:
                    observed_difference_color = "#a7c315"
                    observed_difference_text_color = "#000000"

                cellText = [
                    ["60%", "", "90%"],
                    ["", "", ""],
                    [f"{detectable_differences[60][1]:.1f}", "", f"{detectable_differences[60][1]:.1f}"],
                    ["Sample size", "Chance of Detecting a difference", ""],
                    [f"{descriptive_statistics['N'][0]}", "", f"{power_sample_size*100:.1f}%"]
                ]
            
            else:

                observed_difference = round(f_statistics['ratio_sigma']*100, 0)

                if observed_difference < detectable_differences[60][1]:  # Less than 60% power
                    observed_difference_interval = "<60%"
                    observed_difference_color = "#c00000"
                    observed_difference_text_color = "#ffffff"
                elif detectable_differences[60][1] <= observed_difference < detectable_differences[70][1]:  # Between 60-70% power
                    observed_difference_interval = "60%-70%"
                    observed_difference_color = "#f9b002"
                    observed_difference_text_color = "#000000"
                elif detectable_differences[70][1] <= observed_difference < detectable_differences[80][1]:  # Between 70-80% power
                    observed_difference_interval = "70%-80%"
                    observed_difference_color = "#f9b002"
                    observed_difference_text_color = "#000000"
                elif detectable_differences[80][1] <= observed_difference < detectable_differences[90][1]:  # Between 80-90% power
                    observed_difference_interval = "80%-90%"
                    observed_difference_color = "#f9b002"
                    observed_difference_text_color = "#000000"
                else:  # Greater than 90% power
                    observed_difference_interval = ">90%"
                    observed_difference_color = "#a7c315"
                    observed_difference_text_color = "#000000"

                ax.set_title("What is the chance of detecting a difference?", loc="center", pad=-70, y=1.02, fontsize=font_size)

                cellText = [
                    ["60%", "", "90%"],
                    ["", "", ""],
                    [f"{detectable_differences[60][1]:.1f}%", "% Difference", f"{detectable_differences[90][1]:.1f}%"],
                    ["Sample size", "Observed difference", ""],
                    [f"{descriptive_statistics['N'][0]}", "", f"{observed_difference_interval}"]
                ]

            bg_colors = [
                [grey, grey, grey],
                ["#c00000", "#f9b002", "#a7c315"],
                ["#ffffff", "#ffffff", "#ffffff"],
                [grey, grey, grey],
                ["#ffffff", "#ffffff", observed_difference_color]
            ]

            table_bg = ax.table(bbox=[0, 0, 1, 0.5], cellColours=bg_colors, colWidths=[0.18, 0.44, 0.20])
            for cell in table_bg._cells.values():
                cell.set_edgecolor("none")

            bg_none = [
                ["none", "none", "none"],
                ["none", "none", "none"],
                ["none", "none", "none"],
                ["none", "none", "none"],
                ["none", "none", "none"]
            ]

            table = ax.table(
                bbox=[0, 0, 1, 0.5],
                cellText=cellText,
                cellLoc='center',
                loc='center',
                colWidths=[0.12, 0.17, 0.12],
                cellColours=bg_none
            )

            table[(4, 2)].set_text_props(color=observed_difference_text_color)

            # Set table font size
            table.auto_set_font_size(False)
            table.set_fontsize(font_size)

            # Add only outer edges to the table
            for key, cell in table.get_celld().items():
                row, col = key
                
                # Remove all edges first
                cell.visible_edges = ""
                
                # Add edges only for cells on the outside
                if row == 0:  # Top row
                    cell.visible_edges += "T"
                if row == 4:  # Bottom row
                    cell.visible_edges += "B"
                if col == 0:  # Left column
                    cell.visible_edges += "L"
                if col == 2:  # Right column
                    cell.visible_edges += "R"
                    
                # Adjust text positioning
                if key == (0, 0):
                    cell.set_text_props(ha='right')
                if key == (0, 2):
                    cell.set_text_props(ha='left')
                if key == (2, 0):
                    cell.set_text_props(ha='right')
                if key == (2, 2):
                    cell.set_text_props(ha='left')
                if key == (3, 1):
                    cell.set_text_props(ha='left')
                
                # Set edge color
                cell.set_edgecolor(edgecolor)
                cell.set_linewidth(0.5)




            # Difference detectable with sample size N table
            ax = axes["Detectable"]
            ax.axis("off")

            if power is not None:

                ax.set_title(f"What sample size is required to detect a difference\nof {power}?", loc='center', pad=-70, y=1.02, fontsize=font_size)

                table_data = [
                    ["Sample size", "Power"],
                    [f"{required_sample_sizes[0.6]}", "60%"],
                    [f"{required_sample_sizes[0.7]}", "70%"],
                    [f"{required_sample_sizes[0.8]}", "80%"],
                    [f"{required_sample_sizes[0.9]}", "90%"]
                ]

            else:
                ax.set_title("Detectable differences with sample sizes of N", loc='center', pad=-70, y=1.02, fontsize=font_size)

                table_data = [
                    ["% Difference", "Power"],
                    [f"{detectable_differences[60][1]:.1f}%", "60%"],
                    [f"{detectable_differences[70][1]:.1f}%", "70%"],
                    [f"{detectable_differences[80][1]:.1f}%", "80%"],
                    [f"{detectable_differences[90][1]:.1f}%", "90%"]
                ]

            table = ax.table(
                bbox=[0, 0, 1, 0.5],
                cellText=table_data,
                cellLoc='center',
                loc='center'
            )
            # Set the font size for the table
            table.auto_set_font_size(False)
            table.set_fontsize(font_size)

            # Change edgecolor of table
            for cell in table._cells.values():
                cell.set_edgecolor(edgecolor)
                cell.set_linewidth(0.5)

            # Set the top row color to grey
            for cell in table._cells:
                if cell[0] == 0:
                    table._cells[cell].set_facecolor(grey)

            pdf.savefig(fig)
            plt.close(fig)

            # NEW PDF PAGE - Histogram and Errorbar
            fig, axs = plt.subplot_mosaic([
                ["Hist1"],
                ["Hist2"],
                ["Errorbar1"],
                ["Errorbar2"],
                ["Boxplots"]],
                figsize=(8.27, 11.69), gridspec_kw={'height_ratios': [3, 3, 1, 1, 1]}, dpi=300)  # A4 size in inches
            fig.subplots_adjust(hspace=0.8)  # Increase hspace to add more space between charts
            # fig.suptitle(title, fontsize=16, weight='bold', y=0.94)

            add_header_or_footer_to_a4_portrait(fig, header_image_path, position='header')
            add_header_or_footer_to_a4_portrait(fig, footer_image_path, position='footer', page_number=2, total_pages=2, projectNumber=projectNumber)


            # Plot for the Histograms
            # Histogram 1
            ax = axs["Hist1"]
            ax.hist(df1[source_1], color='#95b92a', edgecolor='black', zorder=3, label=f"{source_1}")
            ax.set_title(f"{source_1}", fontsize=10)
            ax.set_ylabel("Frequency")
            ax.grid(True, zorder=0, alpha=0.3)
            # Remove x tick labels but keep the grid lines in Histogram 1
            ax.tick_params(axis='x', which='both', labelbottom=False)
            ax.xaxis.grid(True, alpha=0.3)

            # Histogram 2
            ax = axs["Hist2"]
            ax.hist(df2[source_2], color='#95b92a', edgecolor='black', zorder=3, label=f"{source_2}")
            ax.set_title(f"{source_2}", fontsize=10)
            ax.set_ylabel("Frequency")
            ax.grid(True, zorder=0, alpha=0.3)
            ax.set_position([0.125, 0.5, 0.775, 0.2])  # Adjust the position to move it closer to the first plot

            # Set the same x-limits for both histograms
            hist_min = min(df1[source_1].min(), df2[source_2].min())
            hist_max = max(df1[source_1].max(), df2[source_2].max())
            hist_margin = (hist_max - hist_min) * 0.1
            axs["Hist1"].set_xlim(hist_min - hist_margin, hist_max + hist_margin)
            axs["Hist2"].set_xlim(hist_min - hist_margin, hist_max + hist_margin)

            # Set the same y-limits for both histograms
            hist_max = max(axs["Hist1"].get_ylim()[1], axs["Hist2"].get_ylim()[1])
            axs["Hist1"].set_ylim(0, hist_max)
            axs["Hist2"].set_ylim(0, hist_max)

            # Plot for the Errorbars
            # Bonett and Levene Errorbars
            ax = axs["Errorbar1"]
            ax.set_title(f"95% CI for σ({source_1}) / σ({source_2})", fontsize=10)
            ax.errorbar(x=f_statistics['ratio_sigma'], y=1, xerr=[[f_statistics['ratio_sigma'] - f_statistics['Bonett']['lower_ci']], [f_statistics['Bonett']['upper_ci'] - f_statistics['ratio_sigma']]], fmt='o', color='#95b92a', capsize=3, lw=0.7, markersize=3)
            ax.errorbar(x=f_statistics['ratio_sigma'], y=0, xerr=[[f_statistics['ratio_sigma'] - f_statistics['Levene']['lower_ci']], [f_statistics['Levene']['upper_ci'] - f_statistics['ratio_sigma']]], fmt='o', color='#95b92a', capsize=3, lw=0.7, markersize=3)
            ax.vlines(1, -1, 2, colors='grey', linestyles='dashed', alpha=0.7)
            ax.set_ylim(-0.9, 1.9)
            labels = [item.get_text() for item in ax.get_yticklabels()]
            labels[0] = labels[3] = ''
            labels[1] = 'Levene'
            labels[2] = 'Bonett'
            ax.set_yticks([-1, 0, 1, 2])
            ax.set_yticklabels(labels, fontsize=10)
            ax.grid(True, axis='x', zorder=0, alpha=0.7)
            ax.set_position([0.3, 0.4, 0.6, 0.05])

            # Samples sigma Errorbars
            ax = axs["Errorbar2"]
            ax.set_title("95% CI for σ", fontsize=10)
            ax.errorbar(x=descriptive_statistics['StDev'][1], y=0, xerr=[[descriptive_statistics['StDev'][1] - f_statistics['sigma_2_ll']], [f_statistics['sigma_2_ul'] - descriptive_statistics['StDev'][1]]], fmt='o', color='#95b92a', capsize=3, lw=0.7, markersize=3)
            ax.errorbar(x=descriptive_statistics['StDev'][0], y=1, xerr=[[descriptive_statistics['StDev'][0] - f_statistics['sigma_1_ll']], [f_statistics['sigma_1_ul'] - descriptive_statistics['StDev'][0]]], fmt='o', color='#95b92a', capsize=3, lw=0.7, markersize=3)
            ax.set_ylim(-0.9, 1.9)
            labels = [item.get_text() for item in ax.get_yticklabels()]
            labels[0] = labels[3] = ''
            labels[1] = f'{source_2}'
            labels[2] = f'{source_1}'
            ax.set_yticks([-1, 0, 1, 2])
            for label in ax.get_xticklabels()[1::2]:
                label.set_visible(False)
            ax.set_yticks([-1, 0, 1, 2])
            ax.set_yticklabels(labels, fontsize=10)
            ax.grid(True, axis='x', zorder=0, alpha=0.7)
            ax.set_position([0.3, 0.3, 0.6, 0.05])

            # Boxplots
            ax = axs["Boxplots"]
            ax.set_title(f"Boxplots of {source_1} and {source_2}", fontsize=10)
            sns.boxplot(data=df_combined.values, ax=ax, palette=['#a1d111', '#a1d111'], linecolor='black', showcaps=False, linewidth=0.5, width=0.5, orient='h', flierprops={"marker": "x"})
            ax.set_ylim(-0.9, 1.9)
            labels = [item.get_text() for item in ax.get_yticklabels()]
            labels[0] = f'{source_2}'
            labels[1] = f'{source_1}'
            ax.set_yticks([0, 1])
            ax.set_yticklabels(labels, fontsize=10)
            ax.grid(True, axis='x', zorder=0, alpha=0.7)
            ax.set_position([0.3, 0.15, 0.6, 0.1])

            pdf.savefig(fig)
            plt.close(fig)

        pdf_io.seek(0)
        plt.close('all')
        return pdf_io

def _calculate_f_statistics(df1, source_1, df2, source_2, alpha):

    f_statistics = {}
    desriptive_statistics = {}

    sample_1_size = len(df1)
    sample_1_mean = df1[source_1].mean().round(5)
    sample_1_std = df1[source_1].std().round(3)
    # Calculate 95% CI for sigma (standard deviation)
    # Using chi-square distribution for confidence intervals of variance/std deviation
    chi2_lower_1 = stats.chi2.ppf(alpha/2, sample_1_size-1)
    chi2_upper_1 = stats.chi2.ppf(1-alpha/2, sample_1_size-1)
    sigma_ll_1 = np.sqrt((sample_1_size-1) * sample_1_std**2 / chi2_upper_1)
    sigma_ul_1 = np.sqrt((sample_1_size-1) * sample_1_std**2 / chi2_lower_1)
    sample_1_95_sigma = f"({sigma_ll_1:.3f}; {sigma_ul_1:.3f})"

    # Sample 2
    sample_2_size = len(df2)
    sample_2_mean = df2[source_2].mean().round(5)
    sample_2_std = df2[source_2].std().round(3)
    # Calculate 95% CI for sigma (standard deviation)
    # Using chi-square distribution for confidence intervals of variance/std dev
    chi2_lower_2 = stats.chi2.ppf(alpha/2, sample_2_size-1)
    chi2_upper_2 = stats.chi2.ppf(1-alpha/2, sample_2_size-1)
    sigma_ll_2 = np.sqrt((sample_2_size-1) * sample_2_std**2 / chi2_upper_2)
    sigma_ul_2 = np.sqrt((sample_2_size-1) * sample_2_std**2 / chi2_lower_2)
    sample_2_95_sigma = f"({sigma_ll_2:.3f}; {sigma_ul_2:.3f})"

    desriptive_statistics = {
            "Quelle": [source_1, source_2],
            "N": [sample_1_size, sample_2_size],
            "Mean": [sample_1_mean, sample_2_mean],
            "StDev": [sample_1_std, sample_2_std],
            r"95% CI $\sigma$": [sample_1_95_sigma, sample_2_95_sigma]
        }

    n1, n2 = len(df1), len(df2)
    degfreedom_total = n1 + n2 - 2
    # sample variances
    s1_sq, s2_sq = np.var(df1[source_1], ddof=1), np.var(df2[source_2], ddof=1)
    # F-test statistic (ensuring F >= 1)
    if s1_sq > s2_sq:
        F_stat = s1_sq / s2_sq
        degfreedom1, degfreedom2 = n1 - 1, n2 - 1
    else:
        F_stat = s2_sq / s1_sq
        degfreedom1, degfreedom2 = n2 - 1, n1 - 1
    # p-value for the F-Test
    p_value = 2 * np.minimum(stats.f.cdf(F_stat, degfreedom1, degfreedom2), 1 - stats.f.cdf(F_stat, degfreedom1, degfreedom2))
    # Levene's test for equal variances
    levene_stat, levene_p = stats.levene(df1[source_1], df2[source_2])

    # Approximate using square root of F-statistic CI bounds
    ci_lower_sd_levene = np.sqrt(F_stat / stats.f.ppf(0.975, degfreedom1, degfreedom2))
    ci_upper_sd_levene = np.sqrt(F_stat / stats.f.ppf(0.025, degfreedom1, degfreedom2))
    
    levene_statistics = {
        "test_statistic": levene_stat,
        "df": degfreedom_total,
        "p_value": levene_p,
        "lower_ci": ci_lower_sd_levene,
        "upper_ci": ci_upper_sd_levene
    }

    # Bonett's test approximation (p-value using normal approximation)
    bonett_stat = (s1_sq / s2_sq - 1) / np.sqrt(2 * (n1 - 1) / (n1 * n1) + 2 * (n2 - 1) / (n2 * n2))
    bonett_p = 2 * (1 - stats.norm.cdf(abs(bonett_stat)))

    # 95% CI for Variance Ratio using Bonett’s method
    ci_lower_bonett = np.exp(np.log(F_stat) - 1.96 * np.sqrt(2 / degfreedom1 + 2 / degfreedom2))
    ci_upper_bonett = np.exp(np.log(F_stat) + 1.96 * np.sqrt(2 / degfreedom1 + 2 / degfreedom2))

    # 95% CI for Standard Deviation Ratio using Bonett's method
    ci_lower_sd_bonett = np.sqrt(ci_lower_bonett)
    ci_upper_sd_bonett = np.sqrt(ci_upper_bonett)

    bonett_statistics = {
        "test_statistic": bonett_stat,
        "p_value": bonett_p,
        "lower_ci": ci_lower_sd_bonett,
        "upper_ci": ci_upper_sd_bonett
    }

    # Determine if the observed difference is detectable using f-test
    ratio_sigma = np.sqrt(F_stat)

    f_statistics = {
        "Levene": levene_statistics,
        "Bonett": bonett_statistics,
        "ratio_sigma": ratio_sigma,
        "deg_freedom": degfreedom_total,
        "sigma_1_ll": sigma_ll_1,
        "sigma_1_ul": sigma_ul_1,
        "sigma_2_ll": sigma_ll_2,
        "sigma_2_ul": sigma_ul_2
    }

    return desriptive_statistics, f_statistics


def _calculate_detectable_stddev_ratio(n1, n2, alpha=0.05, power_levels=[0.6, 0.7, 0.8, 0.9]):
    """Calculate detectable standard deviation ratios at various power levels."""    
    df1 = n1 - 1
    df2 = n2 - 1
    
    def objective_function(var_ratio, desired_power):
        # Critical values for rejection
        f_crit_lower = stats.f.ppf(alpha/2, df1, df2)
        f_crit_upper = stats.f.ppf(1-alpha/2, df1, df2)
        
        # Power calculation for two-sided test
        power = (1 - stats.f.cdf(f_crit_upper, df1, df2, scale=var_ratio) + 
                stats.f.cdf(f_crit_lower, df1, df2, scale=var_ratio))
        return power - desired_power
    
    results = {}
    for power in power_levels:
        try:
            var_ratio = optimize.brentq(objective_function, 1.001, 100, args=(power,))
            std_ratio = np.sqrt(var_ratio)
            percent_diff = (std_ratio - 1) * 100
            results[int(power*100)] = (std_ratio, percent_diff)
        except ValueError:
            results[int(power*100)] = (None, None)
    
    return results

def _sample_size_f_test(trennschaerfe, alpha=0.05, power_levels=[0.6, 0.7, 0.8, 0.9], two_sided=True):
    """
    Calculate the required sample size for detecting a difference in standard deviations 
    using an F-test with specified statistical power levels.
    
    Parameters:
    -----------
    trennschaerfe : float
        The ratio of the larger to the smaller standard deviation (σ₁/σ₂) that you want to detect.
        This is equivalent to the square root of the F-ratio of the variances.
    alpha : float, optional
        Significance level (Type I error rate), default is 0.05.
    power_levels : list, optional
        List of desired statistical power levels, default is [0.6, 0.7, 0.8, 0.9].
    two_sided : bool, optional
        Whether the test is two-sided (default) or one-sided.
        
    Returns:
    --------
    dict
        Dictionary with power levels as keys and required sample sizes as values.
        
    Notes:
    ------
    The F-test for comparing two variances requires that both samples have the same size.
    The returned sample size is the required size for each group.
    """
    # Convert trennschaerfe to variance ratio (F-ratio)
    # If trennschaerfe is already the variance ratio, square it
    # If trennschaerfe is the std ratio, square it to get variance ratio
    f_ratio = trennschaerfe**2
    
    # If f_ratio < 1, invert it since we're interested in the ratio > 1
    if f_ratio < 1:
        f_ratio = 1 / f_ratio
    
    # Adjust alpha for two-sided test
    if two_sided:
        alpha = alpha / 2
    
    results = {}
    
    for power in power_levels:
        # Start with a reasonable initial guess
        n = 10
        found = False
        max_iter = 1000
        iter_count = 0
        
        while not found and iter_count < max_iter:
            # Calculate the critical F-value
            f_crit = stats.f.ppf(1 - alpha, n - 1, n - 1)
            
            # Calculate the non-centrality parameter
            # For F-test comparing variances, non-centrality parameter is related to the ratio of variances
            nc = (n - 1) * (f_ratio - 1)**2 / (2 * f_ratio)
            
            # Calculate the actual power
            actual_power = 1 - stats.ncf.cdf(
                f_crit, 
                n - 1, 
                n - 1, 
                nc
            )
            
            # Check if we've reached the desired power
            if abs(actual_power - power) < 0.01:  # Within 1% of desired power
                found = True
            elif actual_power < power:
                n += 1
            else:
                # We overshot, but let's keep the smallest n that achieves the power
                found = True
            
            iter_count += 1
        
        results[power] = n
    
    return results

def _calculate_power_variance_test(n, expected_stddev, target_stddev, alpha=0.1):
    """
    Calculates the statistical power to detect a difference in standard deviation using a two-sided variance test.

    Parameters:
        n (int): Sample size for each group in the test.
        expected_stddev (float): The expected (baseline) standard deviation.
        target_stddev (float): The actual or hypothesized standard deviation to be detected.
        alpha (float, optional): Significance level for the test, with a default value of 0.1.

    Returns:
        float: The calculated power of the two-sided variance test.
    """
    variance_ratio = (target_stddev / expected_stddev) ** 2
    z_alpha_half = stats.norm.ppf(1 - alpha / 2)
    effect_size = math.sqrt(n / 2) * math.log(variance_ratio)
    cdf = stats.norm.cdf
    return cdf(-z_alpha_half - effect_size) + (1 - cdf(z_alpha_half - effect_size))