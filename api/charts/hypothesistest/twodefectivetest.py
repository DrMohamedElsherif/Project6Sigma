import io
import numpy as np
import pandas as pd
import scipy.stats as stats
import matplotlib.pyplot as plt
from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Optional, Union
from api.schemas import BusinessLogicException
from matplotlib.backends.backend_pdf import PdfPages

from ...utils.pdf_utils import add_header_or_footer_to_a4_portrait

header_image_path = 'assets/img/Header.png'
footer_image_path = 'assets/img/Footer.png'

from ...utils.mpl_table_utils import merge_mpl_table_cells as mergecells


class TwoDefectiveTestConfig(BaseModel):
    title: str
    variant: str
    power: Optional[float] = None
    alphalevel: float
    # For all formats
    sample_names: Optional[List[str]] = None           # Optional sample names
    # For variant 1 (Summarized data)
    sample_size: Optional[List[int]] = None            # Variant 1
    defective_count: Optional[List[int]] = None        # Variant 1
    # For variant 2 ("All data in one column")
    sample_columns: Optional[List[str]] = None         # Variant 2/3
    sample_column: Optional[str] = None                # Variant 2
    defective_name: Optional[str] = None               # Variant 2/3

    @field_validator('sample_size', 'defective_count')
    def validate_list_length(cls, v, values):
        if v is not None and len(v) != 2:
            raise ValueError(f"Must contain exactly 2 values")
        return v

class TwoDefectiveTestData(BaseModel):
    values: Optional[Dict[str, List[str]]] = Field(None)

class TwoDefectiveTestRequest(BaseModel):
    project: str
    step: str
    config: TwoDefectiveTestConfig
    data: Optional[TwoDefectiveTestData] = None

