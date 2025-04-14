import io
import os
import pandas as pd
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt

from matplotlib.backends.backend_pdf import PdfPages
from pydantic import BaseModel, Field, conlist, model_validator
from typing import Dict, Optional, Annotated, List
from api.schemas import BusinessLogicException
import seaborn as sns
from statsmodels.stats.power import TTestIndPower

from ...utils.pdf_utils import add_header_or_footer_to_a4_portrait

header_image_path = 'assets/img/Header.png'
footer_image_path = 'assets/img/Footer.png'

from ...utils.mpl_table_utils import merge_mpl_table_cells as mergecells


# check data format
class TtestConfig(BaseModel):
    title: str
    target_mu: float
    power: Optional[Annotated[float, Field(gt=0, le=1)]] = None
    alphalevel: float

class TtestData(BaseModel):
    values: Dict[str, conlist(float, min_length=1)] # type: ignore

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
        """
        Process the t-test, generate graphs and create PDF report.
        
        Returns:
            BytesIO: PDF report as a BytesIO object
        """
        # Extract configuration values
        title = self.config.title
        target_mu = self.config.target_mu
        alpha = self.config.alphalevel
        power = self.config.power
        
        # Prepare data
        source = list(self.data.values.keys())[0]
        df = pd.DataFrame(self.data.values)

        # Validation for the sample size
        if len(df) < 2:
            raise BusinessLogicException(
                error_code="insufficient_data",
                field="data.values",
                details={"message": "At least 2 data points are required for a t-test"}
            )
        

        confidence_percent = int((1 - alpha) * 100)
        
        results, power_analysis = _calculate_statistics(df, target_mu, alpha, power)

        # Hypothesis test result
        if results['p_value'] > alpha:
            difference_string = f"The mean value from ”{source}” is not significantly\ndifferent from target"
            difference_color = "#d6ed5f"
        else:
            difference_string = f"The mean value from ”{source}” is significantly\ndifferent from target"
            difference_color = "#9cc563"

        descriptive_statistics = pd.DataFrame({
            "Quelle": source,
            "N": results['sample_size'],
            "Mean": results['mean'].round(5),
            "Median": results['median'].round(5),
            "StDev": results['std_dev'].round(5),
            "SE Mean": results['std_err'].round(5),
            f"{confidence_percent}% CI for µ": f"({results['confidence_interval'][0]:.5f}; {results['confidence_interval'][1]:.5f})",
            "Range": results['sample_range'].round(5)
        }, index=[0])

        # Generate PDF report
        pdf_io = io.BytesIO()
        
        with PdfPages(pdf_io) as pdf:
            # Page 1: T-Test Results, Descriptive Statistics, Data Time Series
            fig, axes = plt.subplot_mosaic([
                ["T-Test Results", "T-Test Results"],
                ["Descriptive Statistics", "Descriptive Statistics"],
                ["TS1", "TS1"],         # Time Series Plots for each dataset
                ["Chance", "Detectable"]],    # Chance and Detectable Difference
                figsize=(8.27, 11.69),  dpi=300)  # A4 size in inches
            fig.suptitle(title, fontsize=14, y=0.92, ha='left', x=0.1)
            add_header_or_footer_to_a4_portrait(fig, header_image_path, position='header')
            add_header_or_footer_to_a4_portrait(fig, footer_image_path, position='footer', page_number=1, total_pages=2)
            


            # Define colors and formatting
            grey = "#e7e6e6"
            green_table = "#9cc563"
            lightgreen_table = "#d6ed5f"
            font_size = 7
            edge_color = "#7c7c7c"
            
            # T-Test Results table
            ax = axes["T-Test Results"]
            ax.axis('off')

            # Calculate confidence percentage for display            
            table_data = [
                ["Configuration", "", "Hypothesis", "", "", ""],
                ["Each sample in its own column", "", r"$\mathrm{H_{0}: \mu}$ =" + f" {target_mu}", "t-Value", "df", "p-Value*"],
                ["Test-Setup", "Different", r"$\mathrm{H_{1}: \mu} \neq $" + f" {target_mu}", f"{results['t_statistic'].round(2)}", f"{results['degrees_of_freedom']}", f"{results['p_value']:.3f}"],
                ["Target", f"{target_mu}", "", "", "", ""],
                ["Sample", f"{source}", "empty", "", "", f"{results['observed_difference'].round(6)}"],
                ["Alpha-Level", f"{alpha}", "empty", "", "", f"({results['diff_confidence_interval'][0]:.4f}; {results['diff_confidence_interval'][1]:.4f})"],
                ["Interested\ndifference**", f"{power if power is not None else '-'}", "empty", difference_string, "", ""],
                ["", "", "", "", "", ""]
            ]
            
            # Set column widths
            col_widths = [0.15, 0.15, 0.15, 0.15, 0.15, 0.15]

            bg_colors = [
                [grey, grey, grey, grey, grey, grey],
                ["#ffffff", "#ffffff", lightgreen_table, "#ffffff", "#ffffff", "#ffffff"],
                ["#ffffff", "#ffffff", green_table, "#ffffff", "#ffffff", difference_color],
                ["#ffffff", "#ffffff", "#ffffff", grey, grey, grey],
                ["#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff"],
                ["#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff"],
                ["#ffffff", "#ffffff", "#ffffff", difference_color, difference_color, difference_color],
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
                cell.set_edgecolor(edge_color)
                cell.set_linewidth(0.5)

            # Apply cell merges
            mergecells(table, [(0, 0), (0, 1)])
            mergecells(table, [(0, 3), (0, 4), (0, 5)])
            mergecells(table, [(1, 0), (1, 1)])
            mergecells(table, [(3, 2), (4, 2), (5, 2), (6, 2)])
            mergecells(table, [(3, 3), (3, 4), (3, 5)])
            mergecells(table, [(4, 3), (4, 4)])
            mergecells(table, [(5, 3), (5, 4)])
            mergecells(table, [(6, 3), (6, 4), (6, 5)])
            mergecells(table, [(7, 0), (7, 1), (7, 2), (7, 3), (7, 4), (7, 5)])

            table.get_celld()[7, 0].set_fontsize(5)
            
            # Set cell text properties
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
                text=f'{confidence_percent}% CI (confidence interval)',
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
            
            # Define text formatting
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
            
            # Descriptive Statistics table
            ax = axes['Descriptive Statistics']
            ax.axis('off')
            ax.set_title("Descriptive Statistics", loc='left', pad=-50, y=1.02)
            ax.axis('tight')
            
            # Adjust column widths as needed
            table_1_widths = [0.18, 0.06, 0.11, 0.11, 0.11, 0.11, 0.21, 0.11]
            table_1 = axes["Descriptive Statistics"].table(
                cellText=descriptive_statistics.values, 
                colLabels=descriptive_statistics.columns, 
                loc='center', 
                cellLoc='center', 
                colWidths=table_1_widths
            )
            table_1.auto_set_font_size(False)
            table_1.set_fontsize(font_size)
            
            for cell in table_1._cells.values():
                cell.set_edgecolor(edge_color)
                cell.set_linewidth(0.5)

            # Set the top row color to grey
            for col in range(len(descriptive_statistics.columns)):
                cell = table_1[(0, col)]
                cell.set_facecolor(grey)

            # Data Time series plot
            ax = axes["TS1"]
            ax.plot(df, color='black', marker="o", lw=0.5)
            ax.set_title("Data Time Series", loc='left')
            ax.hlines(results['mean'], 0, len(df), colors='grey', linestyles='dashed', label=f"Target mu: {target_mu}", alpha=0.7, lw=0.5)
            ax.text(0.1, 0.1, source, transform=ax.transAxes, fontsize=7, verticalalignment='top', horizontalalignment='center')
            
            # Highlight outliers
            Q1 = df[source].quantile(0.25)
            Q3 = df[source].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR

            # Set y-axis limits with 10% padding
            y_min = df[source].min()
            y_max = df[source].max()
            y_padding = (y_max - y_min) * 0.1
            ax.set_ylim(y_min - y_padding, y_max + y_padding)

            for i, value in enumerate(df[source]):
                if value < lower_bound or value > upper_bound:
                    ax.plot(i, value, color='red', marker="s")  # Red square for outliers
                       


            # Chance of detecting a difference table
            ax = axes["Chance"]
            ax.axis('off')
            ax.set_title("Power and detected difference", loc='left', pad=-50, y=1.2)
            

            if power is not None:

                if power_analysis['Detection Chance'] < 60:
                    observed_difference_color = "#c00000"
                    observed_difference_text_color = "#ffffff"
                elif 60 <= power_analysis['Detection Chance'] <= 90:
                    observed_difference_color = "#f9b002"
                    observed_difference_text_color = "#000000"
                else:
                    observed_difference_color = "#a7c315"
                    observed_difference_text_color = "#000000"

                ax.set_title(f"What is the chance of detecting a difference of {power}?", pad=-70, y=1.02, fontsize=font_size)

                cellText = [
                    ["60%", "", "90%"],
                    ["", "", ""],
                    [f"{power_analysis['Detectable Difference 60%']:.6f}", "", f"{power_analysis['Detectable Difference 90%']:.6f}"],
                    ["Sample size", "Chance of Detecting a difference", ""],
                    [f"{results['sample_size']}", "", f"{power_analysis['Detection Chance']}%"]
                ]
            else:
                if results['observed_difference'] < power_analysis['Detectable Difference 60%']:
                    observed_difference_interval = "<60%"
                    observed_difference_color = "#c00000"
                    observed_difference_text_color = "#ffffff"
                elif power_analysis['Detectable Difference 60%'] <= results['observed_difference'] < power_analysis['Detectable Difference 70%']:
                    observed_difference_interval = "60%-70%"
                    observed_difference_color = "#f9b002"
                    observed_difference_text_color = "#000000"
                elif power_analysis['Detectable Difference 70%'] <= results['observed_difference'] < power_analysis['Detectable Difference 80%']:
                    observed_difference_interval = "70%-80%"
                    observed_difference_color = "#f9b002"
                    observed_difference_text_color = "#000000"
                elif power_analysis['Detectable Difference 80%'] <= results['observed_difference'] < power_analysis['Detectable Difference 90%']:
                    observed_difference_interval = "80%-90%"
                    observed_difference_text_color = "#000000"
                else:
                    observed_difference_interval = ">90%" 
                    observed_difference_color = "#a7c315"
                    observed_difference_text_color = "#000000"

                ax.set_title("Chance of detecting a difference", loc='center', pad=-70, y=1.02, fontsize=font_size)

                cellText = [
                    ["60%", "", "90%"],
                    ["", "", ""],
                    [f"{power_analysis['Detectable Difference 60%']:.6f}", "", f"{power_analysis['Detectable Difference 90%']:.6f}"],
                    ["Sample size", "Observed difference", ""],
                    [f"{results['sample_size']}", f"{results['observed_difference']:.6f}", f"{observed_difference_interval}"]
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
                loc='lower left',
                colWidths=[0.12, 0.17, 0.12],  # Column widths for the left table
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
                    cell.set_edgecolor(edge_color)

            # Configure text alignment
            text_alignments = {
                (0, 0): 'right',
                (0, 2): 'left',
                (2, 0): 'right',
                (2, 2): 'left',
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
                
            # Detectable difference table
            ax = axes["Detectable"]
            ax.axis('off')
            power_column = ["60%", "70%", "80%", "90%"]
            # Create table data
            # Create table data from power analysis results
            if power is not None:
                # If power was provided, show required sample sizes
                ax.set_title(f"What sample size is required to detect a difference\nof {power}?", loc='center', pad=-70, y=1.02, fontsize=font_size)
                sample_sizes = [f"{power_analysis[f'Required Samples {p}']:.0f}" for p in power_column]
                table_data = list(zip(power_column, sample_sizes))
                colLabels_difference = ["Power", "Sample Size"]
            else:
                # Otherwise show detectable differences
                ax.set_title("Detectable difference with sample sizes of N", loc='center', pad=-70, y=1.02, fontsize=font_size)
                differences = [f"{power_analysis[f'Detectable Difference {p}']:.6f}" for p in power_column]
                table_data = list(zip(power_column, differences))
                colLabels_difference = ["Power", "Difference"]

            # Define table column widths
            col_widths = [0.5, 0.5]

            # Create the table
            table = ax.table(
                bbox=[0, 0, 1, 0.5],
                cellText=table_data,
                colLabels=colLabels_difference,
                cellLoc='center',
                loc='center',
                colWidths=col_widths
            )

            # Set font size
            table.auto_set_font_size(False)
            table.set_fontsize(font_size)

            # Set table styling
            for cell in table._cells.values():
                cell.set_edgecolor(edge_color)
                cell.set_linewidth(0.5)

            # Set the top row color to grey
            for cell in table._cells:
                if cell[0] == 0:
                    table._cells[cell].set_facecolor(grey)
                    
            pdf.savefig(fig)
            plt.close(fig)

            # Page 2: Histogram and Boxplot
            fig, axes = plt.subplot_mosaic([
                ["Hist"],
                ["Boxplot"]],
                figsize=(8.27, 11.69), dpi=300)  # A4 size in inches
            # fig.suptitle(title, fontsize=16, weight='bold', y=0.94)
            # fig.subplots_adjust(hspace=0.4)
            header_ax = add_header_or_footer_to_a4_portrait(fig, header_image_path, position='header')
            footer_ax = add_header_or_footer_to_a4_portrait(fig, footer_image_path, position='footer', page_number=2, total_pages=2)
            
            # Histogram
            ax = axes["Hist"]
            n, bins, patches = ax.hist(df[source], color='#95b92a', edgecolor='black', zorder=1)
            ax.set_title(f"Histogram of {source}")
            ax.set_ylabel("Frequency")
            ax.set_xlabel(f"{source}")
            
            # Get the current y-axis limits
            ymin, ymax = ax.get_ylim()
            
            # Plot target_mu and sample mean
            ax.plot(target_mu, -0.5, color="red", marker="*", label=r'$\mu_{0}$')
            ax.errorbar(
                results['mean'], 
                -0.5, 
                xerr=[
                    [results['mean'] - results['confidence_interval'][0]], 
                    [results['confidence_interval'][1] - results['mean']]
                ], 
                fmt='|', 
                capsize=5, 
                color='lightblue', 
                label=r"$\overline{x}$"
            )
            
            # Adjust y-axis
            ax.set_ylim(bottom=-1, top=ymax * 1.05)
            ax.set_axisbelow(True)
            ax.grid(True, zorder=0, alpha=0.3)

            # Configure legend
            legend = ax.legend()
            for text in legend.get_texts():
                text.set_fontsize('x-small')
            for line in legend.get_lines():
                line.set_linewidth(0)

            # Boxplot
            ax = axes["Boxplot"]
            sns.boxplot(
                x=df[source], 
                ax=ax, 
                orient='h', 
                color="#a1d111", 
                linecolor='black', 
                showcaps=False, 
                linewidth=1, 
                width=0.3, 
                flierprops={"marker": "x"}
            )

            # Plot target_mu and sample mean
            ax.plot(target_mu, -0.3, color="red", marker="*", label=r'$\mu_{0}$')
            ax.errorbar(
                results['mean'], 
                -0.3, 
                xerr=[
                    [results['mean'] - results['confidence_interval'][0]], 
                    [results['confidence_interval'][1] - results['mean']]
                ], 
                fmt='|', 
                capsize=5, 
                color='lightblue', 
                label=r"$\overline{x}$"
            )
            
            ax.set_title(f"Boxplot of {source}")
            ax.set_xlabel(f"{source}")
            ax.set_ylim(-0.6, 0.6)
            ax.grid(True, alpha=0.3)
            
            # Configure legend
            legend = ax.legend()
            for text in legend.get_texts():
                text.set_fontsize('x-small')
            for line in legend.get_lines():
                line.set_linewidth(0)

            pdf.savefig(fig)
            plt.close(fig)

        pdf_io.seek(0)
        plt.close('all')
        return pdf_io
    
def _calculate_statistics(data, mu, alpha, p):
    # Extract first column if data is a DataFrame
    if isinstance(data, pd.DataFrame):
        source = list(data.columns)[0]
        data_values = data[source]
    else:
        data_values = data

    # Calculate descriptive statistics
    sample_size = len(data_values)
    degrees_of_freedom = sample_size - 1
    mean = data_values.mean()
    median = data_values.median()
    std_dev = data_values.std(ddof=1)  # Sample standard deviation
    std_err = std_dev / np.sqrt(sample_size)
    confidence_level = 1 - alpha
    confidence_interval = stats.t.interval(confidence_level, degrees_of_freedom, loc=mean, scale=std_err)
    sample_range = data_values.max() - data_values.min()
    observed_difference = mean - mu
    
    # Calculate confidence interval for the observed difference
    # This is the same as the confidence interval for the mean, but centered around the observed difference
    t_critical = stats.t.ppf((1 + confidence_level) / 2, degrees_of_freedom)
    margin_of_error = t_critical * std_err
    diff_lower = observed_difference - margin_of_error
    diff_upper = observed_difference + margin_of_error
    diff_confidence_interval = (diff_lower, diff_upper)

    # Perform 1-sample t-test
    t_statistic, p_value = stats.ttest_1samp(data_values, mu)

    # Create a dictionary to store the results
    results = {
        'sample_size': sample_size,
        'degrees_of_freedom': degrees_of_freedom,
        'mean': mean,
        'median': median,
        'std_dev': std_dev,
        'std_err': std_err,
        'confidence_interval': confidence_interval,
        'confidence_level': confidence_level * 100,
        'sample_range': sample_range,
        't_statistic': t_statistic,
        'p_value': p_value,
        'observed_difference': observed_difference,
        'diff_confidence_interval': diff_confidence_interval
    }

    power_analysis = {}
    powers = [0.6, 0.7, 0.8, 0.9]
    for power in powers:
        # Calculate the detectable difference
        effect_size = stats.norm.ppf(1 - alpha / 2) + stats.norm.ppf(power)
        detectable_diff = effect_size * std_err
        power_analysis[f'Detectable Difference {int(power * 100)}%'] = detectable_diff

        # Calculate the required sample size if p is provided
        if p is not None:
            # Use Cohen's d formula to calculate effect size from the desired detectable difference
            effect_size = p / std_dev
            # Use statsmodels power calculation for a more accurate sample size estimate
            analysis = TTestIndPower()
            required_N = analysis.solve_power(effect_size=effect_size, power=power, alpha=alpha, alternative='two-sided')
            power_analysis[f'Required Samples {int(power * 100)}%'] = required_N
            
            # Calculate the chance of detecting the specified difference p with the current sample size
            calculated_power = analysis.solve_power(
            effect_size=effect_size,
            nobs1=sample_size,
            alpha=alpha,
            alternative='two-sided'
            )
            power_analysis['Detection Chance'] = calculated_power * 100  # Store as percentage
    
    # Calculate chance of detecting difference at specific power levels (60% and 90%)
    if p is not None:
        effect_size = p / std_dev
        analysis = TTestIndPower()
        
        # Calculate detection chance at 60%
        chance_60 = analysis.solve_power(
            effect_size=effect_size,
            power=0.6,
            alpha=alpha,
            alternative='two-sided'
        )
        power_analysis['Detection Chance 60%'] = chance_60 * 100
        
        # Calculate detection chance at 90%
        chance_90 = analysis.solve_power(
            effect_size=effect_size,
            power=0.9,
            alpha=alpha,
            alternative='two-sided'
        )
        power_analysis['Detection Chance 90%'] = chance_90 * 100

    return results, power_analysis