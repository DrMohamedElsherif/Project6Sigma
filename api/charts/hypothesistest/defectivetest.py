import io
import math
import pandas as pd
import numpy as np
import scipy.stats as stats
from scipy.optimize import brentq
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.backends.backend_pdf import PdfPages
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from api.schemas import BusinessLogicException
import seaborn as sns
from statsmodels.stats.power import TTestIndPower

from ...utils.pdf_utils import add_header_or_footer_to_a4_portrait

header_image_path = 'assets/img/Header.png'
footer_image_path = 'assets/img/Footer.png'

from ...utils.mpl_table_utils import merge_mpl_table_cells as mergecells


# check data format
class DefectiveTestConfig(BaseModel):
    title: str
    target_p: float
    variant: str
    power: Optional[float] = None
    alphalevel: float
    sample_name: Optional[str] = None
    sample_size: Optional[int] = None   # Variant 1
    defective_count: Optional[int] = Field(None, alias="defective/event")   # Variant 1
    sample_column: Optional[str] = None     # Variant 2
    defective_name: Optional[str] = None    # Variant 2
    
    class Config:
        populate_by_name = True

class DefectiveTestData(BaseModel):
    values: Optional[Dict[str, List[str]]] = Field(None)

class DefectiveTestRequest(BaseModel):
    project: str
    step: str
    config: DefectiveTestConfig
    data: Optional[DefectiveTestData] = None