class TwoDefectivetest:
    def __init__(self, data: dict):
        try:
            validated_data = TwoDefectiveTestRequest(**data)
            self.project = validated_data.project
            self.step = validated_data.step
            self.config = validated_data.config
            self.data = validated_data.data
            
            # Determine which format is being used
            variant = self.config.variant
            
            # Validation for "Summarized data" format
            if variant == "Summarized data":
                if self.config.sample_size is None or self.config.defective_count is None:
                    raise BusinessLogicException(
                        error_code="error_validation",
                        field="configuration_parameters",
                        details={
                            "message": "For 'Summarized data' variant, sample_size and defective_count are required."
                        }
                    )
                # Set default sample names if not provided
                if self.config.sample_names is None:
                    self.config.sample_names = ["Sample 1", "Sample 2"]
                    
            # Validation for "All data in one column" format
            elif variant == "All data in one column":
                if self.config.sample_columns is None or len(self.config.sample_columns) != 2 or self.config.defective_name is None:
                    raise BusinessLogicException(
                        error_code="error_validation",
                        field="configuration_parameters",
                        details={
                            "message": "For 'All data in one column' variant, sample_columns (with 2 columns) and defective_name are required."
                        }
                    )
                if self.data is None or self.data.values is None:
                    raise BusinessLogicException(
                        error_code="error_validation",
                        field="data",
                        details={"message": "Data values are required for 'All data in one column' variant."}
                    )
                # Check if the specified columns exist in the data
                for column in self.config.sample_columns:
                    if column not in self.data.values:
                        raise BusinessLogicException(
                            error_code="error_validation",
                            field=f"sample_columns.{column}",
                            details={"message": f"Column '{column}' not found in data."}
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
                # If sample_columns is not provided, use the keys from data.values
                if self.config.sample_columns is None:
                    if len(self.data.values) != 2:
                        raise BusinessLogicException(
                            error_code="error_validation",
                            field="data.values",
                            details={"message": "Exactly 2 data columns are required."}
                        )
                    self.config.sample_columns = list(self.data.values.keys())
                else:
                    # Check if the specified columns exist in the data
                    for column in self.config.sample_columns:
                        if column not in self.data.values:
                            raise BusinessLogicException(
                                error_code="error_validation",
                                field=f"sample_columns.{column}",
                                details={"message": f"Column '{column}' not found in data."}
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
        
        # Initialize variables
        count1 = count2 = fails1 = fails2 = source_1 = source_2 = None
        
        # Process data based on the variant
        if variant == "Summarized data":
            # Use the summarized data directly
            count1 = self.config.sample_size[0]
            count2 = self.config.sample_size[1]
            fails1 = self.config.defective_count[0]
            fails2 = self.config.defective_count[1]
            source_1 = self.config.sample_names[0] if self.config.sample_names else "Sample 1"
            source_2 = self.config.sample_names[1] if self.config.sample_names else "Sample 2"
            
        elif variant == "All data in one column":
            # Extract data from columns - one column contains values, another identifies the sample
            value_column = self.config.sample_columns[0]
            sample_column = self.config.sample_columns[1]
            defective_name = self.config.defective_name
            
            values = list(self.data.values[value_column])
            samples = list(self.data.values[sample_column])
            
            # Find unique sample names
            unique_samples = list(set(samples))
            if len(unique_samples) != 2:
                raise BusinessLogicException(
                    error_code="error_validation",
                    field="sample_column",
                    details={"message": f"Expected exactly 2 unique sample values, got {len(unique_samples)}."}
                )
            
            source_1 = unique_samples[0]
            source_2 = unique_samples[1]
            
            # Count samples and defectives
            values1 = [values[i] for i in range(len(values)) if samples[i] == source_1]
            values2 = [values[i] for i in range(len(values)) if samples[i] == source_2]
            
            count1 = len(values1)
            count2 = len(values2)
            fails1 = values1.count(defective_name)
            fails2 = values2.count(defective_name)
            
        else:  # "Each data in its own column"
            # Get column names from sample_columns or directly from data
            defective_name = self.config.defective_name
            
            if self.config.sample_columns and len(self.config.sample_columns) >= 2:
                source_1 = self.config.sample_columns[0]
                source_2 = self.config.sample_columns[1]
            else:
                source_1 = list(self.data.values.keys())[0]
                source_2 = list(self.data.values.keys())[1]
            
            values1 = list(self.data.values[source_1])
            values2 = list(self.data.values[source_2])
            
            count1 = len(values1)
            count2 = len(values2)
            fails1 = values1.count(defective_name)
            fails2 = values2.count(defective_name)
        
        # Count passes
        passes1 = count1 - fails1
        passes2 = count2 - fails2

        # Calculate defective rates
        defective_1 = fails1 / count1 if count1 > 0 else 0
        defective_2 = fails2 / count2 if count2 > 0 else 0
        defective_diff = defective_1 - defective_2

        # Fisher's exact test
        contingency_table = np.array([[passes1, fails1], [passes2, fails2]])
        fisher_p_value = stats.fisher_exact(contingency_table)[1]

        # Normal approximation and z-value
        pooled_ratio = (fails1 + fails2) / (count1 + count2)
        std_error = np.sqrt(pooled_ratio * (1 - pooled_ratio) * (1/count1 + 1/count2))

        if std_error == 0:
            z_value = 0
            normal_p_value = 1
        else:
            z_value = (defective_1 - defective_2) / std_error
            normal_p_value = 2 * (1- stats.norm.cdf(abs(z_value)))

        # Calculate confidence interval based on alpha level
        if alphalevel == 0.1:  # 90% CI
            z_critical = 1.645
            ci_level = "90%"
        elif alphalevel == 0.05:  # 95% CI
            z_critical = 1.96
            ci_level = "95%"
        elif alphalevel == 0.01:  # 99% CI
            z_critical = 2.576
            ci_level = "99%"
        else:
            z_critical = 1.96  # Default to 95% CI
            ci_level = "95%"
            
        std_error_diff = np.sqrt((defective_1 * (1 - defective_1) / count1) + (defective_2 * (1 - defective_2) / count2))
        margin = z_critical * std_error_diff
        ci_lower = defective_diff - margin
        ci_upper = defective_diff + margin

        # Confidence Interval as percentages
        ci_lower_perc = ci_lower*100
        ci_upper_perc = ci_upper*100

        if variant == "Each data in its own column":
            variant_str = "Each data in its own column"
        else:
            variant_str = "Summarized data"

        # Calculate advanced power analysis
        power_analysis = _calculate_power_analysis(defective_1, defective_2, count1, count2, power)

        results = {
            "test_system_1": {
                "count": count1,
                "defects": fails1,
                "defect_rate": defective_1
            },
            "test_system_2": {
                "count": count2,
                "defects": fails2,
                "defect_rate": defective_2
            },
            "difference": {
                "absolute": defective_diff,
                "percent": defective_diff * 100,
                "interested difference": f"{(power*100) if power is not None else '-'}"
            },
            "statistics": {
                "fisher_p_value": fisher_p_value,
                "normal_approx_p_value": normal_p_value,
                "z_value": z_value,
                "ci_95_lower": ci_lower,
                "ci_95_upper": ci_upper,
                "ci_95_lower_perc": ci_lower_perc,
                "ci_95_upper_perc": ci_upper_perc
            },
            "power_analysis": power_analysis
        }
        # Hypothesis test verdict
        if normal_p_value < alphalevel:
            hypothesis_string = f"The % Defective value from ”{source_1}” is significantly\ndifferent from ”{source_2}”"
            table_1_color = "#9cc563"
        else:
            hypothesis_string = f"The % Defective value from ”{source_1}” is not significantly\ndifferent from ”{source_2}”"
            table_1_color = "#d6ed5f"

        # Create PDF
        pdf_io = io.BytesIO()

        with PdfPages(pdf_io) as pdf:
            # NEW PDF PAGE - T-Test results, Descriptive Statistics, Data Time Series
            fig, axes = plt.subplot_mosaic([
                ["Defective-Test Results", "Defective-Test Results"],
                ["Descriptive Statistics", "Descriptive Statistics"],
                ["Power", "Difference"],         # Time Series Plots for each dataset
                ["Errorbar", "Defect Rate Distribution"]],    # Chance and Detectable Difference
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
                ["Configuration", "", "Hypothesis", "", "", ""],
                [variant_str, "", r"$\mathrm{H_{0}}: p_{1} = p_{2}$", "p-Value", "Z-Value", "p-Value*"],
                ["Test-Setup", "Different", r"$\mathrm{H_{0}}: p_{1} \neq p_{2}$", f"{results['statistics']['fisher_p_value']:.3f}", f"{results['statistics']['z_value']:.2f}", f"{results['statistics']['normal_approx_p_value']:.3f}"],
                ["Sample 1", f"{source_1}", "", "", "", ""],
                ["Sample 2", f"{source_2}", "empty", "", "", f"{results['difference']['absolute']:.4f}"],
                ["Alpha-Level", f"{alphalevel}", "empty", "", "", f"({results['statistics']['ci_95_lower']:.4f};{results['statistics']['ci_95_upper']:.4f})"],
                ["Interested\ndifference**", f"{results['difference']['interested difference']}%", "empty", hypothesis_string, "", ""],
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
                text='Difference Sample p',
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
                text='* If the p-value is less than the α-level, then H0 is to be rejected and the alternative hypothesis H1 is to be accepted.\n  (The normal approximation may be inaccurate for small samples) \n** Optional: What difference between the two means has a practical value? (Power and sample size)',
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
            ax.set_title("Descriptive Statistics", loc='left', pad=-50, y=1.1)
            descriptive_stats = pd.DataFrame({
                "Quelle": [source_1, source_2],
                "N": [count1, count2],
                "Nondefective": [passes1, passes2],
                "Defective": [fails1, fails2],
                "Sample p": [f"{defective_1:.3f}", f"{defective_2:.3f}"],
                "Sample p (%)": [f"{(defective_1 * 100):.2f}", f"{(defective_2 * 100):.2f}"],
                f"{ci_level} CI \nfor difference": [f"\n\n({ci_lower_perc:.2f};{ci_upper_perc:.2f})", f"({ci_lower_perc:.2f};{ci_upper_perc:.2f})"]
            })

            descriptive_table_widths = [0.18, 0.06, 0.13, 0.11, 0.11, 0.13, 0.19]
            descriptive_table = ax.table(
                cellText=descriptive_stats.values.tolist(),
                colLabels=list(descriptive_stats.keys()),
                cellLoc="center",
                loc="upper left",
                colWidths=descriptive_table_widths,
                bbox=[0, 0.35, 0.8, 0.35]
            )
            descriptive_table.auto_set_font_size(False)
            descriptive_table.set_fontsize(font_size)

            mergecells(descriptive_table, [(1, 6), (2, 6)])

            for cell in descriptive_table._cells.values():
                cell.set_edgecolor(edge_color)
                cell.set_linewidth(0.5)

            # Set the top row color to #e7e6e6
            for col in range(len(descriptive_stats.columns)):
                cell = descriptive_table[(0, col)]
                cell.set_facecolor(grey)

            # Change the height of the first row
            for (row, col), cell in descriptive_table.get_celld().items():
                if row == 0:  # Target the first row (including headers if present)
                    cell.set_height(0.11)

            ax = axes["Power"]
            ax.axis('off')
            ax.set_title("Power and detected difference", loc='left', y=1.2)
            table_data = [
                ["60%", "", "90%"],
                ["", "", ""],
                ["", "", ""],
                [f"{results['power_analysis']['detectable_differences']['60%']*100:.2f}", "Difference", f"{results['power_analysis']['detectable_differences']['90%']*100:.2f}"],
                [f"For α = {alphalevel} and sample size = {count1}:\nIf the true % defective were greater than the target by {round(power*100, 0)}, you would have a {power}%\nchance of detecting the difference." if power is not None else f"For α = {alphalevel} and sample size = {count1}:\nIf the true % of defectives differed by {results['power_analysis']['detectable_differences']['60%']*100:.2f} from the target, you would have a 60% \nchance of detecting the difference. If they differed by {results['power_analysis']['detectable_differences']['90%']*100:.2f}, you would have a \n90% chance.", "", ""]
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
                power_values = [results['power_analysis']['power_for_your_sample_size']]  # The power levels in the table
                marker_values = [results['power_analysis']['power_for_your_sample_size']]

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
            diff_table_data = []
            if power is not None:
                ax.set_title(f"What sample sizes are required to detect a difference of {power}?", fontsize=font_size)
                required_sample_sizes = results['power_analysis']['required_sample_sizes']
                your_sample_power = results['power_analysis']['power_for_your_sample_size']
                powers = list(required_sample_sizes.keys())
                sample_sizes = list(required_sample_sizes.values())
                values = [f"{size}" for size in sample_sizes]

                diff_table_data = [
                    ["Sample size", "Power"]
                ]

                for i in range(len(powers)):
                    diff_table_data.append([values[i], powers[i]])

                diff_table_data.append(
                    ["", ""]
                )

                diff_table_data.append(
                    ["Your Sample Size", "Power"]
                )
                diff_table_data.append(
                    [count1, f"{your_sample_power:.0f}%"]
                )

            else:
                ax.set_title(f"What difference can you detect with your sample size of {count1}?", fontsize=font_size, pad=-10, y=1.02)
                # Create a table showing detectable differences for different power levels
                detectable_diffs = results['power_analysis']['detectable_differences']
                powers = list(detectable_diffs.keys())
                diff_values = list(detectable_diffs.values())
                values = [f"{diff*100:.2f}" for diff in diff_values]

                # Prepare table data
                diff_table_data = [
                    ["Difference","Power"],
                ]

                for i in range(len(powers)):
                    diff_table_data.append([values[i], powers[i]])

            table_widths = [0.18, 0.18]

            # Create the table
            table = ax.table(cellText=diff_table_data, 
                                loc='center', 
                                cellLoc='center',
                                colWidths=table_widths,
                                bbox=[0.1, 0.2, 0.8, 0.7]
            )

            table.auto_set_font_size(False)
            table.set_fontsize(font_size)
            # remove the border of the table
            for cell in table._cells.values():
                cell.set_edgecolor("none")
            # Add edges below the first line and above the last line
            # Set borders for the first row (header)
            for col in range(len(table_widths)):
                cell = table[(0, col)]
                cell.set_edgecolor(edge_color)
                cell.set_linewidth(0.5)
                cell.visible_edges = "B"  # Bottom edge only
            
            # Set smaller row heights for all rows
            for row, col in table._cells.keys():
                cell = table[row, col]
                cell.set_height(0.06)  # Adjust this value as needed for smaller row heights

            # Set header row to stand out slightly
            for col in range(len(table_widths)):
                cell = table[(0, col)]
                cell.set_facecolor(grey)
            
            if power is not None:
                for col in range(len(table_widths)):
                    cell = table[(len(diff_table_data) - 1, col)]
                    cell.set_edgecolor(edge_color)
                    cell.set_linewidth(0.5)
                    cell.visible_edges = "T"  # Top edge only


            # Errorbar plot
            ax = axes["Errorbar"]
            ax.set_title(f"{ci_level} CI for % Defective", y=1.15, fontsize=10)
            ax.text(0.5, 1.1, "Is the entire interval above or below the target?", transform=ax.transAxes, ha='center', fontsize=font_size)
            # ax.set_title("Is the entire interval above or below the target?", y=1.02, fontsize=font_size, pad=30)
            ax.errorbar(x=defective_diff*100, y=0, xerr=[[(defective_diff*100 - ci_lower_perc)], [(ci_upper_perc - defective_diff*100)]], fmt='o', color='#95b92a', capsize=3, lw=0.7, markersize=3)
            ax.vlines(x=0, ymin=-0.5, ymax=0.5, colors='grey', linestyles='dashed', alpha=0.7)
            ax.set_ylim(-0.5, 0.5)
            ax.set_yticks([])
            ax.set_position([0.13, 0.1, 0.35, 0.1])
            ax.grid(True, alpha=0.3)

            ax = axes["Defect Rate Distribution"]
            # Check if there are enough defects in each sample for a meaningful distribution plot
            if fails1 >= 5 and fails2 >= 5 and (count1 - fails1) >= 5 and (count2 - fails2) >= 5:
                # Set up x range for distributions
                min_rate = min(defective_1, defective_2) - 0.15
                max_rate = max(defective_1, defective_2) + 0.15
                min_rate = max(0, min_rate)  # Ensure non-negative
                max_rate = min(1, max_rate)  # Ensure ≤ 1
                x = np.linspace(min_rate, max_rate, 1000)
                
                # Calculate normal approximation for binomials
                # For sample 1
                std_1 = np.sqrt(defective_1 * (1 - defective_1) / count1)
                y1 = stats.norm.pdf(x, defective_1, std_1)
                
                # For sample 2
                std_2 = np.sqrt(defective_2 * (1 - defective_2) / count2)
                y2 = stats.norm.pdf(x, defective_2, std_2)
                
                # Plot distributions
                ax.plot(x*100, y1, color='#95b92a', label=f"{source_1} ({defective_1*100:.1f}%)")
                ax.plot(x*100, y2, color=plt.cm.Paired(0), label=f"{source_2} ({defective_2*100:.1f}%)")
                
                # Add vertical lines at the means
                ax.axvline(x=defective_1*100, color='#95b92a', linestyle='--', alpha=0.7, linewidth=0.8, label=f"Mean {source_1}")
                ax.axvline(x=defective_2*100, color=plt.cm.Paired(0), linestyle='--', alpha=0.7, linewidth=0.8, label=f"Mean {source_2}")
                
                # Add legend and labels
                ax.legend(fontsize=font_size)
                ax.set_xlabel("Defect Rate (%)", fontsize=font_size)
                ax.set_ylabel("Probability Density", fontsize=font_size)
                ax.set_title("Distribution of Defect Rates", fontsize=10, y=1.15)
                
                # Format axes for readability
                ax.tick_params(axis='both', labelsize=font_size-1)
                ax.grid(True, alpha=0.3)
                
                # Set position to align with the errorbar plot
                ax.set_position([0.54, 0.1, 0.35, 0.2])
            else:
                # Not enough data for a meaningful distribution plot
                ax.axis('off')
                ax.text(0.5, 0.5, "Insufficient data for distribution plot\n(need ≥5 defective and nondefective items per sample)", 
                        ha='center', va='center', fontsize=font_size, 
                        transform=ax.transAxes, color='gray', style='italic')




            pdf.savefig(fig)
            plt.close(fig)

        pdf_io.seek(0)
        plt.close('all')
        return pdf_io

        
def _calculate_power_analysis(p1: float, p2: float, count1: int, count2: int, 
                            power_level: Optional[float] = None) -> Dict:
    """
    Calculates power analysis statistics for two proportions.
    
    Args:
        p1: Proportion of defects in first sample
        p2: Proportion of defects in second sample
        count1: Sample size of first group
        count2: Sample size of second group
        power_level: Target difference to detect (percentage)
        
    Returns:
        Dictionary with power analysis results
    """
    p_pooled = (p1 * count1 + p2 * count2) / (count1 + count2)
    p_avg = (p1 + p2) / 2
    
    # Calculate detectable difference with current sample size for different power levels
    power_levels = [0.6, 0.7, 0.8, 0.9]  # 60%, 70%, 80%, 90%
    z_alphas = [1.96]  # For alpha = 0.05 (two-sided)
    z_betas = [0.253, 0.524, 0.84, 1.282]  # For powers of 60%, 70%, 80%, 90%
    
    detectable_diffs = {}
    for i, power in enumerate(power_levels):
        # Formula for minimum detectable difference
        detectable_diff = (z_alphas[0] + z_betas[i]) * np.sqrt(2 * p_pooled * (1 - p_pooled) / min(count1, count2))
        detectable_diffs[f"{int(power*100)}%"] = detectable_diff
    
    # Calculate required sample size for specified power_level
    required_sample_sizes = {}
    power_for_your_sample_size = None
    
    if power_level is not None:
        power_decimal = power_level  # Convert percentage to decimal
        
        # Calculate the statistical power for the current sample size
        # using the provided power_level as the effect size
        min_n = min(count1, count2)
        
        # Calculate the z-score for the effect
        z_effect = (power_decimal * np.sqrt(min_n)) / np.sqrt(2 * p_avg * (1 - p_avg))
        
        # Calculate the power given z-effect and alpha=0.05
        power_for_your_sample_size = 1 - stats.norm.cdf(1.96 - z_effect)
        power_for_your_sample_size = power_for_your_sample_size * 100  # Convert to percentage
        
        for i, power in enumerate(power_levels):
            # Formula for required sample size
            n = ((z_alphas[0] + z_betas[i])**2 * 2 * p_avg * (1 - p_avg)) / (power_decimal**2)
            required_sample_sizes[f"{int(power*100)}%"] = int(np.ceil(n))
    
    return {
        "detectable_differences": detectable_diffs,
        "required_sample_sizes": required_sample_sizes,
        "power_for_your_sample_size": power_for_your_sample_size
    }