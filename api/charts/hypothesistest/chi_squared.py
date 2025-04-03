import io
import numpy as np
import pandas as pd
import scipy.stats as stats
import matplotlib.pyplot as plt
from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Optional, Union, Literal
from api.schemas import BusinessLogicException
from matplotlib.backends.backend_pdf import PdfPages

from ...utils.pdf_utils import add_header_or_footer_to_a4_portrait

header_image_path = 'assets/img/Header.png'
footer_image_path = 'assets/img/Footer.png'

from ...utils.mpl_table_utils import merge_mpl_table_cells as mergecells


class ChiSquaredConfig(BaseModel):
    title: str
    variant: Literal["Summarized data", "Data in columns"]
    alphalevel: float = Field(..., ge=0.01, le=0.1)

    # Only required for "Summarized data" variant
    outcomes: Optional[List[str]] = None
    expected_percent: Optional[List[float]] = None
    observed_count: Optional[List[int]] = None
    
    @field_validator('alphalevel')
    def validate_alphalevel(cls, v):
        common_values = [0.01, 0.05, 0.1]
        if v not in common_values:
            raise ValueError(f"alphalevel should typically be one of {common_values}")
        return v

class ChiSquaredData(BaseModel):
    values: Optional[Dict[str, List[Union[str, float, int]]]] = Field(None)

    @field_validator('values')
    def validate_values_structure(cls, v):
        if v is None:
            return v
        
        required_keys = ["Outcomes", "expected_percent", "sample_count"]
        for key in required_keys:
            if key not in v:
                raise ValueError(f"Missing required key in values: {key}")
        return v

class ChiSquaredRequest(BaseModel):
    project: str
    step: str
    config: ChiSquaredConfig
    data: Optional[ChiSquaredData] = None