class Defectivetest:
    def __init__(self, data: dict):
        try:
            validated_data = DefectiveTestRequest(**data)
            self.project = validated_data.project
            self.step = validated_data.step
            self.config = validated_data.config
            self.data = validated_data.data

            # Check for required parameters based on variant
            if self.config.variant == "Summarized data":
                if self.config.sample_size is None or self.config.defective_count is None:
                    raise BusinessLogicException(
                        error_code="error_defective_summarized",
                        field="configuration_parameters",
                        details={
                            "message": "For 'Summarized data' variant, both 'sample_size' and 'defective_count' are required"
                        }
                    )
            elif self.config.variant == "Datas in column":
                if self.config.defective_name is None or self.data is None or self.data.values is None:
                    raise BusinessLogicException(
                        error_code="error_defective_column",
                        field="configuration_parameters",
                        details={
                            "message": "For 'Datas in column' variant, 'sample_column', 'defective_name', and 'data.values' are required"
                        }
                    )

        except Exception as e:
            raise BusinessLogicException(
                error_code="error_validation",
                field=str(e),
                details={"message": f"Invalid or missing field: {str(e)}"}
            )
        
    def process(self):
        title = self.config.title
        target_p = self.config.target_p
        variant = self.config.variant
        power_percentage = self.config.power
        alphalevel = self.config.alphalevel
        
        # Handle data extraction based on variant
        if variant == "Summarized data":
            sample_size = self.config.sample_size
            defective_count = self.config.defective_count
            source = [self.config.sample_name if self.config.sample_name else "Sample"]
            data = [[]]  # Empty placeholder for summarized data
        else:  # "Datas in column"
            sample_column = self.config.sample_column
            defective_name = self.config.defective_name
            source = list(self.data.values.keys())
            data = list(self.data.values.values())
            
            # Count defectives from column data
            sample_size = len(data[0])
            defective_count = data[0].count(defective_name)

        sample_p = defective_count / sample_size

        # Calculate the Z-value
        std_error = math.sqrt((target_p * (1 - target_p)) / sample_size)
        z_value = (sample_p - target_p) / std_error

        # Calculate p-value (two-tailed)
        p_value = 2 * (1 - stats.norm.cdf(abs(z_value)))

        # Calculate confidence interval based on alpha level
        if alphalevel == 0.1:
            z_critical = 1.645
            ci_level = "90%"
        elif alphalevel == 0.05:
            z_critical = 1.96
            ci_level = "95%"
        elif alphalevel == 0.01:
            z_critical = 2.576
            ci_level = "99%"
        else:
            z_critical = 1.96
            ci_level = "95%"

        ci_margin = z_critical * math.sqrt((sample_p * (1 - sample_p)) / sample_size)
        ci_lower = sample_p - ci_margin
        ci_upper = sample_p + ci_margin

        if variant == "Datas in column":
            variant_str = "Each sample in its own column"
        else:
            variant_str = "Summarized data"

        # Calculate the required sample size for different power levels if power is provided
        if power_percentage is not None:
            delta = power_percentage

            required_n_60, _ = _calculate_required_sample_size(target_p, delta, 60, alphalevel, sample_size)
            required_n_70, _ = _calculate_required_sample_size(target_p, delta, 70, alphalevel, sample_size)
            required_n_80, _ = _calculate_required_sample_size(target_p, delta, 80, alphalevel, sample_size)
            required_n_90, _ = _calculate_required_sample_size(target_p, delta, 90, alphalevel, sample_size)
            _, power_for_your_sample_size = _calculate_required_sample_size(target_p, delta, 90, alphalevel, sample_size)
            detectable_diff_60 = _calculate_detectable_difference(target_p, sample_size, 60, alphalevel)
            detectable_diff_90 = _calculate_detectable_difference(target_p, sample_size, 90, alphalevel)



            # Prepare results
            results = {
            "total_samples": sample_size,
            "defectives": defective_count,
            "sample_p": sample_p,
            "target_p": target_p,
            "z_value": z_value,
            "p_value": p_value,
            "ci_95_lower": ci_lower,
            "ci_95_upper": ci_upper,
            "power_percentage": power_percentage,
            "interested_difference": f"{delta*100}%",
            "power_for_your_sample_size": power_for_your_sample_size,
            "required_sample_sizes": {
                "60%": required_n_60,
                "70%": required_n_70,
                "80%": required_n_80,
                "90%": required_n_90
            },
            "detectable_differences": {
                "60%": detectable_diff_60,
                "90%": detectable_diff_90
            }
        }
        else:
            # Calculate the detectable difference for different power levels
            detectable_diff_60 = _calculate_detectable_difference(target_p, sample_size, 60, alphalevel)
            detectable_diff_70 = _calculate_detectable_difference(target_p, sample_size, 70, alphalevel)
            detectable_diff_80 = _calculate_detectable_difference(target_p, sample_size, 80, alphalevel)
            detectable_diff_90 = _calculate_detectable_difference(target_p, sample_size, 90, alphalevel)

            # Prepare results
            results = {
                "total_samples": sample_size,
                "defectives": defective_count,
                "sample_p": sample_p,
                "target_p": target_p,
                "z_value": z_value,
                "p_value": p_value,
                "ci_95_lower": ci_lower,
                "ci_95_upper": ci_upper,
                "interested_difference": "-",
                "detectable_differences": {
                    "60%": detectable_diff_60,
                    "70%": detectable_diff_70,
                    "80%": detectable_diff_80,
                    "90%": detectable_diff_90
                }
            }
        # Hypothesis test verdict
        if p_value < alphalevel:
            hypothesis_string = f"The % Defective value from ”{source[0]}” is significantly\ndifferent from target."
            table_1_color = "#9cc563"
        else:
            hypothesis_string = f"The % Defective value from ”{source[0]}” is not significantly\ndifferent from target."
            table_1_color = "#d6ed5f"

        # Create PDF
        pdf_io = io.BytesIO()

        with PdfPages(pdf_io) as pdf:
            # NEW PDF PAGE - T-Test results, Descriptive Statistics, Data Time Series
            fig, axes = plt.subplot_mosaic([
                ["Defective-Test Results", "Defective-Test Results"],
                ["Descriptive Statistics", "Descriptive Statistics"],
                ["Power", "Difference"],         # Time Series Plots for each dataset
                ["Errorbar", "Histogram"]],    # Chance and Detectable Difference
                figsize=(8.27, 11.69), dpi=300)  # A4 size in inches
            #fig.subplots_adjust(hspace=0.4)  # Increase hspace to add more space between charts
            fig.suptitle(title, fontsize=14, y=0.92, ha='left', x=0.1)

            add_header_or_footer_to_a4_portrait(fig, header_image_path, position='header')
            add_header_or_footer_to_a4_portrait(fig, footer_image_path, position='footer', page_number=1, total_pages=1)

            # Define the colors + fontsize
            grey = "#e7e6e6"
            green_table = "#9cc563"
            lightgreen_table = "#d6ed5f"
            font_size=7
            edge_color = "#7c7c7c"

            # Table overview of the defective test results
            ax = axes["Defective-Test Results"]
            ax.axis('off')

            table_data = [
                ["Configuration", "", "Hypothesis", "", "", ""],
                [variant_str, "", r"$\mathrm{H_{0}}$:"+ f"p = {target_p}", "", "Z-Value", "p-Value*"],
                ["Test-Setup", "Different", r"$\mathrm{H_{1}}$:" + f"p ≠ {target_p}", "", f"{results['z_value']:.4f}", f"{results['p_value']:.4f}"],
                ["Target", f"{target_p}", "", "", "", ""],
                ["Sample", f"{source[0]}", "empty", "", "Sample p", f"{results['sample_p']:.2f}"],
                ["Alpha-Level", f"{alphalevel}", "empty", "", "", f"({results['ci_95_lower']:.4f};{results['ci_95_upper']:.4f})"],
                ["Interested\ndifference**", f"{results['interested_difference']}", "empty", hypothesis_string, "", ""],
                ["", "", "", "", "", ""]
            ]
            # Set the column widths as needed
            col_widths = [0.15, 0.15, 0.15, 0.15, 0.15, 0.15]

            bg_colors = [
                [grey, grey, grey, grey, grey, grey],
                ["#ffffff", "#ffffff", lightgreen_table, "#ffffff", "#ffffff", "#ffffff"],
                ["#ffffff", "#ffffff", green_table, "#ffffff", "#ffffff", table_1_color],
                ["#ffffff", "#ffffff", "#ffffff", grey, grey, grey],
                ["#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff"],
                ["#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff"],
                ["#ffffff", "#ffffff", "#ffffff", table_1_color, table_1_color, table_1_color],
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
                text='Sample p',
                x=1.5,
                y=0.5,
                visible=True,
                ha='right'
            )
            cell_text_centered_3 = table.get_celld()[(5, 4)]
            cell_text_centered_3.set_text_props(
                text=f'{ci_level} CI (confidence interval)',
                x=1.5,
                y=0.5,
                visible=True,
                ha='right'
            )     
            cell_text_centered_4 = table.get_celld()[(3, 4)]
            cell_text_centered_4.set_text_props(
                text='Defective',
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

            # Descriptive Statistics
            ax = axes["Descriptive Statistics"]
            ax.axis('off')
            ax.set_title("Descriptive Statistics", loc='left', pad=-30, y=1.02)
            descriptive_stats = pd.DataFrame({
                "Quelle": source[0],
                "N": [sample_size],
                "Nondefective": [sample_size - defective_count],
                "Defective": [defective_count],
                "Sample p": [sample_p],
                "95% CI for p": [f"({ci_lower*100:.2f};{ci_upper*100:.2f})"]
            })
            table_1_widths = [0.11, 0.06, 0.11, 0.11, 0.11, 0.11, 0.21]
            table_1 = ax.table(
                cellText=descriptive_stats.values,
                colLabels=descriptive_stats.columns,
                colWidths=table_1_widths,
                cellLoc='center',
                loc='center',
                bbox=[0, 0.45, 0.8, 0.2],
            )
            table_1.auto_set_font_size(False)
            table_1.set_fontsize(font_size)

            for cell in table_1._cells.values():
                cell.set_edgecolor(edge_color)
                cell.set_linewidth(0.5)

            # Set the top row color to #e7e6e6
            for col in range(len(descriptive_stats.columns)):
                cell = table_1[(0, col)]
                cell.set_facecolor(grey)


            # Power table
            ax = axes["Power"]
            ax.axis('off')
            ax.set_title("Power and detected difference", loc='left', y=1.2)
            table_data = [
                ["60%", "", "90%"],
                ["", "", ""],
                ["", "", ""],
                [f"{results['detectable_differences']['60%']*100:.2f}", "Difference", f"{results['detectable_differences']['90%']*100:.2f}"],
                [f"For α = {alphalevel} and sample size = {sample_size}:\nIf the true % defective were greater than the target by {round(power_percentage*100, 0)}, you would have a {power_for_your_sample_size}%\nchance of detecting the difference." if power_percentage is not None else f"For α = {alphalevel} and sample size = {sample_size}:\nIf the true % of defectives differed by {results['detectable_differences']['60%']*100:.2f} from the target, you would have a 60% \nchance of detecting the difference. If they differed by {results['detectable_differences']['90%']*100:.2f}, you would have a \n90% chance.", "", ""]
            ]
            bg_colors = [
                [grey, grey, grey],
                ["#c00000", "#f9b002", "#a7c315"],
                ["#ffffff", "#ffffff", "#ffffff"],
                [grey, grey, grey],
                ["#ffffff", "#ffffff", "#ffffff"]
            ]

            table_bg = ax.table(bbox=[0, 0.4, 1, 0.5], cellColours=bg_colors, colWidths=[0.18, 0.44, 0.20])
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
                bbox=[0, 0.4, 1, 0.5],
                cellText=table_data,
                cellLoc='center',
                loc='lower left',
                colWidths=[0.12, 0.17, 0.12],  # Set column widths for the left table
                cellColours=bg_none,
                edges='open',
            )

            for cell in table._cells.values():
                cell.set_linewidth(0.5)


            # Add visible edges to the table
            n_rows, n_cols = 5, 3
            edge_mapping = {
                'top': [(i, j) for i in [0] for j in range(n_cols)],
                'bottom': [(i, j) for i in [n_rows-3, n_rows-2] for j in range(n_cols)],  # Removed n_rows-1
                'left': [(i, 0) for i in range(n_rows-1)],  # Exclude bottom row
                'right': [(i, n_cols-1) for i in range(n_rows-1)]  # Exclude bottom row
            }

            # Apply edges based on position
            for (i, j), cell in table.get_celld().items():
                # Skip edge drawing for bottom row cells
                if i == n_rows-1:
                    continue
                    
                # Initialize with empty edges
                edges = ""
                
                # Add appropriate edges based on cell position
                if (i, j) in edge_mapping['top']: 
                    edges += "T"
                if (i, j) in edge_mapping['bottom']: 
                    edges += "B"
                if (i, j) in edge_mapping['left']: 
                    edges += "L"
                if (i, j) in edge_mapping['right']: 
                    edges += "R"
                
                # Apply the edges if any were defined
                if edges:
                    cell.visible_edges = edges
                    cell.set_edgecolor(edge_color)

            # Configure text alignment for specific cells
            text_alignments = {
                (0, 0): 'right',
                (0, 2): 'left',
                (2, 0): 'right',
                (3, 0): 'right',
                (2, 2): 'left',
                (3, 2): 'left',
                (4, 0): 'left',
            }

            # Apply text alignments
            for pos, alignment in text_alignments.items():
                if pos in table.get_celld():
                    table.get_celld()[pos].set_text_props(ha=alignment)
                

            # Set font size for the table
            table.auto_set_font_size(False)
            table.set_fontsize(font_size)
            # Set fontsize and text properties for bottom row
            table.get_celld()[4, 0].set_fontsize(5)
            table.get_celld()[4, 0].set_text_props(va='top')

            # Add marker for the detected difference
            # Add visual marker representation of power levels
            if power_percentage is not None:
                ax.set_title(f"What is the chance of detecting a difference of {round(power_percentage*100, 0)}?", loc='center', pad=-20, y=1.07, fontsize=font_size)
                power_values = [results['power_for_your_sample_size']]  # The power levels in the table
                marker_values = [results['power_for_your_sample_size']]

                # Create visual markers for the second row of the table
                for i, (power_val, marker_val) in enumerate(zip(power_values, marker_values)):
                    col = i * 2  # Position in columns 0 and 2
                    marker_text = "|"  # Triangle down marker ▼
                    
                    # Determine position based on power value
                    if marker_val < 60:
                        col = 0
                    elif 60 <= marker_val <= 90:
                        col = 1
                    else:
                        col = 2
                    
                    # If power is below 40%, place marker at far left
                    if marker_val < 40 or 60 < marker_val < 70:
                        horizontal_offset = 'left'
                    # If power is above 90%, place marker at far right
                    elif marker_val > 90 or 80 < marker_val < 90:
                        horizontal_offset = 'right'
                    else:
                        horizontal_offset = 'center'
                    
                    # Add the marker to the cell
                    cell = table.get_celld()[(1, col)]
                    # Set x position based on horizontal offset
                    if horizontal_offset == 'left':
                        x_pos = 0.1
                    elif horizontal_offset == 'right':
                        x_pos = 0.9
                    else:
                        x_pos = 0.5
                    cell.set_text_props(text=marker_text, x=x_pos, y=0.5, fontsize=15, weight='bold', ha=horizontal_offset)
                    
                    # Add a text label underneath showing the exact percentage value
                    label_text = f"{marker_val:.1f}%"
                    cell = table.get_celld()[(2, col)]
                    cell.set_text_props(text=label_text, fontsize=8, ha=horizontal_offset)
            else:
                ax.set_title(f"What is the chance of detecting a difference?", loc='center', pad=-20, y=1.07, fontsize=font_size)

            # Difference table
            ax = axes["Difference"]
            ax.axis('off')
            if power_percentage is not None:
                ax.set_title(f"What sample size is required to detect a difference of {power_percentage*100}%?", fontsize=font_size, y=1.1)
                table_data = [
                    [required_n_60, "60%"],
                    [required_n_70, "70%"],
                    [required_n_80, "80%"],
                    [required_n_90, "90%"],
                    ["", ""],
                    ["Your Sample Size", "Power"],
                    [sample_size, f"{results['power_for_your_sample_size']}%"]
                ]
                table_2_widths = [0.18, 0.18]
                table_2 = ax.table(
                    cellText=table_data,
                    colLabels=["Sample Size","Power"],
                    colWidths=table_2_widths,
                    cellLoc='center',
                    loc='center',
                    bbox=[0, 0.1, 1, 1],
                )
                table_2.auto_set_font_size(False)
                table_2.set_fontsize(font_size)
                # remove the border of the table
                for cell in table_2._cells.values():
                    cell.set_edgecolor("none")
                # Add edges below the first line and above the last line
                # Set borders for the first row (header)
                for col in range(len(table_2_widths)):
                    cell = table_2[(0, col)]
                    cell.set_edgecolor(edge_color)
                    cell.set_linewidth(0.5)
                    cell.visible_edges = "B"  # Bottom edge only

                # Set borders for the last row
                for col in range(len(table_2_widths)):
                    cell = table_2[(7, col)]
                    cell.set_edgecolor(edge_color)
                    cell.set_linewidth(0.5)
                    cell.visible_edges = "T"  # Top edge only

                # Set smaller row heights for all rows
                for row, col in table_2._cells.keys():
                    cell = table_2[row, col]
                    cell.set_height(0.06)  # Adjust this value as needed for smaller row heights

                # Set header row to stand out slightly
                for col in range(len(table_2_widths)):
                    cell = table_2[(0, col)]
                    cell.set_facecolor(grey)
            else:
                ax.set_title(f"What difference can you detect with your sample size of {sample_size}?", fontsize=font_size, y=1.1)
                table_data = [
                    [f"{results['detectable_differences']['60%']*100:.2f}", "60%"],
                    [f"{results['detectable_differences']['70%']*100:.2f}", "70%"],
                    [f"{results['detectable_differences']['80%']*100:.2f}", "80%"],
                    [f"{results['detectable_differences']['90%']*100:.2f}", "90%"]
                ]
                table_2_widths = [0.18, 0.18]
                table_2 = ax.table(
                    cellText=table_data,
                    colLabels=["Sample Size","Power"],
                    colWidths=table_2_widths,
                    cellLoc='center',
                    loc='center',
                    bbox=[0, 0.1, 1, 1],
                )
                table_2.auto_set_font_size(False)
                table_2.set_fontsize(font_size)
                # remove the border of the table
                for cell in table_2._cells.values():
                    cell.set_edgecolor("none")
                # Add edges below the first line and above the last line
                # Set borders for the first row (header)
                for col in range(len(table_2_widths)):
                    cell = table_2[(0, col)]
                    cell.set_edgecolor(edge_color)
                    cell.set_linewidth(0.5)
                    cell.visible_edges = "B"  # Bottom edge only

                # Set smaller row heights for all rows
                for row, col in table_2._cells.keys():
                    cell = table_2[row, col]
                    cell.set_height(0.06)  # Adjust this value as needed for smaller row heights

                # Set header row to stand out slightly
                for col in range(len(table_2_widths)):
                    cell = table_2[(0, col)]
                    cell.set_facecolor(grey)

            # Errorbar plot
            ax = axes["Errorbar"]
            ax.set_title(f"{ci_level} CI for % Defective", y=1.15, fontsize=10)
            ax.text(0.5, 1.1, "Is the entire interval above or below the target?", transform=ax.transAxes, ha='center', fontsize=font_size)
            # ax.set_title("Is the entire interval above or below the target?", y=1.02, fontsize=font_size, pad=30)
            ax.errorbar(x=sample_p*100, y=0, xerr=[[(sample_p - ci_lower)*100], [(ci_upper - sample_p)*100]], fmt='o', color='#95b92a', capsize=3, lw=0.7, markersize=3)
            ax.vlines(x=target_p*100, ymin=-0.5, ymax=0.5, colors='grey', linestyles='dashed', alpha=0.7)
            ax.set_ylim(-0.5, 0.5)
            ax.set_yticks([])
            ax.set_position([0.13, 0.1, 0.35, 0.1])
            ax.grid(True, alpha=0.3)


            # Histogram plot
            ax = axes["Histogram"]
            x_max = int(sample_size * target_p + 6 * np.sqrt(sample_size * target_p * (1 - target_p)))
            x_range = np.arange(0, 20)
            binom_props = stats.binom.pmf(x_range, sample_size, target_p)
            ax.set_title(f"Deviation from Expected Defect Rate ({target_p*100}%)", fontsize=10)
            ax.bar(x_range, binom_props, color='#95b92a', label=f"Theoretical Distribution ({target_p*100}% Defect rate)")
            ax.vlines(x=results['defectives'], ymin=0, ymax=max(binom_props), colors='grey', linestyles='dashed', alpha=0.7, label=f"Observed Defects ({results['defectives']})")
            legend = ax.legend()
            # Make the legend smaller
            legend = ax.legend(prop={'size': 4})
            legend.get_frame().set_linewidth(0.5)
            # for text in legend.get_texts():
            #     text.set_fontsize(3)

            ax.set_position([0.55, 0.1, 0.35, 0.2])
            xticks = ax.get_xticks()
            ax.set_xticks(xticks)
            ax.set_xticklabels([f"{x:.2f}" for x in xticks], fontsize=font_size)
            yticks = ax.get_yticks()
            ax.set_yticks(yticks)
            ax.set_yticklabels([f"{y:.2f}" for y in yticks], fontsize=font_size)
            ax.grid(True, alpha=0.3)


            pdf.savefig(fig)
            plt.close(fig)

        pdf_io.seek(0)
        plt.close('all')
        return pdf_io



