import io
import warnings
import numpy as np
import pandas as pd
import scipy.stats as stats
import matplotlib.pyplot as plt
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Tuple
from api.schemas import BusinessLogicException
from matplotlib.backends.backend_pdf import PdfPages

from ...utils.pdf_utils import add_header_or_footer_to_a4_portrait

header_image_path = 'assets/img/Header.png'
footer_image_path = 'assets/img/Footer.png'

from ...utils.mpl_table_utils import merge_mpl_table_cells as mergecells


class MultipleDefectiveTestConfig(BaseModel):
    title: str
    variant: str
    power: Optional[float] = None
    alphalevel: float
    sample_names: Optional[List[str]] = None    # Variant 1 
    sample_size: Optional[List[int]] = None    # Variant 1
    defective_count: Optional[List[int]] = None      # Variant 1
    sample_column: Optional[str] = None     # Variant 2
    defective_name: Optional[str] = None    # Variant 2

class MultipleDefectiveTestData(BaseModel):
    values: Optional[Dict[str, List[str]]] = Field(None)

class MultipleDefectiveTestRequest(BaseModel):
    project: str
    step: str
    config: MultipleDefectiveTestConfig
    data: Optional[MultipleDefectiveTestData] = None

class MultipleDefectiveTest:
    def __init__(self, data: dict):
        try:
            validated_data = MultipleDefectiveTestRequest(**data)
            self.project = validated_data.project
            self.step = validated_data.step
            self.config = validated_data.config
            self.data = validated_data.data
            
            # Determine which format is being used
            variant = self.config.variant
            
            # Validation for "Summarized data" format
            if variant == "Summarized data":
                if self.config.sample_names is None or self.config.sample_size is None or self.config.defective_count is None:
                    raise BusinessLogicException(
                        error_code="error_validation",
                        field="configuration_parameters",
                        details={
                            "message": "For 'Summarized data' variant, sample_names, sample_size, and defective_count are required."
                        }
                    )
                # Check that arrays have matching lengths
                if len(self.config.sample_names) != len(self.config.sample_size) or len(self.config.sample_size) != len(self.config.defective_count):
                    raise BusinessLogicException(
                        error_code="error_validation",
                        field="configuration_parameters",
                        details={
                            "message": "sample_names, sample_size, and defective_count must have the same length."
                        }
                    )
                    
            # Validation for "All data in one column" format
            elif variant == "All data in one column":
                if self.config.sample_column is None or self.config.defective_name is None:
                    raise BusinessLogicException(
                        error_code="error_validation",
                        field="configuration_parameters",
                        details={
                            "message": "For 'All data in one column' variant, sample_column and defective_name are required."
                        }
                    )
                if self.data is None or self.data.values is None:
                    raise BusinessLogicException(
                        error_code="error_validation",
                        field="data",
                        details={"message": "Data values are required for 'All data in one column' variant."}
                    )
                # Check if the specified columns exist in the data
                if self.config.sample_column not in self.data.values:
                    raise BusinessLogicException(
                        error_code="error_validation",
                        field="sample_column",
                        details={"message": f"Column '{self.config.sample_column}' not found in data."}
                    )
                
                # Need at least one more column for the values
                value_columns = [col for col in self.data.values.keys() if col != self.config.sample_column]
                if not value_columns:
                    raise BusinessLogicException(
                        error_code="error_validation",
                        field="data.values",
                        details={"message": "At least one value column is required in addition to the sample_column."}
                    )
                
            # Validation for "Each data in its own column" format
            else:  # "Each data in its own column"
                if self.config.defective_name is None:
                    raise BusinessLogicException(
                        error_code="error_validation",
                        field="defective_name",
                        details={"message": "defective_name is required for 'Each data in its own column' variant."}
                    )
                if self.data is None or self.data.values is None:
                    raise BusinessLogicException(
                        error_code="error_validation",
                        field="data",
                        details={"message": "Data values are required for 'Each data in its own column' variant."}
                    )
                # Need to ensure we have at least 2 columns
                if len(self.data.values) < 2:
                    raise BusinessLogicException(
                        error_code="error_validation",
                        field="data.values",
                        details={"message": "At least 2 data columns are required."}
                    )
            
        except Exception as e:
            raise BusinessLogicException(
                error_code="error_validation",
                field=str(e),
                details={"message": f"Invalid or missing field: {str(e)}"}
            )
            
    def process(self):
        title = self.config.title
        variant = self.config.variant
        power = self.config.power if self.config.power is not None else None
        alphalevel = self.config.alphalevel
        defective_name = self.config.defective_name

        # Extract or calculate sample sizes and defect counts based on variant
        sources = []
        counts = []
        fails = []
        
        if variant == "Summarized data":
            # Data is already provided in the config
            sources = self.config.sample_names
            counts = self.config.sample_size
            fails = self.config.defective_count
        
        elif variant == "All data in one column":
            # Need to process data by sample groups
            sample_column = self.config.sample_column
            value_column = [col for col in self.data.values.keys() if col != sample_column][0]  # Get first value column
            
            # Get unique sample names
            unique_samples = list(set(self.data.values[sample_column]))
            sources = unique_samples
            
            # For each unique sample, count total values and defectives
            for sample in unique_samples:
                # Get indices for this sample
                indices = [i for i, s in enumerate(self.data.values[sample_column]) if s == sample]
                
                # Count total non-empty values for this sample
                valid_values = [self.data.values[value_column][i] for i in indices if self.data.values[value_column][i]]
                counts.append(len(valid_values))
                
                # Count defectives
                defective_count = sum(1 for i in indices 
                                if self.data.values[value_column][i] == defective_name)
                fails.append(defective_count)
        
        else:  # "Each data in its own column"
            # Each column is a separate data set
            for col_name, values in self.data.values.items():
                sources.append(col_name)
                # Count non-empty values
                valid_values = [v for v in values if v]
                counts.append(len(valid_values))
                # Count defectives
                fails.append(sum(1 for v in valid_values if v == defective_name))
        
        # Number of samples
        sample_num = len(sources)
        
        # Count passes and calculate defective rates
        passes = [counts[i] - fails[i] for i in range(sample_num)]
        defectives = [fails[i] / counts[i] if counts[i] > 0 else 0 for i in range(sample_num)]

        # Continue with your existing code...
        # Join sources with newlines for display
        sources_str = ", ".join(sources[:2]) + "\n" + ", ".join(sources[2:]) if len(sources) > 2 else ", ".join(sources)
        
        # Calculate test results
        results = _calculate_multiple_proportion_test(
            sample_sizes=counts, 
            defect_counts=fails, 
            alpha=alphalevel, 
            power_level=power
        )

        if variant == "Each data in its own column":
            variant_str = "Each data in its own column"
        else:
            variant_str = "Summarized data"

        # results = _calculate_multiple_proportion_test(sample_sizes=counts, defect_counts=fails, alpha=alphalevel, power_level=power)

        # Hypothesis test verdict
        if results['statistics']['p_value'] < alphalevel:
            hypothesis_string = f"The % Defective value from minimum one sample is\nsignificantly different from target"
            table_1_color = "#9cc563"
        else:
            hypothesis_string = f"The % Defective value from all samples is not\nsignificantly different from target"
            table_1_color = "#d6ed5f"

        # Summary for descriptive statistics table
        stats_summary = [
                [
                    sources[i],
                    results['groups'][i]['sample_size'],
                    results['groups'][i]['defects'],
                    f"{results['overall']['overall_defect_rate']*100:.2f}",
                    results['groups'][i]['sample_size'] - results['groups'][i]['defects'],
                    f"{results['groups'][i]['sample_size'] - results['overall']['overall_defect_rate']*100:.2f}",
                    f"{results['groups'][i]['defect_rate']*100:.2f}",
                    f"({results['groups'][i]['ci_95']['wilson']['lower']*100:.2f}; {results['groups'][i]['ci_95']['wilson']['upper']*100:.2f})"
                ]
                for i in range(sample_num)
            ]

        # Create PDF
        pdf_io = io.BytesIO()

        with PdfPages(pdf_io) as pdf:
            # NEW PDF PAGE - T-Test results, Descriptive Statistics, Data Time Series
            fig, axes = plt.subplot_mosaic([
                ["Defective-Test Results", "Defective-Test Results"],
                ["Descriptive Statistics", "Descriptive Statistics"],
                ["Power", "Difference"],         # Time Series Plots for each dataset
                ["Comparison Chart", "Pie Charts"]],    # Chance and Detectable Difference
                figsize=(8.27, 11.69), dpi=300)  # A4 size in inches
            #fig.subplots_adjust(hspace=0.4)  # Increase hspace to add more space between charts
            # fig.suptitle(title, fontsize=16, weight='bold', y=0.94)
            header_ax = add_header_or_footer_to_a4_portrait(fig, header_image_path, position='header')
            footer_ax = add_header_or_footer_to_a4_portrait(fig, footer_image_path, position='footer', page_number=1, total_pages=1)

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
                ["Configuration", "", "Hypothesis", "", ""],
                [variant_str, "", r"$\mathrm{H_{0}}:$ all $p_{i} = p_{j}$", "p-Value*", f"{results['statistics']['p_value']:.3f}"],
                ["Test-Setup", "Different", r"$\mathrm{H_{1}}:$ one $p_{i} \neq p_{j}$", "Number defects", results['overall']['total_defects']],
                ["Samples", f"{sources_str}", "", "Number samples", results['overall']['total_samples']],
                [ "", "", "empty", "Total defect percentage", f"{results['overall']['overall_defect_rate']*100:.2f}"],
                ["Alpha-Level", f"{alphalevel}", "empty", f"Expected defects = N * {results['overall']['overall_defect_rate']*100:.4f}\nExpected nondefects = N - (expected defects)" , ""],
                ["Interested\ndifference**", f"{power*100 if power is not None else '-'}%", "empty", hypothesis_string, ""],
                ["", "", "", "", ""]
            ]
            # Set the column widths as needed
            col_widths = [0.15, 0.15, 0.15, 0.25, 0.25]

            bg_colors = [
                [grey, grey, grey, grey, grey],
                ["#ffffff", "#ffffff", lightgreen_table, "#ffffff", table_1_color],
                ["#ffffff", "#ffffff", green_table, "#ffffff", "#ffffff"],
                ["#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff",],
                ["#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff"],
                ["#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff"],
                ["#ffffff", "#ffffff", "#ffffff", table_1_color, table_1_color],
                ["#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff"]
            ]
            table_bg = ax.table(bbox=[0, 0, 1, 1], cellColours=bg_colors, colWidths=col_widths)
            for cell in table_bg._cells.values(): 
                cell.set_edgecolor("none")

            bg_none = [
                ["none", "none", "none", "none", "none", ],
                ["none", "none", "none", "none", "none", ],
                ["none", "none", "none", "none", "none", ],
                ["none", "none", "none", "none", "none", ],
                ["none", "none", "none", "none", "none", ],
                ["none", "none", "none", "none", "none", ],
                ["none", "none", "none", "none", "none", ],
                ["none", "none", "none", "none", "none", ]
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
            mergecells(table, [(1, 0), (1, 1)])
            mergecells(table, [(0, 3), (0, 4)])
            mergecells(table, [(3, 0), (4, 0)])
            mergecells(table, [(3, 1), (4, 1)])
            mergecells(table, [(5, 3), (5, 4)])
            mergecells(table, [(3, 2), (4, 2), (5, 2), (6, 2)])
            mergecells(table, [(6, 3), (6, 4)])
            mergecells(table, [(7, 0), (7, 1), (7, 2), (7, 3), (7, 4)])

            table.get_celld()[7, 0].set_fontsize(5)
            table.get_celld()[5, 3].set_fontsize(6)

            cell_text_centered_1 = table.get_celld()[(0, 3)]
            cell_text_centered_1.set_text_props(
                text='Results',
                x=1.5,
                y=0.5,
                visible=True,
                ha='right'
            )
            cell_text_small = table.get_celld()[(7, 0)]
            cell_text_small.set_text_props(
                text='* If the p-value is less than the α-level, then H0 is to be rejected and the alternative hypothesis H1 is to be accepted.\n  (The normal approximation may be inaccurate for small samples) \n** Optional: What difference between the two means has a practical value? (Power and sample size)',
                visible=True,
                color='grey',
                ha='right'
            )
            bold_text = [(2, 1), (1, 3)]
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

            cell = table.get_celld()[(3, 1)]
            cell.set_text_props(va='top', fontsize=6)

            # Descriptive Statistics
            ax = axes["Descriptive Statistics"]
            ax.axis('off')
            ax.set_title("Descriptive Statistics", loc='left', pad=-50, y=1.1)
            descriptive_table_labels = ["Source", "N", f"Observed\nDefective", f"Expected\nDefective", f"Observed\nNondefective", f"Expected\nNondefective", f"%Defective", f"{(1-alphalevel)*100:.0f}% CI\nfor defective"]
            descriptive_table_widths = [0.18, 0.06, 0.13, 0.13, 0.16, 0.16, 0.13, 0.16]
            descriptive_table = ax.table(
                cellText=stats_summary,
                colLabels=descriptive_table_labels,
                colWidths=descriptive_table_widths,
                cellLoc="center",
                loc="upper left",
                bbox=[0, 0.2, 1, 0.5]
            )
            descriptive_table.auto_set_font_size(False)
            descriptive_table.set_fontsize(font_size)

            for cell in descriptive_table._cells.values():
                cell.set_edgecolor(edge_color)
                cell.set_linewidth(0.5)

            # Set the top row color to #e7e6e6
            for col in range(len(descriptive_table_labels)):
                cell = descriptive_table[(0, col)]
                cell.set_facecolor(grey)

            # Change the height of the first row
            for (row, col), cell in descriptive_table.get_celld().items():
                if row == 0:  # Target the first row (including headers if present)
                    cell.set_height(0.20)
                else:
                    cell.set_height(0.15)

            ax = axes["Power"]
            ax.axis('off')
            ax.set_title("Power and detected difference", loc='left', y=1.2)
            table_data = [
                ["60%", "", "90%"],
                ["", "", ""],
                ["", "", ""],
                [f"{results['power_analysis']['detectable_differences']['60%']:.2f}", "Difference", f"{results['power_analysis']['detectable_differences']['90%']:.2f}"],
                [f"For α = {alphalevel} and sample size = {results['groups'][1]['sample_size']}:\nIf the true % defective were greater than the target by {round(power*100, 0)}, you would have a {power}%\nchance of detecting the difference." if power is not None else f"For α = {alphalevel} and sample size = {results['groups'][1]['sample_size']}:\nIf the true % of defectives differed by {results['power_analysis']['detectable_differences']['60%']*100:.2f} from the target, you would have a 60% \nchance of detecting the difference. If they differed by {results['power_analysis']['detectable_differences']['90%']*100:.2f}, you would have a \n90% chance.", "", ""]
            ]
            bg_colors = [
                [grey, grey, grey],
                ["#c00000", "#f9b002", "#a7c315"],
                ["#ffffff", "#ffffff", "#ffffff"],
                [grey, grey, grey],
                ["#ffffff", "#ffffff", "#ffffff"]
            ]

            table_bg = ax.table(bbox=[0, 0.3, 1, 0.5], cellColours=bg_colors, colWidths=[0.18, 0.44, 0.20])
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
                bbox=[0, 0.3, 1, 0.5],
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
            if power is not None:
                ax.set_title(f"What is the chance of detecting a difference of {round(power*100, 0)}?", loc='center', pad=-20, y=1.0, fontsize=font_size)
                power_values = [results['power_analysis']['current_power']*100]  # The power levels in the table
                marker_values = [results['power_analysis']['current_power']*100]

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
                ax.set_title(f"What is the chance of detecting a difference?", loc='center', pad=-20, y=1.0, fontsize=font_size)


            ax = axes["Difference"]
            ax.axis('off')
            if power is not None:
                ax.set_title(f"What sample sizes are required to detect a difference\nof {power*100}?", fontsize=font_size)
                table_data = [
                    [results['power_analysis']['required_total_sample_sizes']['60%'], "60%"],
                    [results['power_analysis']['required_total_sample_sizes']['70%'], "70%"],
                    [results['power_analysis']['required_total_sample_sizes']['80%'], "80%"],
                    [results['power_analysis']['required_total_sample_sizes']['90%'], "90%"],
                    ["", ""],
                    ["Your Sample Size", "Power"],
                    [results['groups'][1]['sample_size'], f"{results['power_analysis']['current_power']*100:.0f}%"]
                ]
                colLabels = ["Sample Size", "Power"]

            else:
                ax.set_title(f"What difference can you detect with your sample of {results['groups'][0]['sample_size']}?", fontsize=font_size)
                table_data = [
                    [results['power_analysis']['detectable_differences']['60%'].round(2), "60%"],
                    [results['power_analysis']['detectable_differences']['70%'].round(2), "70%"],
                    [results['power_analysis']['detectable_differences']['80%'].round(2), "80%"],
                    [results['power_analysis']['detectable_differences']['90%'].round(2), "90%"]
                ]
                colLabels = ["Difference", "Power"]
            table_2_widths = [0.18, 0.18]
            table_2 = ax.table(
                cellText=table_data,
                colLabels=colLabels,
                colWidths=table_2_widths,
                cellLoc='center',
                loc='center',
                bbox=[0.1, 0.1, 0.8, 0.8],  # Reduced bbox height to compress the table vertically
            )
            table_2.auto_set_font_size(False)
            table_2.set_fontsize(font_size)
            # remove the border of the table
            for cell in table_2._cells.values():
                cell.set_edgecolor("none")
            # Add edges below the first line and above the last line
            for col in range(len(table_2_widths)):
                cell = table_2[(0, col)]
                cell.set_edgecolor(edge_color)
                cell.set_linewidth(0.5)
                cell.visible_edges = "B"  # Bottom edge only

            # Set smaller row heights for all rows
            for row, col in table_2._cells.keys():
                cell = table_2[row, col]
                cell.set_height(0.04)  # Reduced from 0.06 to make rows closer together

            # Set header row to stand out slightly
            for col in range(len(table_2_widths)):
                cell = table_2[(0, col)]
                cell.set_facecolor(grey)

            if power is not None:
                for col in range(len(table_2_widths)):
                    cell = table_2[(len(table_data), col)]
                    cell.set_edgecolor(edge_color)
                    cell.set_linewidth(0.5)
                    cell.visible_edges = "T"  # Top edge only

            ax = axes["Comparison Chart"]
            ax.set_title(f"% Defectives Comparison Chart\nOrange intervals do not overlap", fontsize=font_size, pad=-20, y=1.15)

            # Extract defect rates and confidence intervals
            defect_rates = [results['groups'][i]['defect_rate'] for i in range(sample_num)]
            lower_bounds = [results['groups'][i]['ci_95']['wilson']['lower'] for i in range(sample_num)]
            upper_bounds = [results['groups'][i]['ci_95']['wilson']['upper'] for i in range(sample_num)]

            # Calculate error bars (distance from point to CI bounds)
            xerr = [[defect_rates[i] - lower_bounds[i] for i in range(sample_num)], 
                [upper_bounds[i] - defect_rates[i] for i in range(sample_num)]]

            # Check for non-overlapping intervals
            overlapping = [[True for _ in range(sample_num)] for _ in range(sample_num)]
            for i in range(sample_num):
                for j in range(i+1, sample_num):
                    # Check if intervals overlap
                    if upper_bounds[i] < lower_bounds[j] or upper_bounds[j] < lower_bounds[i]:
                        overlapping[i][j] = False
                        overlapping[j][i] = False

            # Plot horizontal error bars with points
            y_positions = range(sample_num, 0, -1)  # Position points from top to bottom
            
            # Plot each point individually to apply the right color
            for i in range(sample_num):
                # Check if this interval doesn't overlap with any other
                has_non_overlapping = any(not overlapping[i][j] for j in range(sample_num) if i != j)
                color = 'orange' if has_non_overlapping else '#95b92a'
                
                ax.errorbar(
                    defect_rates[i] * 100,  # Convert to percentage
                    y_positions[i],
                    xerr=[[xerr[0][i] * 100], [xerr[1][i] * 100]],  # Convert to percentage
                    fmt='o',
                    color=color,
                    capsize=0,
                    linewidth=0.5,
                    markersize=3
                )

            # Set y-ticks as source names

            ax.set_yticks(y_positions)
            ax.set_yticklabels(sources)

            # Set x-axis label and limits
            ax.set_xlabel('Defect Rate (%)', fontsize=font_size+1)
            x_min = max(0, min(lower_bounds) * 100 - 5)  # Convert to percentage
            x_max = min(100, max(upper_bounds) * 100 + 5)  # Convert to percentage
            ax.set_xlim(x_min, x_max)
            ax.set_position([0.15, 0.1, 0.3, 0.2])
            ax.grid(True, alpha=0.3)

            ax = axes["Pie Charts"]
            ax.axis('off')
            ax.set_title(f"Pie Chart of {', '.join(sources[i] for i in range(sample_num))}", fontsize=font_size, y=1.1)
            pie_positions = [(0.25, 0.75), (0.75, 0.75), (0.25, 0.1), (0.75, 0.1)]
            for i in range(sample_num):
                defects = results['groups'][i]['defects']
                sample_size = results['groups'][i]['sample_size']
                position = pie_positions[i % 4]
                ax_inset = ax.inset_axes([position[0] - 0.25, position[1] - 0.25, 0.5, 0.5])
                wedges, texts = ax_inset.pie(
                    [defects, sample_size - defects], 
                    startangle=90, 
                    colors=['orange', '#95b92a'],
                    wedgeprops={'edgecolor': 'black', 'linewidth': 0.5}
                )
                ax_inset.set_title(f"{sources[i]}", fontsize=8)
            
            pdf.savefig(fig)
            plt.close(fig)

        pdf_io.seek(0)
        plt.close('all')
        return pdf_io



# Checken, obs alle berechnungen in _calculate_multiple_propotion_test braucht.
def _calculate_multiple_proportion_test(
    sample_sizes: List[int],
    defect_counts: List[int],
    alpha: float,
    power_level: Optional[float] = None
) -> Dict:
    """
    Performs a multiple-sample percentage defective test using chi-square.
    
    Args:
        sample_sizes: List of sample sizes for each group
        defect_counts: List of defect counts for each group
        alpha: Float of Alphalevel
        power_level: Optional power level for sample size calculation (percentage)
        
    Returns:
        Dictionary containing test results
    """
    # Validate inputs   
    if len(sample_sizes) != len(defect_counts):
        raise ValueError("Sample sizes and defect counts must have the same length")
    if any(d > n for n, d in zip(sample_sizes, defect_counts)):
        raise ValueError("Defect counts cannot exceed sample sizes")
        
    # Add new validation
    if any(n == 0 for n in sample_sizes):
        raise BusinessLogicException(
            error_code="error_validation",
            field="sample_sizes",
            details={"message": "Sample sizes must be greater than zero"}
        )
    
    if all(d == 0 for d in defect_counts):
        raise BusinessLogicException(
            error_code="error_validation",
            field="defect_counts",
            details={"message": "At least one group must have defects"}
        )
    
    if all(d == n for d, n in zip(defect_counts, sample_sizes)):
        raise BusinessLogicException(
            error_code="error_validation",
            field="defect_counts",
            details={"message": "At least one group must have non-defects"}
        )
    
    # Perform the chi-square test
    
    # Calculate defect rates for each group
    defect_rates = [d / n if n > 0 else 0 for n, d in zip(sample_sizes, defect_counts)]
    
    # Calculate confidence intervals for each group's defect rate
    confidence_intervals = [0] * len(defect_counts)
    for i in range(len(defect_counts)):
        confidence_intervals[i] = _calculate_wilson_ci(defect_counts[i], sample_sizes[i], 1-alpha)

    # Calculate overall statistics
    total_samples = sum(sample_sizes)
    total_defects = sum(defect_counts)
    overall_defect_rate = total_defects / total_samples if total_samples > 0 else 0
    
    # Calculate confidence intervals for overall defect rate
    overall_ci = _calculate_wilson_ci(total_defects, total_samples, 1-alpha)
    
    # Calculate expected defects under the null hypothesis (all groups have the same defect rate)
    expected_defects = [overall_defect_rate * n for n in sample_sizes]
    expected_nondefects = [n - e for n, e in zip(sample_sizes, expected_defects)]
    
    # Prepare contingency table for chi-square test
    observed = np.array([defect_counts, [n - d for n, d in zip(sample_sizes, defect_counts)]])
    
    # Check if any expected frequencies would be too small
    row_sums = observed.sum(axis=1)
    col_sums = observed.sum(axis=0)
    total = observed.sum()
    
    expected = np.outer(row_sums, col_sums) / total
    if (expected < 5).any():
        # Use Fisher's exact test for small expected frequencies
        # or return a warning that the chi-square approximation may be unreliable
        warnings.warn("Expected frequencies less than 5 detected - chi-square results may be unreliable")
    
    # Chi-square test
    try:
        chi2, p_value, dof, expected = stats.chi2_contingency(observed)
    except ValueError as e:
        raise BusinessLogicException(
            error_code="error_calculation",
            field="chi_square_test",
            details={"message": "Cannot perform chi-square test - check your data for extreme values or small samples"}
        )
    
    # Chi-square test
    chi2, p_value, dof, expected = stats.chi2_contingency(observed)
    
    # Calculate power for detecting differences at various effect sizes
    power_analysis = _calculate_power_analysis(
        sample_sizes, 
        defect_rates, 
        overall_defect_rate,
        alpha, 
        power_level
    )
    
    # Prepare group-specific results
    groups = []
    for i, (n, d, rate, ci) in enumerate(zip(sample_sizes, defect_counts, defect_rates, confidence_intervals)):
        groups.append({
            "group": f"Group_{i+1}",
            "sample_size": n,
            "defects": d,
            "defect_rate": rate,
            "ci_95": {
                "wilson": {"lower": ci[0], "upper": ci[1]}
            }
        })
    
    # Prepare results
    results = {
        "groups": groups,
        "overall": {
            "total_samples": total_samples,
            "total_defects": total_defects,
            "overall_defect_rate": overall_defect_rate,
            "overall_ci_95": {
                "wilson": {"lower": overall_ci[0], "upper": overall_ci[1]}
            }
        },
        "expected": {
            "defects": [round(e, 2) for e in expected_defects],
            "nondefects": [round(e, 2) for e in expected_nondefects]
        },
        "statistics": {
            "chi2": chi2,
            "p_value": p_value,
            "degrees_of_freedom": dof
        },
        "power_analysis": power_analysis
    }
    
    return results

def _calculate_wilson_ci(successes: int, n: int, confidence: float) -> Tuple[float, float]:
    """
    Calculate Wilson score interval for a binomial proportion.
    
    Args:
        successes: Number of successes (defects in this case)
        n: Total number of trials
        confidence: Confidence level (e.g., 0.95 for 95% CI)
        
    Returns:
        Tuple containing lower and upper bounds of the confidence interval
    """
    if n == 0:
        return 0, 0
        
    # Get z value for the desired confidence level
    z = stats.norm.ppf(1 - (1 - confidence) / 2)
    
    # Calculate proportion
    p_hat = successes / n
    
    # Wilson score calculation
    denominator = 1 + (z**2 / n)
    center = (p_hat + z**2 / (2 * n)) / denominator
    interval = z * np.sqrt(p_hat * (1 - p_hat) / n + z**2 / (4 * n**2)) / denominator
    
    lower = max(0, center - interval)
    upper = min(1, center + interval)
    
    return lower, upper


def _calculate_power_analysis(
    sample_sizes: List[int], 
    observed_rates: List[float],
    overall_rate: float,
    alpha: float,
    power: Optional[float] = None
) -> Dict:
    """
    Calculates power analysis statistics for multiple proportions.
    
    Args:
        sample_sizes: List of sample sizes for each group
        observed_rates: List of observed defect rates for each group
        overall_rate: Overall defect rate across all groups
        alpha: Alphalevel specified by the user
        power: Target difference to detect (percentage)
        
    Returns:
        Dictionary with power analysis results
    """
    # Calculate effect size (using Cohen's w)
    # w = sqrt(sum((p_i - p)^2 / p) for each group proportion p_i with overall proportion p
    effect_size = 0
    if overall_rate > 0 and overall_rate < 1:
        effect_size = np.sqrt(sum(
            sample_sizes[i] * (rate - overall_rate)**2 / (overall_rate * (1 - overall_rate))
            for i, rate in enumerate(observed_rates)
        ) / sum(sample_sizes))
    
    # Calculate power for different sample sizes (if a difference is specified)
    required_sample_sizes = {}
    power_levels = [0.6, 0.7, 0.8, 0.9]  # 60%, 70%, 80%, 90%
    
    if power is not None:
        Z_alpha = stats.norm.ppf(1 - alpha/2)

        # Calculate the statistical power for the current sample size
        total_n = sum(sample_sizes)
        Z_beta = (power * np.sqrt(total_n) / np.sqrt(2 * overall_rate * (1 - overall_rate))) - Z_alpha
        current_power = stats.norm.cdf(Z_beta)

        for p in power_levels:
            Z_beta = stats.norm.ppf(p)
            n = 2 * ((Z_alpha + Z_beta) ** 2 * overall_rate * (1 - overall_rate) / (power**2))
            n_total = np.ceil(n)
            
            # Store result
            required_sample_sizes[f"{int(p*100)}%"] = int(n_total)
    
    # Calculate minimum detectable effect size for the current sample sizes
    min_detectable_effects = {}
    total_n = sum(sample_sizes)
    
    for power_level in power_levels:
        beta = 1 - power_level
        dof = len(sample_sizes) - 1
        
        # Calculate non-centrality parameter
        lambda_nc = stats.ncx2.ppf(1 - beta, df=dof, nc=0)
        
        # Effect size detectable with current sample size
        w_min = np.sqrt(lambda_nc / total_n)
        
        # Convert to percentage difference
        detectable_diff = w_min * 100
        
        min_detectable_effects[f"{int(power_level*100)}%"] = detectable_diff
    
    result = {
        "observed_effect_size": effect_size,
        "detectable_differences": min_detectable_effects,
        "required_total_sample_sizes": required_sample_sizes
    }
    
    # Add current power calculation if power is provided
    if power is not None:
        result["current_power"] = current_power
    
    return result