class ChiSquared:
    def __init__(self, data: dict):
        try:
            validated_data = ChiSquaredRequest(**data)
            self.project = validated_data.project
            self.step = validated_data.step
            self.config = validated_data.config
            self.data = validated_data.data
            
            # Validate that we have all required data for one of the two variants
            variant = self.config.variant
            
            # For "Summarized data" variant
            if variant == "Summarized data":
                if self.config.outcomes is None or self.config.expected_percent is None or self.config.observed_count is None:
                    raise ValueError("For 'Summarized data' variant, outcomes, expected_percent, and observed_count must be provided")
                
                # Validate matching list lengths
                if len(self.config.outcomes) != len(self.config.expected_percent) or len(self.config.outcomes) != len(self.config.observed_count):
                    raise ValueError("outcomes, expected_percent, and observed_count must have the same length")
                
                # Validate percentages sum to 1
                if abs(sum(self.config.expected_percent) - 1.0) > 0.001:
                    raise ValueError("expected_percent values must sum to approximately 1.0")
                    
            # For "Data in columns" variant
            elif variant == "Data in columns":
                if self.data is None or self.data.values is None:
                    raise ValueError("For 'Data in columns' variant, data.values must be provided")
                
                # Verify required keys exist in values
                required_keys = ["Outcomes", "expected_percent", "sample_count"]
                for key in required_keys:
                    if key not in self.data.values:
                        raise ValueError(f"Missing required key in data.values: {key}")
                
                # Validate that sample_count contains valid categories from Outcomes
                outcomes = set(self.data.values["Outcomes"])
                sample_count = self.data.values["sample_count"]
                invalid_values = [value for value in sample_count if value not in outcomes]
                if invalid_values:
                    raise ValueError(f"Found invalid categories in sample_count: {set(invalid_values)}")
                    
                # Validate percentages sum to 1
                if abs(sum(self.data.values["expected_percent"]) - 1.0) > 0.001:
                    raise ValueError("expected_percent values must sum to approximately 1.0")
            
            else:
                raise ValueError("variant must be either 'Summarized data' or 'Data in columns'")
                
        except ValueError as e:
            raise BusinessLogicException(
                error_code="error_validation",
                field=str(e),
                details={"message": f"Invalid or missing field: {str(e)}"}
            )
    
    def process(self):
        title = self.config.title
        variant = self.config.variant
        alphalevel = self.config.alphalevel
        
        if variant == "Summarized data":
            outcomes = self.config.outcomes
            expected_percent = self.config.expected_percent
            observed_count = self.config.observed_count
            sample_size = sum(observed_count)
        else:
            outcomes_key = "Outcomes"
            expected_percent_key = "expected_percent"
            sample_count_key = "sample_count"

            outcomes = self.data.values[outcomes_key]
            expected_percent = self.data.values[expected_percent_key]
            sample_count = self.data.values[sample_count_key]

            observed_count = []
            for outcome in outcomes:
                count = sum(1 for value in sample_count if value == outcome)
                observed_count.append(count)

            sample_size = len(sample_count)

        expected_count = [sample_size * percent for percent in expected_percent]
        observed_percentage = [count / sample_size for count in observed_count]

        chi_squared_results = _perform_chisquare(
            observed=observed_count,
            expected=expected_count,
            alpha=alphalevel
        )

        if len(outcomes) < 2:
            raise BusinessLogicException(
                error_code="error_validation",
                field="outcomes",
                details={"message": "At least 2 outcome categories are required"}
            )
        
        # Ensure no zero expected counts (would cause division by zero in chi-square)
        if any(count == 0 for count in expected_count):
            raise BusinessLogicException(
                error_code="error_validation",
                field="expected_count",
                details={"message": "Expected counts cannot be zero. Check your expected percentages."}
            )
        
        # Warn about small expected counts (chi-square requires expected >= 5)
        small_counts = [i for i, count in enumerate(expected_count) if count < 5]
        if small_counts:
            print(f"Warning: Small expected counts (<5) in categories: {[outcomes[i] for i in small_counts]}")
            print("Chi-squared test may not be reliable with small expected counts.")

        # Convert results to proper format for return
        results = {
            "title": title,
            "sample_size": sample_size,
            "outcomes": outcomes,
            "expected_percentage": [float(ep) for ep in expected_percent],
            "observed_count": [float(oc) for oc in observed_count],
            "observed_percentage": [float(op) for op in observed_percentage],
            "chi_squared": chi_squared_results["chi_squared"],
            "p_value": chi_squared_results["p_value"],
            "degrees_of_freedom": chi_squared_results["deg_freedom"],
            "categories": chi_squared_results["categories"]
        }
        
        variant_str = "     Data in columns" if variant == "Data in columns" else "     Summarized Data"

        if results['p_value'] < alphalevel:
            hypothesis_string = f"The %-Sample is significantly different from\nthe %-Target"
            table_color = "#9cc563"
        else:
            hypothesis_string = f"The %-Sample is not significantly different from\nthe %-Target"
            table_color = "#d6ed5f"

        # Create PDF
        pdf_io = io.BytesIO()

        with PdfPages(pdf_io) as pdf:
            # NEW PDF PAGE - T-Test results, Descriptive Statistics, Data Time Series
            fig, axes = plt.subplot_mosaic([
                ["Defective-Test Results", "Defective-Test Results"],
                ["Descriptive Statistics", "Descriptive Statistics"],
                ["Comparison Bar", "Difference Bar"],         # Time Series Plots for each dataset
                ["Comparison Bar", "empty"]],    # Chance and Detectable Difference
                figsize=(8.27, 11.69), dpi=300)  # A4 size in inches
            #fig.subplots_adjust(hspace=0.4)  # Increase hspace to add more space between charts
            #fig.suptitle(title, fontsize=16, weight='bold', y=0.94)

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
                [variant_str, "", r"$\mathrm{H_{0}}: \mathrm{p_{Sample} = p_{Target}}$", "", "p-Value*"],
                ["Test-Setup", "Different", r"$\mathrm{H_{1}}: \mathrm{p_{Sample} \neq p_{Target}}$", "", f"{results['p_value']:.3f}"],
                ["Sample size:", f"{results['sample_size']}", "", "", ""],
                ["Samples", f"{results['outcomes']}", "empty", "Degree of freedom", f"{results['degrees_of_freedom']}"],
                ["Chi-Square", f"{results['chi_squared']:.2f}", "", "", ""],
                ["Alpha-Level", f"{alphalevel}", "empty", hypothesis_string, ""],
                ["", "", "", "", ""]
            ]
            # Set the column widths as needed
            col_widths = [0.15, 0.15, 0.15, 0.15, 0.15, 0.15]

            bg_colors = [
                [grey, grey, grey, grey, grey],
                ["#ffffff", "#ffffff", lightgreen_table, "#ffffff", "#ffffff"],
                ["#ffffff", "#ffffff", green_table, "#ffffff", table_color],
                ["#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff"],
                ["#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff"],
                ["#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff"],
                ["#ffffff", "#ffffff", "#ffffff", table_color, table_color],
                ["#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff"]
            ]

            table_bg = ax.table(bbox=[0, 0, 1, 1], cellColours=bg_colors)
            for cell in table_bg._cells.values():
                cell.set_edgecolor("none")

            bg_none = [
                ["none", "none", "none", "none", "none"],
                ["none", "none", "none", "none", "none"],
                ["none", "none", "none", "none", "none"],
                ["none", "none", "none", "none", "none"],
                ["none", "none", "none", "none", "none"],
                ["none", "none", "none", "none", "none"],
                ["none", "none", "none", "none", "none"],
                ["none", "none", "none", "none", "none"]
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
            mergecells(table, [(0, 3), (0, 4)])
            mergecells(table, [(1, 0), (1, 1)])
            mergecells(table, [(5, 2), (6, 2)])
            mergecells(table, [(4, 1), (4, 2)])
            mergecells(table, [(6, 3), (6, 4)])
            mergecells(table, [(7, 0), (7, 1), (7, 2), (7, 3), (7, 4)])

            table.get_celld()[7, 0].set_fontsize(5)

            cell_text_centered_1 = table.get_celld()[(0, 3)]
            cell_text_centered_1.set_text_props(
                text='Results',
                x=1.5,
                y=0.5,
                visible=True,
                ha='center'
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
                text='* If the p-value is less than the α-level, then H0 is to be rejected and the alternative hypothesis H1 is to be accepted.',
                visible=True,
                color='grey',
                ha='right'
            )
            bold_text = [(2, 1), (1, 3), (1, 4)]
            for row, col in bold_text:
                cell = table.get_celld()[(row, col)]
                cell.set_text_props(weight='bold')

            left_text = [(1, 0), (4, 1), (5, 3), (6, 3), (7, 0)]
            for row, col in left_text:
                cell = table.get_celld()[(row, col)]
                cell.set_text_props(ha='left')

            right_text = [(0, 0), (3, 3), (4, 3)]
            for row, col in right_text:
                cell = table.get_celld()[(row, col)]
                cell.set_text_props(ha='right')


            # Descriptive statistics
            ax = axes["Descriptive Statistics"]
            ax.axis('off')
            descriptive_table_widths = [0.09, 0.06,0.11,0.11,0.11,0.11,0.11,0.16,0.11]
            descriptive_table_data = [
                ["\nSource", "\nN", "Target expected", "", "Target observed", "", "\nDelta\n% Target", f"\n{(1 - alphalevel)*100}% CI\nfor observed %", "\nDiffer from\ntarget?"],
                ["", "", "Percent [%]", "count", "Percent [%]", "Count", "", "", ""]
            ]
            
            for i, outcome in enumerate(results['outcomes']):
                expected_pct = results['expected_percentage'][i] * 100
                expected_count = expected_pct * results['sample_size'] / 100
                observed_pct = results['observed_percentage'][i] * 100
                observed_count = results['observed_count'][i]
                delta = observed_pct - expected_pct
                ci_lower = results['categories'][i]['ci_lower']
                ci_upper = results['categories'][i]['ci_upper']
                ci_range = f"({ci_lower:.1f}; {ci_upper:.1f})"
                
                # Determine if significantly different
                # Check if expected percentage is outside the confidence interval
                if expected_pct < ci_lower:
                    different = "Higher"
                elif expected_pct > ci_upper:
                    different = "Lower"
                else:
                    different = "No"
                
                row = [
                    outcome, 
                    f"{sample_size}", 
                    f"{expected_pct:.1f}%", 
                    f"{expected_count:.1f}", 
                    f"{observed_pct:.1f}%", 
                    f"{observed_count:.1f}", 
                    f"{delta:.1f}%", 
                    ci_range, 
                    different
                ]
                descriptive_table_data.append(row)
            
            # Create table colors
            descriptive_bg_colors = []
            descriptive_bg_colors.append([grey] * 9)  # Header row 1
            descriptive_bg_colors.append([grey] * 9)     # Header row 2
            
            # Add colors for data rows
            for i in range(len(results['outcomes'])):
                row_color = ["#ffffff"] * 9
                # Color the "Differ from target?" cell based on result
                if descriptive_table_data[i+2][-1] == "Yes":
                    row_color[-1] = "#ffcccc"  # Light red for "Yes"
                descriptive_bg_colors.append(row_color)

            bg_table = ax.table(bbox=[0, 0.3, 1, 0.5], cellColours=descriptive_bg_colors)
            for cell in bg_table._cells.values():
                cell.set_edgecolor("none")

            bg_none = []
            for _ in range(len(results['outcomes']) + 2):
                row_color = ["none"] * 9
                bg_none.append(row_color)
            
            descriptive_table = ax.table(
                cellText=descriptive_table_data,
                colWidths=descriptive_table_widths,
                cellLoc='center',
                loc='upper left',
                cellColours=bg_none,
                bbox=[0, 0.3, 1, 0.5]
            )
            mergecells(descriptive_table, [(0, 0), (1, 0)])
            mergecells(descriptive_table, [(0, 1), (1, 1)])
            mergecells(descriptive_table, [(0, 2), (0, 3)])
            mergecells(descriptive_table, [(0, 4), (0, 5)])
            mergecells(descriptive_table, [(0, 6), (1, 6)])
            mergecells(descriptive_table, [(0, 7), (1, 7)])
            mergecells(descriptive_table, [(0, 8), (1, 8)])
            
            descriptive_table.auto_set_font_size(False)
            descriptive_table.set_fontsize(font_size)
            
            for (row, col), cell in descriptive_table._cells.items():
                cell.set_edgecolor(edge_color)
                cell.set_linewidth(0.5)

            # Set text alignment for cells (0, 2) and (0, 3) to left
            cell_left_text_1 = descriptive_table.get_celld()[(0, 2)]
            cell_left_text_1.set_text_props(ha='left')

            cell_left_text_2 = descriptive_table.get_celld()[(0, 4)]
            cell_left_text_2.set_text_props(ha='left')

            ax = axes["Comparison Bar"]
            ax.set_title("Outcome Comparison Chart\nCompare the sample and target percents.", loc='center', fontsize=font_size)
            # Create the horizontal bar chart comparing observed vs expected percentages
            bar_height = 0.35
            
            # Reverse the order of outcomes and corresponding data
            reversed_outcomes = list(reversed(results['outcomes']))
            reversed_expected_pcts = list(reversed([p * 100 for p in results['expected_percentage']]))
            reversed_observed_pcts = list(reversed([p * 100 for p in results['observed_percentage']]))
            
            y = np.arange(len(reversed_outcomes))

            # Plot the horizontal bars
            ax.barh(y - bar_height/2, reversed_expected_pcts, bar_height, label='Target %', color=plt.cm.Paired(0), edgecolor=edge_color, zorder=5)
            ax.barh(y + bar_height/2, reversed_observed_pcts, bar_height, label='Sample %', color=plt.cm.Paired(1), edgecolor=edge_color, zorder=5)

            # Add category labels
            ax.set_yticks(y)
            ax.set_yticklabels(reversed_outcomes, fontsize=font_size)

            # Set x-axis title and limits
            ax.set_xlabel('Percentage (%)', fontsize=font_size)
            ax.set_xlim(0, max(max(reversed_expected_pcts), max(reversed_observed_pcts)) * 1.2)
            
            # Get current x-ticks and display only every other one
            xticks = ax.get_xticks()
            ax.set_xticks(xticks[::1])  # Take every other tick
            
            ax.tick_params(axis='x', labelsize=font_size)

            # Add value labels to the right of each bar
            for i, v in enumerate(reversed_expected_pcts):
                ax.text(v + 1, i - bar_height/2, f"{v:.1f}%", va='center', fontsize=font_size)
                
            for i, v in enumerate(reversed_observed_pcts):
                ax.text(v + 1, i + bar_height/2, f"{v:.1f}%", va='center', fontsize=font_size)

            # Add legend
            ax.legend(fontsize=font_size)
            ax.grid(True, alpha=0.3, zorder=0)

            # Create the "Difference Bar" chart
            ax = axes["Difference Bar"]
            ax.set_title("% Difference between Sample and Target Counts\nLook for longer bars, which indicate relative difference from the target", loc='center', fontsize=font_size)

            # Calculate differences
            differences = [reversed_observed_pcts[i] - reversed_expected_pcts[i] for i in range(len(reversed_observed_pcts))]

            # Plot the differences as horizontal bars
            bars = ax.barh(y, differences, height=0.5, color='#95b92a', edgecolor=edge_color, zorder=5)

            # Add category labels
            ax.set_yticks(y)
            ax.set_yticklabels(reversed_outcomes, fontsize=font_size)

            # Set x-axis title
            ax.set_xlabel('Difference (%)', fontsize=font_size)
            ax.tick_params(axis='x', labelsize=font_size)

            # Add a vertical line at x=0
            ax.axvline(x=0, color='black', linestyle='-', linewidth=0.8)

            # Add value labels to the right/left of each bar
            for i, v in enumerate(differences):
                if v >= 0:
                    ha = 'right'
                    x_offset = -0.5
                else:
                    ha = 'left'
                    x_offset = 0.5
                ax.text(x_offset, i, f"{v:.1f}%", va='center', ha=ha, fontsize=font_size)

            ax.grid(True, alpha=0.3, zorder=0)

            ax = axes["empty"]
            ax.axis('off')

            pdf.savefig(fig)
            plt.close(fig)

        pdf_io.seek(0)
        plt.close('all')
        return pdf_io


def _perform_chisquare(observed: list, expected: list, alpha: float):

    results = {}

    observed = np.array(observed)
    expected = np.array(expected)

    total = observed.sum()
    k = len(observed)

    chi2_stat, p_value = stats.chisquare(observed, expected)

    df = k - 1

    observed_proportions = observed / total

    z = stats.norm.ppf(1 - alpha/2)

    ci_lower = (observed_proportions - z * np.sqrt(observed_proportions * (1 - observed_proportions) / total))*100
    ci_upper = (observed_proportions + z * np.sqrt(observed_proportions * (1 - observed_proportions) / total))*100

    # Create a list to store category info (proportion and CI)
    categories = []
    for i in range(k):
        categories.append({
            'proportion': float(observed_proportions[i]),
            'ci_lower': float(ci_lower[i]),
            'ci_upper': float(ci_upper[i])
        })
    
    results = {
        "chi_squared": float(chi2_stat),
        "p_value": float(p_value),
        "deg_freedom": df,
        "categories": categories
    }
    
    return results