def _calculate_required_sample_size(target_p, delta, power_level, alphalevel, sample_size):
    """Calculate required sample size for a given power level"""
    alpha = alphalevel  # Standard significance level
    beta = 1 - (power_level/100)  # Convert power percentage to beta
    
    # Using formula for sample size calculation
    z_alpha = stats.norm.ppf(1 - alpha/2)
    z_beta = stats.norm.ppf(1 - beta)
    
    p_avg = (target_p + (target_p + delta)) / 2
    required_n = ((z_alpha + z_beta)**2 * p_avg * (1 - p_avg)) / (delta**2)

    power_for_your_sample_size = {}

    std_error = math.sqrt((target_p * (1 - target_p)) / sample_size)
    z_power = (delta / std_error) - z_alpha
    actual_power = stats.norm.cdf(z_power) * 100
    power_for_your_sample_size = round(actual_power, 1)

    return math.ceil(required_n), power_for_your_sample_size

def _calculate_detectable_difference(target_p, sample_size, power_level, alphalevel):
    """Calculate the minimum detectable difference with the given sample size and power level"""
    alpha = alphalevel
    beta = 1 - (power_level/100)
    
    z_alpha = stats.norm.ppf(1 - alpha/2)
    z_beta = stats.norm.ppf(1 - beta)
    
    # Function to solve for delta
    def equation_to_solve(delta):
        p_avg = (target_p + (target_p + delta)) / 2
        return ((z_alpha + z_beta)**2 * p_avg * (1 - p_avg)) / (delta**2) - sample_size
    
    # Use numerical method to find delta
    # Starting with a reasonable range for delta: 0.001 to 0.5
    try:
        delta = brentq(equation_to_solve, 0.001, 0.5)
        return delta
    except ValueError:
        # If the function doesn't change sign in the interval, try a different approach
        # Use an approximation formula
        p_avg = target_p  # Approximation
        delta = math.sqrt(((z_alpha + z_beta)**2 * p_avg * (1 - p_avg)) / sample_size)
        return delta