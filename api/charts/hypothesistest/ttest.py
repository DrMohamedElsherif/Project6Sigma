import io
import pandas as pd
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.backends.backend_pdf import PdfPages
from pydantic import BaseModel, Field
from typing import List, Dict
from api.schemas import BusinessLogicException
import seaborn as sns
from .mergecells import mergecells


# check data format
class TtestConfig(BaseModel):
    title: str
    target_mu: float
    alphalevel: float


class TtestData(BaseModel):
    values: Dict[str, List[float]] = Field(..., min_length=1)

class TtestRequest(BaseModel):
    project: str
    step: str
    config: TtestConfig
    data: TtestData

class Ttest:
    """
    A class to perform a one-sample t-test and generate a PDF report with the results.
    Attributes:
        project (str): The project name.
        step (str): The step name.
        config (object): The configuration object containing title, target_mu, and alphalevel.
        data (dict): The data dictionary containing the values to be tested.
    Methods:
        __init__(data: dict):
            Initializes the Ttest object with validated data.
        process():
            Processes the t-test, calculates descriptive statistics, generates a PDF report, and returns the PDF as a BytesIO object.
    """
    def __init__(self, data: dict):
        try:
            validated_data = TtestRequest(**data)
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
        target_mu = self.config.target_mu
        alpha = self.config.alphalevel
        source = list(self.data.values.keys())[0]
        df = pd.DataFrame(self.data.values)

        # Perform the t-test
        t_statistic, p_value = stats.ttest_1samp(df, target_mu)
        p_value = np.round(p_value, 4)
        if p_value < 0.0001:
            p_value = "0.000"

        # Calculate descriptive statistics
        sample_size = df.count().astype(int)
        sample_mean = df.mean().astype(float)
        sample_median = df.median()
        sample_std = df.std(ddof=1)
        sample_standard_error = sample_std / (sample_size ** 0.5)
        sample_lower_confidence_interval = sample_mean - stats.t.ppf(1 - alpha / 2, sample_size - 1) * sample_standard_error
        sample_lower_confidence_interval = sample_lower_confidence_interval.round(5)
        sample_upper_confidence_interval = sample_mean + stats.t.ppf(1 - alpha / 2, sample_size - 1) * sample_standard_error
        sample_upper_confidence_interval = sample_upper_confidence_interval.round(5)
        sample_95_confidence_interval = sample_lower_confidence_interval.astype(str) + "; " + sample_upper_confidence_interval.astype(str)
        sample_range = df.max() - df.min()


        descriptive_statistics = pd.DataFrame({
            "Quelle": source,
            "N": sample_size,
            "Mean": sample_mean.round(5),
            "Median": sample_median.round(5),
            "StDev": sample_std.round(5),
            "SE Mean": sample_standard_error.round(5),
            "95% CI for µ": sample_95_confidence_interval,
            "Range": sample_range.round(5)
        })

        # Calculate the power of the test
        observed_difference = abs(sample_mean[source] - target_mu)

        sample_95_confidence_interval_values = f"({sample_lower_confidence_interval[source].round(4)};{sample_upper_confidence_interval[source].round(4)})"
        print(sample_95_confidence_interval_values)

        if sample_lower_confidence_interval[source] <= target_mu <= sample_upper_confidence_interval[source]:
            difference_string = f"The mean value from ”{source}” is not significantly\ndifferent from target"
        else:
            difference_string = f"The mean value from ”{source}” is significantly\ndifferent from target"

        # Calculate detectable differences for different power levels
        power_levels = [0.6, 0.7, 0.8, 0.9]
        detectable_differences = {}
        for power in power_levels:
            effect_size = stats.norm.ppf(1 - alpha / 2) + stats.norm.ppf(power)
            detectable_difference = effect_size * sample_standard_error[source]
            detectable_differences[int(power * 100)] = detectable_difference.round(6)

        if observed_difference < detectable_differences[60]:
            observed_difference_color = "#c00000"
        elif detectable_differences[60] <= observed_difference <= detectable_differences[90]:
            observed_difference_color = "#f9b002"
        else:
            observed_difference_color = "#a7c315"

        if observed_difference < detectable_differences[60]:
            observed_difference_interval = "<60%"
        elif detectable_differences[60] <= observed_difference < detectable_differences[70]:
            observed_difference_interval = "60%-70%"
        elif detectable_differences[70] <= observed_difference < detectable_differences[80]:
            observed_difference_interval = "70%-80%"
        elif detectable_differences[80] <= observed_difference < detectable_differences[90]:
            observed_difference_interval = "80%-90%"
        else:
            observed_difference_interval = ">90%"           

        
        pdf_io = io.BytesIO()

        with PdfPages(pdf_io) as pdf:
            # NEW PDF PAGE - T-Test results, Descriptive Statistics, Data Time Series
            fig, axes = plt.subplot_mosaic([
                ["T-Test Results", "T-Test Results"],
                ["Descriptive Statistics", "Descriptive Statistics"],
                ["TS1", "TS1"],         # Time Series Plots for each dataset
                ["Chance", "Detectable"]],    # Chance and Detectable Difference
                figsize=(8.27, 11.69))  # A4 size in inches
            #fig.subplots_adjust(hspace=0.4)  # Increase hspace to add more space between charts
            fig.suptitle(title, fontsize=16, weight='bold', y=0.94)

            # Define the colors + fontsize
            edgecolor = "#7c7c7c"
            grey = "#e7e6e6"
            green_table = "#9cc563"
            lightgreen_table = "#d6ed5f"
            font_size=7            

            edge_color = '#D3D3D3'
            desired_height = 0.12
            font_size = 7
            row_height = 0.18
    
            # Table overview of the t-test results
            ax = axes["T-Test Results"]
            ax.axis('off')

            
            table_data = [
                ["Configuration", "", "Hypothesis", "", "", ""],
                [
                    "Each sample in its own column",
                    "",
                    f"H0: µ = {target_mu}",
                    "t-Value",
                    "df",
                    "p-Value*"
                ],
                [
                    "Test-Setup",
                    "Different",
                    f"H1: µ ≠ {target_mu}",
                    f"{t_statistic[0].round(2)}",
                    f"{sample_size[source] - 1}",
                    f"{p_value}"
                ],
                [
                    "Target",
                    f"{target_mu}",
                    "",
                    "",
                    "",
                    ""
                ],
                [
                    "Sample",
                    f"{source}",
                    "empty",
                    "",
                    "",
                    f"{observed_difference.round(6)}"
                ],
                [
                    "Alpha-Level",
                    f"{alpha}",
                    "empty",
                    "",
                    "",
                    f"{sample_95_confidence_interval_values}"
                ],
                [
                    "Interested\ndifference**",
                    "-",
                    "empty",
                    f"{difference_string}",
                    "",
                    ""
                ],
                [
                    "",
                    "","","","",""
                ]
            ]
            # Set the column widths as needed
            col_widths = [0.15, 0.15, 0.15, 0.15, 0.15, 0.15]

            bg_colors = [
                ["#e7e6e6", "#e7e6e6", "#e7e6e6", "#e7e6e6", "#e7e6e6", "#e7e6e6"],
                ["#ffffff", "#ffffff", "#d6ed5f", "#ffffff", "#ffffff", "#ffffff"],
                ["#ffffff", "#ffffff", "#9cc563", "#ffffff", "#ffffff", "#9cc563"],
                ["#ffffff", "#ffffff", "#ffffff", "#e7e6e6", "#e7e6e6", "#e7e6e6"],
                ["#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff"],
                ["#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff"],
                ["#ffffff", "#ffffff", "#ffffff", "#9cc563", "#9cc563", "#9cc563"],
                ["#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff"]
            ]

            table_bg = ax.table(bbox=[0, 0, 1, 1], cellColours=bg_colors)
            for cell in table_bg._cells.values():
                cell.set_edgecolor("none")

            bg_none = [
                ["none", "none", "none", "none", "none", "none"],
                ["none", "none", "none", "none", "none", "none"],
                ["none", "none", "none", "none", "none", "none"],
                ["none", "none", "none", "none", "none", "none"],
                ["none", "none", "none", "none", "none", "none"],
                ["none", "none", "none", "none", "none", "none"],
                ["none", "none", "none", "none", "none", "none"],
                ["none", "none", "none", "none", "none", "none"]
            ]

            table = ax.table(
                bbox=[0, 0, 1, 1],
                cellText=table_data,
                colWidths=col_widths,
                loc='upper left',
                cellLoc='center',
                cellColours=bg_none          
            )
            table.auto_set_font_size(False)
            table.set_fontsize(font_size)

            for cell in table._cells.values():
                cell.set_edgecolor("#7c7c7c")
                cell.set_linewidth(0.5)

            mergecells(table, [(0, 0), (0, 1)])
            mergecells(table, [(0, 3), (0, 4), (0, 5)])
            mergecells(table, [(1, 0), (1, 1)])
            mergecells(table, [(3, 2), (4, 2), (5, 2), (6, 2)])
            mergecells(table, [(3, 3), (3, 4), (3, 5)])
            mergecells(table, [(4, 3), (4, 4)])
            mergecells(table, [(5, 3), (5, 4)])
            mergecells(table, [(6, 3), (6, 4), (6, 5)])
            mergecells(table, [(7, 0), (7, 1), (7, 2), (7, 3), (7, 4), (7, 5)])

            # test_cell = table.get_celld()[(7, 0)]
            # test_cell.set_fontsize(2)
            table.get_celld()[7, 0].set_fontsize(5)
            

            cell_text_centered_1 = table.get_celld()[(0, 4)]
            cell_text_centered_1.set_text_props(
                text='Results',
                x=1.5,
                y=0.5,
                visible=True,
                ha='center'
            )
            cell_text_centered_2 = table.get_celld()[(4, 4)]
            cell_text_centered_2.set_text_props(
                text='Mean sample',
                x=1.5,
                y=0.5,
                visible=True,
                ha='right'
            )
            cell_text_centered_3 = table.get_celld()[(5, 4)]
            cell_text_centered_3.set_text_props(
                text='95% CI (confidence interval)',
                x=1.5,
                y=0.5,
                visible=True,
                ha='right'
            )     
            cell_text_centered_4 = table.get_celld()[(3, 4)]
            cell_text_centered_4.set_text_props(
                text='Mean',
                x=1.5,
                y=0.5,
                visible=True,
                ha='center'
            )
            cell_text_small = table.get_celld()[(7, 0)]
            cell_text_small.set_text_props(
                text='* If the p-value is less than the α-level, then H0 is to be rejected and the alternative hypothesis H1 is to be accepted.\n** Optional: What difference between the two means has a practical value? (Power and sample size)',
                visible=True,
                color='grey',
                ha='right'
            )
            bold_text = [(2, 1), (1, 3), (1, 4), (1, 5)]
            for row, col in bold_text:
                cell = table.get_celld()[(row, col)]
                cell.set_text_props(weight='bold')

            left_text = [(1, 0), (5, 3), (6, 3), (7, 0)]
            for row, col in left_text:
                cell = table.get_celld()[(row, col)]
                cell.set_text_props(ha='left')

            right_text = [(0, 0), (3, 3), (4, 3)]
            for row, col in right_text:
                cell = table.get_celld()[(row, col)]
                cell.set_text_props(ha='right')
            
            # Set the text of the bottom row to grey
            # for col in range(6):
            #     cell = table.get_celld()[(7, col)]
            #     cell.set_text_props(color='grey')

            # table.auto_set_font_size(False)
            # table.set_fontsize(font_size)

            # Table for descriptive statistics
            axes["Descriptive Statistics"].axis('off')
            axes["Descriptive Statistics"].set_title("Descriptive Statistics", loc='left', pad=-50, y=1.02)
            axes["Descriptive Statistics"].axis('tight')
            table_1_widths = [0.18, 0.06, 0.11, 0.11, 0.11, 0.11, 0.21, 0.11]
            table_1 = axes["Descriptive Statistics"].table(cellText=descriptive_statistics.values, colLabels=descriptive_statistics.columns, loc='center', cellLoc='center', colWidths=table_1_widths)
            table_1.auto_set_font_size(False)
            table_1.set_fontsize(font_size)
            for cell in table_1._cells.values():
                cell.set_edgecolor("#7c7c7c")
                cell.set_linewidth(0.5)

            # Set the top row color to #e7e6e6
            for col in range(len(descriptive_statistics.columns)):
                cell = table_1[(0, col)]
                cell.set_facecolor("#e7e6e6")

            axes["TS1"].plot(df, color='black', marker="o")
            axes["TS1"].set_title("Data Time Series", loc='left')
            axes["TS1"].hlines(sample_mean, 0, len(df), colors='grey', linestyles='dashed', label=f"Target mu: {target_mu}", alpha=0.7)
            # Highlight points outside the mean ± standard deviation
            Q1 = df[source].quantile(0.25)
            Q3 = df[source].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR

            for i, value in enumerate(df[source]):
                if value < lower_bound or value > upper_bound:
                    axes["TS1"].plot(i, value, color='red', marker="s")  # Red color, 's' marker

            # Table for the power of the test
            ax = axes["Chance"]
            ax.axis('off')
            ax.set_title("Power and detected difference", loc='left', pad=-50, y=1.02)

            cellText = [
                ["60%", "", "90%"],
                ["", "", ""],
                [f"{detectable_differences[60]}", "", f"{detectable_differences[90]}"],
                ["Sample size", "Observed difference", ""],
                ["50", f"{observed_difference.round(6)}", f"{observed_difference_interval}"]
            ]

            # Determine the background color for the bottom right cell based on the observed difference
            # CHANGE: MOVE UP
            # if observed_difference > detectable_differences[90]:
            #     bottom_right_color = "#a7c315"  # green
            # elif observed_difference < detectable_differences[60]:
            #     bottom_right_color = "#c00000"  # red
            # else:
            #     bottom_right_color = "#f9b002"  # yellow

            bg_colors = [
                ["#e7e6e6", "#e7e6e6", "#e7e6e6"],
                ["#c00000", "#f9b002", "#a7c315"],
                ["#ffffff", "#ffffff", "#ffffff"],
                ["#e7e6e6", "#e7e6e6", "#e7e6e6"],
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
                loc='lower left',
                colWidths=[0.12, 0.17, 0.12],  # Set column widths for the left table
                cellColours=bg_none,
                edges='open'
            )

            for cell in table._cells.values():
                cell.set_linewidth(0.5)


            # Add visible edges to the table
            n_rows, n_cols = 5, 3
            for (i, j), cell in table.get_celld().items():
                # Top row: set top edge visible
                if i == 0:
                    cell.visible_edges = cell.visible_edges + "T"
                    cell.set_edgecolor("#7c7c7c")
                # Bottom row: set bottom edge visible
                if i == n_rows - 1:
                    cell.visible_edges = cell.visible_edges + "B"
                    cell.set_edgecolor("#7c7c7c")
                if i == n_rows - 2:
                    cell.visible_edges = cell.visible_edges + "B"
                    cell.set_edgecolor("#7c7c7c")
                if i == n_rows - 3:
                    cell.visible_edges = cell.visible_edges + "B"
                    cell.set_edgecolor("#7c7c7c")
                # First column: set left edge visible
                if j == 0:
                    cell.visible_edges = cell.visible_edges + "L"
                    cell.set_edgecolor("#7c7c7c")
                # Last column: set right edge visible
                if j == n_cols - 1:
                    cell.visible_edges = cell.visible_edges + "R"
                    cell.set_edgecolor("#7c7c7c")
                if i == n_rows - 1 and j == 0:
                    cell.visible_edges = "BLR"
                    cell.set_edgecolor("#7c7c7c")

            for key, cell in table.get_celld().items():
                if key == (0, 0):
                    cell.set_text_props(ha='right')
                if key == (0, 2):
                    cell.set_text_props(ha='left')
                # if key == (1, 0):
                #     cell.visible_edges = 'BTL'
                if key == (2, 0):
                    cell.set_text_props(ha='right')
                if key == (2, 2):
                    cell.set_text_props(ha='left')
                # if key == (1, 2):
                #     cell.visible_edges = 'BTR'
                if key == (3, 1):
                    cell.set_text_props(ha='right')
                
            mergecells(table, [(3, 1), (3, 2)])

            table.auto_set_font_size(False)
            table.set_fontsize(font_size)
            
            # Table for detectable differences
            ax = axes["Detectable"]
            ax.axis('off')
            # Create table data for detectable differences
            power_column = list(detectable_differences.keys())
            difference_column = list(detectable_differences.values())
            table_data = list(zip(power_column, difference_column))

            # Define table column widths
            col_widths = [0.5, 0.5]

            # Create the table
            table = ax.table(
                bbox=[0, 0, 1, 0.5],
                cellText=table_data,
                colLabels=["Power", "Difference"],
                cellLoc='center',
                loc='center',
                colWidths=col_widths
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

            # NEW PDF PAGE - Graphs
            fig, axes = plt.subplot_mosaic([
                ["Hist"],
                ["Boxplot"]],
            figsize=(8.27, 11.69))  # A4 size in inches
            #fig.subplots_adjust(hspace=0.4)  # Increase hspace to add more space between charts
            fig.suptitle(title, fontsize=16, weight='bold', y=0.94)
            fig.subplots_adjust(hspace=0.4)

            # Histogram
            axes["Hist"].hist(df[source], color='#95b92a', edgecolor='black', zorder=1)
            axes["Hist"].set_title(f"Histogram of {source}")
            axes["Hist"].set_ylabel("Frequency")
            axes["Hist"].set_xlabel(f"{source}")
            # Plot target_mu as a point at y = -0.5
            axes["Hist"].plot(target_mu, -0.5, color="red", marker="*", label=f'Target Mean: {target_mu}')
            # Plot sample mean as a point with 95% CI error bars at y = -1
            axes["Hist"].errorbar(sample_mean[source], -0.5, xerr=[[sample_mean[source] - sample_lower_confidence_interval[source]], [sample_upper_confidence_interval[source] - sample_mean[source]]], fmt='|', capsize=5, color='lightblue', label=f'Sample Mean: {sample_mean[source]:.5f}')
            # Adjust y-axis to make space for the lines
            axes["Hist"].set_ylim(bottom=-0.1 * axes["Boxplot"].get_ylim()[1])
            axes["Hist"].set_axisbelow(True)
            axes["Hist"].grid(True, axis='y', zorder=0)

            legend = axes["Hist"].legend()
            for text in legend.get_texts():
                text.set_fontsize('x-small')
            # Remove the horizontal line through the target_mu marker
            for line in legend.get_lines():
                line.set_linewidth(0)

            # Boxplot
            sns.boxplot(x=df[source], ax=axes["Boxplot"], orient='h', color="#a1d111", linecolor='black', showcaps=False, linewidth=1, width=0.3)

            # Plot target_mu as a point below the boxplot
            axes["Boxplot"].plot(target_mu, -0.3, color="red", marker="*", label=f'Target Mean: {target_mu}')
            # Plot sample mean as a point with 95% CI error bars below the boxplot
            axes["Boxplot"].errorbar(sample_mean[source], -0.3, xerr=[[sample_mean[source] - sample_lower_confidence_interval[source]], [sample_upper_confidence_interval[source] - sample_mean[source]]], fmt='|', capsize=5, color='lightblue', label=f'Sample Mean: {sample_mean[source]:.5f}')
            # Adjust y-axis to make space for the lines
            axes["Boxplot"].set_title(f"Boxplot of {source}")
            axes["Boxplot"].set_xlabel(f"{source}")
            axes["Boxplot"].set_ylim(-0.6, 0.6)
            axes["Boxplot"].grid(True)
            legend = axes["Boxplot"].legend()
            for text in legend.get_texts():
                text.set_fontsize('x-small')
            for line in legend.get_lines():
                line.set_linewidth(0)

            pdf.savefig(fig)
            plt.close(fig)

        pdf_io.seek(0)
        plt.close('all')
        return pdf_io