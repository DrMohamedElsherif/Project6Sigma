import io
import math
import pandas as pd
import numpy as np
import scipy.stats as stats
from scipy.stats import norm
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from matplotlib.backends.backend_pdf import PdfPages
from pydantic import BaseModel, Field, conlist
from typing import List, Dict, Optional, Annotated
from api.schemas import BusinessLogicException
import seaborn as sns

from ...utils.pdf_utils import add_header_or_footer_to_a4_portrait

header_image_path = 'assets/img/Header.png'
footer_image_path = 'assets/img/Footer.png'

from ...utils.mpl_table_utils import merge_mpl_table_cells as mergecells

class FtestConfig(BaseModel):
    title: str
    target_sigma: float
    power: Optional[Annotated[float, Field(gt=0, le=1)]] = None
    alphalevel: float


class FtestData(BaseModel):
    values: Dict[str, conlist(float, min_length=1)] # type: ignore

class FtestRequest(BaseModel):
    project: str
    step: str
    config: FtestConfig
    data: FtestData

class Ftest:
    """
    A class to perform F-test analysis on data.
    F-test is used to test if two standard deviations are significantly different or if a standard deviation
    is significantly different from a target value. This implementation supports both Bonett's method (valid for any
    continuous distribution) and Chi-Square method (valid for normal distributions).
    The class handles data validation, processing, and visualization of results including:
    - Statistical hypothesis testing for standard deviations
    - Confidence intervals using both Bonett and Chi-Square methods
    - Power analysis for detecting differences
    - Sample size calculations
    - Data visualization through histograms, time series plots, and error bars
    The output is a PDF report with comprehensive statistical analysis and visualizations.
    Parameters
    ----------
    data : dict
        A dictionary containing the following keys:
        - project: Project information
        - step: Step information
        - config: Configuration settings including:
            - title: Title for the report
            - target_sigma: Target standard deviation to test against
            - alphalevel: Significance level (typically 0.05 for 95% confidence)
            - power: Optional power value for sample size calculations
        - data: The dataset to analyze with:
            - values: Dictionary of data values with column names as keys
    Raises
    ------
    BusinessLogicException
        If the input data fails validation
    Methods
    -------
    process()
        Performs the F-test analysis and generates a PDF report
    Returns
    -------
    io.BytesIO
        A BytesIO object containing the generated PDF report
    """
    def __init__(self, data: dict):
        try:
            validated_data = FtestRequest(**data)
            self.project = validated_data.project
            self.step = validated_data.step
            self.config = validated_data.config
            self.data = validated_data.data
        
        except ValueError as e:
            raise BusinessLogicException(
                error_code="error_validation",
                field=str(e),
                details={"message": f"Invalid or missing field: {str(e)}"}
            )
    
    def process(self):
        title = self.config.title
        target_sigma = self.config.target_sigma
        alpha = self.config.alphalevel
        power = self.config.power
        source = list(self.data.values.keys())[0]
        df1 = pd.DataFrame(self.data.values)

        # Calculate Bonett's confidence interval for the population standard deviation
        lower_bonett, upper_bonett = _bonett_confidence_interval(df1[source], alpha)

        # Calculate Bonett's test for H0: sigma = target_sigma
        Z_bonett, p_value_bonett = _bonett_test(df1[source], target_sigma)
        
        # Calculate the confidence interval for sigma using the Chi-Square distribution
        lower_chi, upper_chi = _chi_square_confidence_interval(df1[source], alpha)

        # Calculate the Chi-Square test for H0: sigma = target_sigma
        chi_square_stat, df, p_value_chi = _chi_square_test(df1[source], target_sigma)

        # Determine if the observed difference is detectable
        if lower_chi > target_sigma or upper_chi < target_sigma:
            difference_string = f"The standard deviation from ”{source}” is\n significantly different from target."
            difference_color = "#9cc563"
        else:
            difference_string = f"The standard deviation from ”{source}” is\nnot significantly different from target."
            difference_color = "#d6ed5f"


        # Calculate descriptive statistics
        sample_1_size = len(df1)
        sample_1_mean = df1[source].mean().round(5)
        sample_1_std = df1[source].std().round(3)
        # Calculate 95% CI for sigma (standard deviation)
        # Using chi-square distribution for confidence intervals of variance/std deviation
        chi2_lower_1 = stats.chi2.ppf(alpha/2, sample_1_size-1)
        chi2_upper_1 = stats.chi2.ppf(1-alpha/2, sample_1_size-1)
        sigma_ll_1 = np.sqrt((sample_1_size-1) * sample_1_std**2 / chi2_upper_1)
        sigma_ul_1 = np.sqrt((sample_1_size-1) * sample_1_std**2 / chi2_lower_1)
        sample_1_95_sigma = f"({sigma_ll_1:.3f}; {sigma_ul_1:.3f})"

        descriptive_statistics = {
            "Quelle": [source],
            "N": [sample_1_size],
            "Mean": [sample_1_mean],
            "StDev": [sample_1_std],
            r"95% CI for $\sigma$": [sample_1_95_sigma]
        }

        # Calculate detectable differences for given power levels
        power_levels = [0.6, 0.7, 0.8, 0.9]
        detectable_differences = _calculate_detectable_differences(n=sample_1_size, alpha=alpha, sigma0=target_sigma, powers=power_levels)
        
        # Calculate required sample sizes if power provided
        if power is not None:
            required_sample_sizes_greater = _calculate_sample_size_variance_test(expected_stddev = target_sigma, target_stddev=(target_sigma + power), alpha=alpha, power_levels=power_levels)
            required_sample_sizes_less = _calculate_sample_size_variance_test(expected_stddev = target_sigma, target_stddev=(target_sigma - power), alpha=alpha, power_levels=power_levels)
            power_sample_size_greater = _calculate_power_variance_test(n=sample_1_size, expected_stddev=target_sigma, target_stddev=(target_sigma + power), alpha=alpha)
            power_sample_size_less = _calculate_power_variance_test(n=sample_1_size, expected_stddev=target_sigma, target_stddev=(target_sigma - power), alpha=alpha)

        pdf_io = io.BytesIO()

        with PdfPages(pdf_io) as pdf:
            # NEW PDF PAGE - T-Test results, Descriptive Statistics, Data Time Series
            fig, axes = plt.subplot_mosaic([
                ["T-Test Results", "T-Test Results"],
                ["Descriptive Statistics", "Descriptive Statistics"],
                ["TS1", "TS1"],         # Time Series Plots for each dataset
                ["Chance", "Detectable"]],    # Chance and Detectable Difference
                figsize=(8.27, 11.69), dpi=300)  # A4 size in inches
            # fig.subplots_adjust(hspace=0.4)  # Increase hspace to add more space between charts
            # fig.suptitle(title, fontsize=16, weight='bold', y=0.94)

            header_ax = add_header_or_footer_to_a4_portrait(fig, header_image_path, position='header')
            footer_ax = add_header_or_footer_to_a4_portrait(fig, footer_image_path, position='footer', page_number=1, total_pages=2)


            # Define the colors + font size
            edgecolor = "#7c7c7c"
            grey = "#e7e6e6"
            green_table = "#9cc563"
            lightgreen_table = "#d6ed5f"
            font_size=7

            # T-Test Results Table
            ax = axes["T-Test Results"]
            ax.axis('off')

            # Define table data
            cellText = [
                ["Configuration", "", "Hypothesis", "", "", "", ""],
                ["Each sample in its own column", "", f"$H_{0}: \sigma =${target_sigma}", "Method*", "Test statistic", "df", "p-Value*"],
                ["\nTest-Setup", "\nDifferent", f"\n$H_{1}: \sigma ≠${target_sigma}", "Bonett", "-", "-", f"{p_value_bonett:.3f}"],
                ["", "", "", "Chi-Square", f"{chi_square_stat:.2f}", f"{df}", f"{p_value_chi:.3f}"],
                ["Target", f"{target_sigma}", "", "", "", "", ""],
                ["Sample", f"{source}", "", "", "", "", f"{sample_1_std:.3f}"],
                ["\nα-Level", f"\n {alpha}", "", "", "Bonett CI", "", f"({lower_bonett:.3f}; {upper_bonett:.3f})"],
                ["", f"{alpha}", "", "", "", "", f"({lower_chi:.3f}; {upper_chi:.3f})"],
                ["Interested\ndifference**", f"{power if power is not None else '-'}", "", f"{difference_string}", "", "", ""],
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
                text=r"$\sigma$ sample",
                x=1.5,
                y=0.5,
                visible=True,
                ha='right'
            )
            cell_text_centered_3 = table.get_celld()[(5, 5)]
            cell_text_centered_3.set_text_props(
                text=f"{sample_1_std:.3f}",
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
                text='90% CI (Chi-Square)',
                x=1.5,
                y=0.5,
                visible=True,
                ha='right'
            )
            cell_text_centered_6 = table.get_celld()[(6, 5)]
            cell_text_centered_6.set_text_props(
                text=f"({lower_bonett:.3f}; {upper_bonett:.3f})",
                x=1.5,
                y=0.5,
                visible=True,
                ha='left'
            )
            cell_text_centered_7 = table.get_celld()[(7, 5)]
            cell_text_centered_7.set_text_props(
                text=f"({lower_chi:.3f}; {upper_chi:.3f})",
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

            right_text = [(0, 0), (3, 3), (4, 3)]
            for row, col in right_text:
                cell = table.get_celld()[(row, col)]
                cell.set_text_props(ha='right')

            # Descriptive Statistics Table
            ax = axes["Descriptive Statistics"]
            ax.axis('off')
            ax.set_title("Descriptive Statistics", loc='left', pad=-50, y=1.02)
            descriptive_table_widths = [0.18, 0.06, 0.11, 0.11, 0.19]
            cellText = list(zip(*descriptive_statistics.values()))
            descriptive_table = ax.table(
                cellText=cellText,
                colLabels=list(descriptive_statistics.keys()),
                cellLoc='center',
                loc='upper left',
                colWidths=descriptive_table_widths,
                bbox=[0, 0.3, 0.6, 0.15]
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



            # Data time series plot
            ax = axes["TS1"]
            ax.plot(df1, color='black', marker="o", linewidth=0.5)
            ax.set_title("Data Time Series", loc='left')
            sample_mean = df1[source].mean()
            ax.hlines(sample_mean, 0, len(df1) - 1, colors='grey', linestyles='dashed', label=f"Sample mean: {sample_mean:.2f}", alpha=0.7)
            # Highlight points outside the mean ± standard deviation
            Q1 = df1[source].quantile(0.25)
            Q3 = df1[source].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR

            for i, value in enumerate(df1[source]):
                if value < lower_bound or value > upper_bound:
                    ax.plot(i, value, color='red', marker="s")  # Red color, 's' marker


            # Power and detected difference
            ax = axes["Chance"]
            ax.axis('off')
            ax.set_title("Power and Detectable Differences", loc='left', pad=-50, y=1.2)


            if power is not None:

                ax.set_title(f"What is the chance of detecting a difference of {power}?", pad=-70, y=1.02, fontsize=font_size)

                if power_sample_size_greater < 0.60:
                    observed_difference_color_1 = "#c00000"
                elif 0.60 <= power_sample_size_greater <= 0.90:
                    observed_difference_color_1 = "#f9b002"
                else:
                    observed_difference_color_1 = "#a7c315"

                if power_sample_size_less < 0.60:
                    observed_difference_color_2 = "#c00000"
                    observed_difference_text_color = "#ffffff"
                elif 0.60 <= power_sample_size_less <= 0.90:
                    observed_difference_color_2 = "#f9b002"
                    observed_difference_text_color = "#000000"
                else:
                    observed_difference_color_2 = "#a7c315"
                    observed_difference_text_color = "#000000"

                cellText = [
                    ["60%", "", "90%"],
                    ["", "", ""],
                    [f"{detectable_differences['Greater'][2]}|-{detectable_differences['Less'][2]}", "", f"{detectable_differences['Greater'][5]}|-{detectable_differences['Less'][5]}"],
                    ["Sample size", "Chance of Detecting a difference", ""],
                    [f"{sample_1_size}", "greater", f"{power_sample_size_greater*100:.1f}%"],
                    ["", "less", f"{power_sample_size_less*100:.1f}%"]
                ]
                bg_colors = [
                ["#e7e6e6", "#e7e6e6", "#e7e6e6"],
                ["#c00000", "#f9b002", "#a7c315"],
                ["#ffffff", "#ffffff", "#ffffff"],
                [grey, grey, grey],
                ["#ffffff", "#ffffff", observed_difference_color_1],
                ["#ffffff", "#ffffff", observed_difference_color_2]
                ]

                table_bg = ax.table(bbox=[0, 0, 1, 0.5], cellColours=bg_colors, colWidths=[0.18, 0.44, 0.20])
                for cell in table_bg._cells.values():
                    cell.set_edgecolor("none")

                bg_none = [
                    ["none", "none", "none"],
                    ["none", "none", "none"],
                    ["none", "none", "none"],
                    ["none", "none", "none"],
                    ["none", "none", "none"],
                    ["none", "none", "none"]
                ]

            else: 
                # Calculate observed difference from target
                observed_difference = abs(sample_1_std - target_sigma)

                # Determine the observed difference interval based on detectable differences
                if observed_difference < detectable_differences['Greater'][2]:  # Less than 60% power
                    observed_difference_interval = "<60%"
                    observed_difference_color = "#c00000"
                    observed_difference_text_color = "#ffffff"
                elif detectable_differences['Greater'][2] <= observed_difference < detectable_differences['Greater'][3]:  # Between 60-70% power
                    observed_difference_interval = "60%-70%"
                    observed_difference_color = "#f9b002"
                    observed_difference_text_color = "#000000"
                elif detectable_differences['Greater'][3] <= observed_difference < detectable_differences['Greater'][4]:  # Between 70-80% power
                    observed_difference_interval = "70%-80%"
                    observed_difference_color = "#f9b002"
                    observed_difference_text_color = "#000000"
                elif detectable_differences['Greater'][4] <= observed_difference < detectable_differences['Greater'][5]:  # Between 80-90% power
                    observed_difference_interval = "80%-90%"
                    observed_difference_color = "#f9b002"
                    observed_difference_text_color = "#000000"
                else:  # Greater than 90% power
                    observed_difference_interval = ">90%"
                    observed_difference_color = "#a7c315"
                    observed_difference_text_color = "#000000"

                ax.set_title("Chance of detecting a difference", loc='center', pad=-70, y=1.02, fontsize=font_size)

                cellText = [
                    ["60%", "", "90%"],
                    ["", "", ""],
                    [f"{detectable_differences['Greater'][2]}|-{detectable_differences['Less'][2]}", "", f"{detectable_differences['Greater'][5]}|-{detectable_differences['Less'][5]}"],
                    ["Sample size", "Observed difference", ""],
                    [f"{sample_1_size}", "", f"{observed_difference_interval}"]
                ]

                bg_colors = [
                    ["#e7e6e6", "#e7e6e6", "#e7e6e6"],
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
                cellColours=bg_none,
                edges='open'
            )

            table[(4, 2)].set_text_props(color=observed_difference_text_color)

            for cell in table._cells.values():
                cell.set_linewidth(0.5)

            # Add visible edges to the table
            n_rows, n_cols = 5, 3
            edge_mapping = {
                'top': [(i, j) for i in [0] for j in range(n_cols)],
                'bottom': [(i, j) for i in [n_rows-3, n_rows-2, n_rows-1] for j in range(n_cols)],
                'left': [(i, 0) for i in range(n_rows)],
                'right': [(i, n_cols-1) for i in range(n_rows)]
            }

            # Apply edges based on position
            for (i, j), cell in table.get_celld().items():
                edges = ""
                if (i, j) in edge_mapping['top']: 
                    edges += "T"
                if (i, j) in edge_mapping['bottom']: 
                    edges += "B"
                if (i, j) in edge_mapping['left']: 
                    edges += "L"
                if (i, j) in edge_mapping['right']: 
                    edges += "R"
                
                # Special case for bottom-left cell
                if i == n_rows-1 and j == 0:
                    edges = "BLR"
                    
                # Apply the edges if any were defined
                if edges:
                    cell.visible_edges = edges
                    cell.set_edgecolor(edgecolor)

            # Configure text alignment
            text_alignments = {
                (0, 0): 'right',
                (0, 2): 'left',
                (2, 0): 'left',
                (2, 2): 'right',
                (3, 1): 'left'
            }

            # Apply text alignments
            for pos, alignment in text_alignments.items():
                if pos in table.get_celld():
                    table.get_celld()[pos].set_text_props(ha=alignment)
            
            # Merge cells
            mergecells(table, [(3, 1), (3, 2)])

            # Set font size
            table.auto_set_font_size(False)
            table.set_fontsize(font_size)

            ax = axes["Detectable"]
            ax.axis('off')

            if power is not None:
                ax.set_title(f"What sample size is required to detect a differnce\nof {power}?", pad=-70, y=1.02, fontsize=font_size)
                table_data = [
                [f"\nPower", "",""],
                ["", "greater", "less"],
                ["60%", f"{required_sample_sizes_greater[0.6]}", f"{required_sample_sizes_less[0.6]}"],
                ["70%", f"{required_sample_sizes_greater[0.7]}", f"{required_sample_sizes_less[0.7]}"],
                ["80%", f"{required_sample_sizes_greater[0.8]}", f"{required_sample_sizes_less[0.8]}"],
                ["90%", f"{required_sample_sizes_greater[0.9]}", f"{required_sample_sizes_less[0.9]}"]
                ]
            else:
                ax.set_title(f"Detectable difference with sample sizes of N = {sample_1_size}", pad=-70, y=1.02, fontsize=font_size)
                # Define table data
                table_data = detectable_differences.values.tolist()

                # Define column widths
                col_widths = [0.5, 0.25, 0.25]

            # Define background colors
            bg_colors = [
                ["#e7e6e6", "#e7e6e6", "#e7e6e6"],
                ["#e7e6e6", "#e7e6e6", "#e7e6e6"],
                ["#ffffff", "#ffffff", "#ffffff"],
                ["#ffffff", "#ffffff", "#ffffff"],
                ["#ffffff", "#ffffff", "#ffffff"],
                ["#ffffff", "#ffffff", "#ffffff"]
            ]

            # Create the table with background colors
            table_bg = ax.table(bbox=[0, 0, 1, 0.5], cellColours=bg_colors)
            for cell in table_bg._cells.values():
                cell.set_edgecolor("none")

            bg_none = [
                ["none", "none", "none"],
                ["none", "none", "none"],
                ["none", "none", "none"],
                ["none", "none", "none"],
                ["none", "none", "none"],
                ["none", "none", "none"]
            ]


            table = ax.table(
                bbox=[0, 0, 1, 0.5],
                cellText=table_data,
                cellLoc='center',
                loc='center',
                colWidths=col_widths,
                cellColours=bg_none
            )
            # Set the font size for the table
            table.auto_set_font_size(False)
            table.set_fontsize(font_size)

            # Change edgecolor of table
            for cell in table._cells.values():
                cell.set_edgecolor(edgecolor)
                cell.set_linewidth(0.5)

            mergecells(table, [(0, 0), (1, 0)])
            mergecells(table, [(0, 1), (0, 2)])


            cell_text_right = table.get_celld()[(0, 1)]
            if power is not None:
                cell_text_right.set_text_props(
                    text='Required sample size',
                    x=0.5,
                    y=0.5,
                    visible=True,
                    ha='left'
                )
            else:
                cell_text_right.set_text_props(
                    text='Difference to target',
                    x=0.5,
                    y=0.5,
                    visible=True,
                    ha='left'
                )

            pdf.savefig(fig)
            plt.close(fig)            

            # NEW PDF PAGE - Histogram and Errorbar
            fig, axs = plt.subplot_mosaic([
                ["Hist"],
                ["Errorbar"]],
                figsize=(8.27, 11.69), gridspec_kw={'height_ratios': [3, 1]}, dpi=300)  # A4 size in inches
            fig.subplots_adjust(hspace=0.8)  # Increase hspace to add more space between charts
            # fig.suptitle(title, fontsize=16, weight='bold', y=0.94)

            header_ax = add_header_or_footer_to_a4_portrait(fig, header_image_path, position='header')
            footer_ax = add_header_or_footer_to_a4_portrait(fig, footer_image_path, position='footer', page_number=2, total_pages=2)


            # Histogram
            ax = axs["Hist"]
            ax.hist(df1[source], color='#95b92a', edgecolor='black', zorder=2)
            ax.set_title(f"Histogram of {source}", loc='left')
            ax.set_ylabel("Frequency")
            ax.grid(True, alpha=0.3, zorder=0)

            # Fit a gaussian function to the data
            counts, bins, _ = ax.hist(df1[source], color='#95b92a', edgecolor='black')

            # Define gaussian function
            def gaussian(x, a, mu, sigma):
                return a * np.exp(-(x-mu)**2 / (2*sigma**2))
            
            # Calculate the bin centers
            bin_center = (bins[:-1] + np.diff(bins) / 2)

            x_values_to_fit = np.linspace(bins[0], bins[-1], 1000)
            param, cov = curve_fit(gaussian, bin_center, counts)
            ax.plot(x_values_to_fit, gaussian(x_values_to_fit, *param), color='#a03130', label='Gaussian fit', zorder=5)

            # Errorbar
            ax = axs["Errorbar"]
            ax.errorbar(x=sample_1_std, y=1, xerr=[[sample_1_std - lower_chi], [upper_chi - sample_1_std]], fmt='o', color='#0054a7', capsize=5)
            ax.vlines(target_sigma, 0.5, 1.5, color='#67b57a', linestyles='dashed', label=f"Target: {target_sigma}")
            ax.set_title("90% CI for the Standard Deviation", loc='center')
            ax.set_ylim(0.75, 1.25)
            ax.set_yticks([])
            ax.grid(True, axis='x', zorder=0, alpha=0.7)
            legend = ax.legend()
            for text in legend.get_texts():
                text.set_fontsize('x-small')
            # Remove the horizontal line through the target_mu marker
            for line in legend.get_lines():
                line.set_linewidth(1)

            pdf.savefig(fig)
            plt.close(fig)

        pdf_io.seek(0)
        plt.close('all')
        return pdf_io
    

def _bonett_confidence_interval(data, alpha):
        """
        Bonett's confidence interval for the population standard deviation.
        alpha=0.10 gives a 90% confidence interval.
        """
        n = len(data)
        s2 = np.var(data, ddof=1)  # Unbiased sample variance

        # Step 1: G = ln(s^2)
        G = np.log(s2)

        # Step 2: z-value for (1 - alpha/2)
        z = norm.ppf(1 - alpha/2)  # e.g., alpha=0.10 => z=1.645 for 90% CI

        # Step 3: Var(G) ~ 2/(n-1)
        varG = 2.0 / (n - 1)
        seG = np.sqrt(varG)  # standard error of G

        # Step 4: Confidence interval for ln(s^2)
        lower_ln = G - z * seG
        upper_ln = G + z * seG

        # Step 5: Confidence interval for s^2
        lower_s2 = np.exp(lower_ln)
        upper_s2 = np.exp(upper_ln)

        # Step 6: Confidence interval for s
        lower_s = np.sqrt(lower_s2)
        upper_s = np.sqrt(upper_s2)

        return lower_s, upper_s
    
def _bonett_test(data, sigma0):
    """
    Bonett test for H0: sigma = sigma0  vs.  H1: sigma != sigma0.
    Returns Z-statistic and two-sided p-value.
    """    
    n = len(data)
    s2 = np.var(data, ddof=1)
    # G = ln(s^2 / sigma0^2)
    G = np.log(s2) - np.log(sigma0**2)

    varG = 2.0 / (n - 1)
    seG = np.sqrt(varG)

    Z = G / seG
    # Two-sided p-value
    p_value = 2 * (1 - norm.cdf(abs(Z)))
    
    return Z, p_value

def _chi_square_confidence_interval(data, alpha):
    """
    Returns the (1-alpha) confidence interval for sigma using the Chi-Square distribution.
    alpha=0.10 => 90% confidence interval.
    """
    from scipy.stats import chi2
    n = len(data)
    s2 = np.var(data, ddof=1)
    df = n - 1
    
    # Chi-square critical values
    chi2_lower = chi2.ppf(alpha/2, df)      # for lower tail
    chi2_upper = chi2.ppf(1 - alpha/2, df)  # for upper tail
    
    lower_sigma = np.sqrt((df * s2) / chi2_upper)
    upper_sigma = np.sqrt((df * s2) / chi2_lower)
    
    return lower_sigma, upper_sigma


def _chi_square_test(data, sigma0):
    """
    Chi-Square test for H0: sigma = sigma0  vs.  H1: sigma != sigma0.
    Returns the chi-square statistic and two-sided p-value.
    """
    n = len(data)
    s2 = np.var(data, ddof=1)
    chi_square_stat = (n - 1) * s2 / (sigma0**2)
    df = n - 1
    
    # Two-sided p-value:
    # p = P(X <= chi_square_stat) for X ~ Chi2(df)
    # But for a two-sided test we consider both tails.
    p_one_side = stats.chi2.cdf(chi_square_stat, df)
    # lower tail is p_one_side
    # upper tail is 1 - p_one_side
    # two-sided p-value is how extreme chi_square_stat is in either tail:
    if chi_square_stat < df:
        # If chi_square_stat is below the mean (df), then the lower tail is p_one_side
        p_value = 2 * p_one_side
    else:
        # If chi_square_stat is above the mean, the upper tail is (1 - p_one_side)
        p_value = 2 * (1 - p_one_side)
    
    # But ensure p_value <= 1
    p_value = min(p_value, 1.0)
    
    return chi_square_stat, df, p_value

def _calculate_detectable_differences(n=50, alpha=0.10, sigma0=0.30, powers=[0.60, 0.70, 0.80, 0.90]):
    # Two-sided z critical value for alpha=0.1
    z_alpha = norm.ppf(1 - alpha/2)  # ~1.645

    # Function to get the z-value for a given power
    def z_for_power(power):
        # power = 1 - beta -> beta = 1 - power
        return norm.ppf(power)

    results = {
        "Power": [],
        "Greater": [],
        "Less": []
    }
    # Add top labels here, so that the table is correctly formatted
    results["Power"].append("\nPower")
    results["Greater"].append("")
    results["Less"].append("")
    results["Power"].append("")
    results["Greater"].append("greater")
    results["Less"].append("less")

    for p in powers:
        beta = 1 - p
        z_beta = z_for_power(p)

        # Combined z factor: (z_alpha + z_beta)
        z_factor = z_alpha + z_beta

        # sqrt(1 / [2*(n-1)])
        sqrt_factor = np.sqrt(1 / (2 * (n - 1)))

        # Calculate sigma_greater
        sigma_greater = sigma0 * np.exp(z_factor * sqrt_factor)
        diff_greater = sigma_greater - sigma0
        diff_greater = round(diff_greater, 6)

        # Calculate sigma_less
        sigma_less = sigma0 * np.exp(-z_factor * sqrt_factor)
        diff_less = sigma0 - sigma_less
        diff_less = round(diff_less, 6)
        
        results["Power"].append(f"{int(p*100)}%")
        results["Greater"].append(diff_greater)
        results["Less"].append(diff_less)

    return pd.DataFrame(results)

def _calculate_sample_size_variance_test(expected_stddev, target_stddev, alpha=0.1, power_levels=None):
    """
    Calculate required sample sizes for a 1-sample F-test (variance test).
    
    Parameters:
    -----------
    expected_stddev : float
        The expected standard deviation (null hypothesis)
    target_stddev : float
        The target standard deviation to detect (alternative hypothesis)
    alpha : float, optional
        Significance level for the test (default is 0.1)
    power_levels : list of float, optional
        List of power levels to calculate sample sizes for
        (default is [0.6, 0.7, 0.8, 0.9])
    
    Returns:
    --------
    dict
        Dictionary mapping power levels to required sample sizes
    """
    if power_levels is None:
        power_levels = [0.6, 0.7, 0.8, 0.9]
    
    # Variance ratio
    variance_ratio = (target_stddev / expected_stddev) ** 2
    
    # Critical z-value for alpha/2 (two-tailed test)
    z_alpha_half = stats.norm.ppf(1 - alpha/2)
    
    results = {}
    
    for power in power_levels:
        # z-value for the desired power
        z_beta = stats.norm.ppf(power)
        
        # Calculate sample size using the formula:
        # n ≈ 1 + 2(z_α/2 + z_β)² / (ln(σ₁²/σ₀²))²
        numerator = 2 * (z_alpha_half + z_beta) ** 2
        denominator = (math.log(variance_ratio)) ** 2
        
        # Ensure we don't divide by zero (in case variance_ratio is very close to 1)
        if abs(denominator) < 1e-10:
            sample_size = float('inf')
        else:
            sample_size = 1 + (numerator / denominator)
        
        # Round up to the nearest integer
        results[power] = math.ceil(sample_size)
    
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