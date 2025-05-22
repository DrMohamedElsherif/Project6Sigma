import io
import numpy as np
import pandas as pd
import scipy.stats as stats
import matplotlib.pyplot as plt
from pydantic import BaseModel, Field, model_validator
from typing import List, Dict, Optional, Union
from api.schemas import BusinessLogicException
from matplotlib.backends.backend_pdf import PdfPages

from ...utils.pdf_utils import add_header_or_footer_to_a4_portrait
from ..constants import COLOR_PALETTE

header_image_path = 'assets/img/Header.png'
footer_image_path = 'assets/img/Footer.png'

from ...utils.mpl_table_utils import merge_mpl_table_cells as mergecells


class MultipleChiSquaredConfig(BaseModel):
    title: str
    variant: str
    alphalevel: float

    categories: Optional[List[str]] = None  # Variant 1
    outcomes: List[str]
    observed_count: Optional[List[List[int]]] = None

    @model_validator(mode='after')
    def validate_variant_requirements(cls, values):
        variant = values.variant
        if variant == "Summarized data":
            # Check required fields for this variant
            if not values.categories:
                raise BusinessLogicException(
                    error_code="error_missing_field",
                    field="categories",
                    details={"message": "Missing required field: categories"}
                )
            if not values.outcomes:
                raise BusinessLogicException(
                    error_code="error_missing_field",
                    field="outcomes",
                    details={"message": "Missing required field: outcomes"}
                )
            if not values.observed_count:
                raise BusinessLogicException(
                    error_code="error_missing_field",
                    field="observed_count",
                    details={"message": "Missing required field: observed_count"}
                )
                
            # Validate observed_count dimensions match categories and outcomes
            observed = values.observed_count
            categories = values.categories
            outcomes = values.outcomes
            
            if len(observed) != len(categories):
                raise BusinessLogicException(
                    error_code="error_row_category_mismatch",
                    field="observed_count",
                    details={"message": "Number of rows in observed_count must match number of categories"}
                )
            
            for i, row in enumerate(observed):
                if len(row) != len(outcomes):
                    raise ValueError(f"Row {i} in observed_count has {len(row)} elements but should have {len(outcomes)} (matching outcomes)")
        
        return values

class MultipleChiSquaredData(BaseModel):
    values: Optional[Dict[str, Dict[str, List[Union[float, str]]]]] = Field(None)     # Variant 2

class MultipleChiSquaredRequest(BaseModel):
    project: str
    step: str
    config: MultipleChiSquaredConfig
    data: Optional[MultipleChiSquaredData] = Field(default_factory=MultipleChiSquaredData)

class MultipleChiSquared:
    def __init__(self, data: dict):
        try:
            validated_data = MultipleChiSquaredRequest(**data)
            self.project = validated_data.project
            self.step = validated_data.step
            self.config = validated_data.config
            self.data = validated_data.data

        except ValueError as e:
            raise BusinessLogicException(
                error_code = "error_validation",
                field=str(e),
                details={"message": f"Invalid or missing field: {str(e)}"}
            )

    def process(self):
        title = self.config.title
        variant = self.config.variant
        alphalevel = self.config.alphalevel
        categories = self.config.categories if self.config.categories is not None else None
        outcomes = self.config.outcomes if self.config.outcomes is not None else None
        observed_count = self.config.observed_count if self.config.observed_count is not None else None

        if observed_count is None:
            # Obtain categories
            categories = list(self.data.values.keys())
            # extract expected percentages for each category and format them -> expected_percent
            # expected_percent_1 = self.data.values[categories[0]]['expected_percent']
            # expected_percent_2 = self.data.values[categories[1]]['expected_percent']
            # expected_percent = [expected_percent_1, expected_percent_2]
            # extract observed count for each category and format them -> observed_count
            observed_count = []
            for cat_idx, category in enumerate(categories):
                cat_counts = []
                for outcome in outcomes:
                    cat_counts.append(self.data.values[category]['samples'].count(outcome))
                observed_count.append(cat_counts)

        # Calculate sample sizes for each category
        sample_sizes = []
        for cat_counts in observed_count:
            sample_sizes.append(sum(cat_counts))

        results = _chi_square_test_general(observed_count, expected_counts=None, alpha=alphalevel, category_names=categories)

        variant_str = "     Data in columns" if variant == "Data in columns" else "     Summarized Data"

        if results['p_value'] < alphalevel:
            hypothesis_string = "Minimum one Category is significantly different"
            table_color = "#9cc563"
        else:
            hypothesis_string = "No Category is significantly different"
            table_color = "#d6ed5f"

        # Create PDF
        pdf_io = io.BytesIO()

        with PdfPages(pdf_io) as pdf:
            # NEW PDF PAGE - T-Test results, Descriptive Statistics, Data Time Series
            fig, axes = plt.subplot_mosaic([
                ["Defective-Test Results", "Defective-Test Results"],
                ["Descriptive Statistics", "Descriptive Statistics"],
                ["Comparison Bar", "Difference Bar"]],    # Chance and Detectable Difference
                figsize=(8.27, 11.69), dpi=300)  # A4 size in inches
            #fig.subplots_adjust(hspace=0.4)  # Increase hspace to add more space between charts
            fig.suptitle(title, fontsize=14, y=0.92, ha='left', x=0.1)

            many_categories = len(categories) > 4  # Check if there are more than 4 categories -> 2 pdf pages
            total_pages = 2 if many_categories else 1

            add_header_or_footer_to_a4_portrait(fig, header_image_path, position='header')
            add_header_or_footer_to_a4_portrait(fig, footer_image_path, position='footer', page_number=1, total_pages=total_pages)


            # Define the colors + fontsize
            grey = "#e7e6e6"
            green_table = "#9cc563"
            lightgreen_table = "#d6ed5f"
            font_size=7
            edge_color = "#7c7c7c"

            # Table overview of the defective test results
            ax = axes["Defective-Test Results"]
            ax.axis('off')

            outcomes_str = split_categories(outcomes, max_line_length=43, max_per_line=4)
            
            categories_str = split_categories(categories, max_line_length=43, max_per_line=4)

            table_data = [
                ["Configuration", "", "Hypothesis", "", ""],
                [variant_str, "", r"$\mathrm{H_{0}}:$ all $\mathrm{Cat_{i}}$ equal", "", "p-Value*"],
                ["Test-Setup", "Different", r"$\mathrm{H_{1}}:$ min. one $\mathrm{Cat_{i}}$" + "\ndifferent", "", f"{results['p_value']:.3f}"],
                ["Sample size:", f"{results['total_sample_size']}", "", "", ""],
                ["Categories", f"{categories_str}", "empty", "Degree of freedom", f"{results['degrees_of_freedom']}"],
                ["Outcomes", outcomes_str, "empty", "", ""],
                ["Chi-Square", f"{results['chi2_statistic']:.2f}", "", "", ""],
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
            mergecells(table, [(4, 1), (4, 2)])
            mergecells(table, [(5, 1), (5, 2)])
            mergecells(table, [(6, 2), (7, 2), (8, 2)])
            mergecells(table, [(1, 3), (2, 3), (3, 3)])
            mergecells(table, [(5, 3), (6, 3)])
            mergecells(table, [(5, 4), (6, 4)])
            mergecells(table, [(7, 3), (7, 4)])
            mergecells(table, [(8, 0), (8, 1), (8, 2), (8, 3), (8, 4)])

            table.get_celld()[8, 0].set_fontsize(5)

            cell_text_centered_1 = table.get_celld()[(0, 3)]
            cell_text_centered_1.set_text_props(
                text='Results',
                x=1.5,
                y=0.5,
                visible=True,
                ha='center'
            )
            cell_text_small = table.get_celld()[(8, 0)]
            cell_text_small.set_text_props(
                text='* If the p-value is less than the α-level, then H0 is to be rejected and the alternative hypothesis H1 is to be accepted.',
                visible=True,
                color='grey',
                ha='right'
            )
            bold_text = [(2, 1), (1, 4), (3, 1)]
            for row, col in bold_text:
                cell = table.get_celld()[(row, col)]
                cell.set_text_props(weight='bold')

            left_text = [(1, 0), (4, 1), (5, 1), (5, 3), (7, 3), (8, 0)]
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

            max_display = min(4, len(categories))

            if many_categories:
                ax.text(0.5, 0.7, "Descriptive statistics shown on the next page", ha='center', va='center', fontsize=font_size)
            
            else:

                # Set padding for the title and bbox for the table based on the number of categories
                if len(outcomes) <= 3:
                    ax.set_title("Descriptive Statistics", loc='left', pad=-50, y=1.1)
                    bbox_1 = [0, 0.3, 1, 0.5]
                elif 3 < len(outcomes) <= 5:
                    ax.set_title("Descriptive Statistics", loc='left', pad=-50, y=1.1)
                    bbox_1 = [0, 0.2, 1, 0.6]
                else: 
                    ax.set_title("Descriptive Statistics", loc='left', pad=-50, y=1.1)
                    bbox_1 = [0, 0.1, 1, 0.7]
                
                # Calculate total columns needed (2 for outcome and N, plus 3 for each category)
                total_cols_1 = 2 + max_display * 3

                descriptive_table_widths_1 = [0.15, 0.05] + [0.075] * max_display * 3

                descriptive_table_data_1 = [
                    ["\n\nOutcome", "\n\nN"] + [""] * max_display * 3,
                    ["", ""]
                ]

                for i, category in enumerate(categories[:max_display]):
                    col_index = 2 + (i * 3)
                    descriptive_table_data_1[0][col_index] = f"Cat {i + 1} / {category}"

                for i in range(len(categories[:max_display])):
                    # col_index = 2 + (i * 3)
                    descriptive_table_data_1[1].extend(["E", "O", r"$\Delta$"])

                # Convert data to numpy arrays and transpose to match dimensions
                observed_array = np.array(observed_count).T
                expected_array = np.array(results['expected_counts']).T
                difference = observed_array - expected_array

                for i, outcome in enumerate(outcomes):
                    # Get the counts for available categories (up to 4)
                    max_cats = max_display
                    expected_counts = expected_array[i][:max_cats]
                    observed_counts = observed_array[i][:max_cats]
                    sample_size = sum(observed_counts)
                    differences = difference[i][:max_cats]

                    # Create a row with elements for available categories
                    row = [outcome, f"{sample_size}"]
                    for j in range(max_cats):
                        row.extend([
                            f"{expected_counts[j]}",
                            f"{observed_counts[j]}",
                            f"{differences[j]}"
                        ])
                    
                    # Fill remaining cells with empty strings if needed
                    while len(row) < 2 + 3 * max_display:  # 14 is max for 4 categories (2 + 4*3)
                        row.append("")
                    descriptive_table_data_1.append(row)

                # Manage the background colors for the tables
                descriptive_table_bg_colors_1 = [
                    [grey] * total_cols_1,
                    [grey] * total_cols_1
                ]

                bg_none_1 = [
                    ["none"] * total_cols_1,
                    ["none"] * total_cols_1
                ]

                # Add (len(outcomes)) rows of white background color
                for _ in range(len(outcomes)):
                    descriptive_table_bg_colors_1.append(["#ffffff"] * total_cols_1)
                    bg_none_1.append(["none"] * total_cols_1)                

                table_bg_1 = ax.table(bbox=bbox_1, cellColours=descriptive_table_bg_colors_1)
                for cell in table_bg_1._cells.values():
                    cell.set_edgecolor("none")

                descriptive_table_1 = ax.table(
                    cellText=descriptive_table_data_1,
                    cellColours=bg_none_1,
                    colWidths=descriptive_table_widths_1,
                    loc='upper left',
                    cellLoc='center',
                    bbox=bbox_1
                )

                descriptive_table_1.auto_set_font_size(False)
                descriptive_table_1.set_fontsize(font_size)

                for cell in descriptive_table_1._cells.values():
                    cell.set_edgecolor(edge_color)
                    cell.set_linewidth(0.5)

                mergecells(descriptive_table_1, [(0, 0), (1, 0)])
                mergecells(descriptive_table_1, [(0, 1), (1, 1)])

                for i in range(len(categories[:4])):
                    mergecells(descriptive_table_1, [(0, 2 + i * 3), (0, 2 + i * 3 + 1), (0, 2 + i * 3 + 2)])
                    cell = descriptive_table_1.get_celld()[(0, 2 + i * 3)]
                    cell.set_text_props(ha='left')


            ax = axes["Comparison Bar"]
            ax.set_title("Percentage Profiles Chart\nCompare the profiles", loc='center', fontsize=font_size)

            categories_with_average = ["Average"] + categories

            observed_count = np.array(observed_count)  # shape (3, 2) - 3 categories, 2 outcomes

            # Calculate row sums (total count per category)
            row_sums = observed_count.sum(axis=1)  # This gives [55, 150, 50] for 3 categories

            percentages = []
            for cat_idx in range(observed_count.shape[0]):  # Loop through categories (3)
                cat_sum = row_sums[cat_idx]  # Get total for this category
                cat_percentages = [(val / cat_sum) * 100 for val in observed_count[cat_idx, :]]  # Calculate % for each outcome
                percentages.append(cat_percentages)

            # Calculate average percentages for each outcome across all categories
            avg_percentages = []
            for outcome_idx in range(observed_count.shape[1]):  # Loop through outcomes (2)
                avg_percentage = sum(percentages[cat_idx][outcome_idx] for cat_idx in range(observed_count.shape[0])) / observed_count.shape[0]
                avg_percentages.append(avg_percentage)

            # Prepare percentages by outcome for plotting
            outcomes_percentages = []
            for outcome_idx in range(observed_count.shape[1]):  # Loop through outcomes (2)
                outcome_percentages = [avg_percentages[outcome_idx]] + [percentages[cat_idx][outcome_idx] for cat_idx in range(observed_count.shape[0])]
                outcomes_percentages.append(outcome_percentages)

            y_pos = np.arange(len(categories_with_average))

            # Create horizontal bars using plt.cm.Paired color palette
            num_outcomes = len(outcomes_percentages)

            # Use plt.cm.Paired color palette
            paired_colors = COLOR_PALETTE[:num_outcomes]  # Paired has 12 colors

            # Invert the order of categories
            categories_with_average = categories_with_average[::-1]
            y_pos = np.arange(len(categories_with_average))
            
            # Need to invert the order of data as well
            for i in range(len(outcomes_percentages)):
                outcomes_percentages[i] = outcomes_percentages[i][::-1]

            # Create a list to store the left positions for each bar
            left_positions = np.zeros(len(y_pos))

            # Plot each outcome's bars
            for i in range(num_outcomes):
                outcome_percentages = outcomes_percentages[i]  # Get the entire array for this outcome
                ax.barh(y_pos, outcome_percentages, left=left_positions, 
                        color=paired_colors[i % len(paired_colors)], 
                        label=outcomes[i] if i < len(outcomes) else f'Outcome {i+1}', zorder=3)
                
                # Add percentage labels to each section
                for j, category in enumerate(categories_with_average):
                    width = outcome_percentages[j]
                    if width > 5:  # Only show text if the bar is wide enough
                        ax.text(left_positions[j] + width/2, j, f"{width:.1f}%", 
                                ha='center', va='center', color='black', fontsize=font_size)
                
                # Update left positions for the next outcome
                left_positions = left_positions + outcome_percentages

            # Add legend below the figure on the left with appropriate number of columns
            ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), 
                        fontsize=font_size-1, ncol=min(len(outcomes), 3))

            # Customize the plot
            ax.set_yticks(y_pos)
            ax.set_yticklabels(categories_with_average, fontsize=font_size)
            ax.set_xlabel('Percentage', fontsize=font_size)
            ax.set_xlim(0, 100)  # Set x-axis limit to match the figure
            ax.set_xticks(np.arange(0, 101, 20))
            ax.set_xticklabels([f"{x}%" for x in range(0, 101, 20)], fontsize=font_size)
            ax.grid(axis='x', linestyle='-', alpha=0.3, zorder=0)

            if many_categories:
                ax.set_position([0.13, 0.11, 0.25, 0.3])




            
            ax = axes["Difference Bar"]
            ax.set_title("% Difference between Observed and\nExpected Counts", loc='center', fontsize=font_size)

            # Calculate the percentage difference between observed and expected counts
            observed_array = np.array(observed_count)  # shape (3, 2) - 3 categories, 2 outcomes
            expected_array = np.array(results['expected_counts'])  # shape (3, 2)
            percentage_diff = ((observed_array - expected_array) / expected_array) * 100  # shape (3, 2)

            # Set up the plot data - reverse the order of categories and outcomes
            labels = []
            for category in categories[::-1]:  # Reverse the categories
                for outcome in outcomes[::-1]:  # Reverse the outcomes
                    labels.append(f"{category}-{outcome}")

            # Create arrays for the percentage differences, flat format with reversed categories and outcomes
            diff_values = []
            categories_labels = []
            outcomes_labels = []

            for cat_idx in range(len(categories)-1, -1, -1):  # Reverse loop through categories
                category = categories[cat_idx]
                for outcome_idx in range(len(outcomes)-1, -1, -1):  # Reverse loop through outcomes
                    outcome = outcomes[outcome_idx]
                    # Fix: Access percentage_diff with correct indices [cat_idx, outcome_idx]
                    diff_values.append(percentage_diff[cat_idx][outcome_idx])
                    categories_labels.append(category)
                    outcomes_labels.append(outcome)

            # Get unique outcomes and determine colors using the same scheme as the Comparison Bar chart
            unique_outcomes = outcomes[::-1]  # Use reversed outcomes list to maintain color consistency
            paired_colors = COLOR_PALETTE[:num_outcomes]  # Paired has 12 colors
            color_dict = {outcome: paired_colors[i % len(paired_colors)] for i, outcome in enumerate(unique_outcomes)}
            bar_colors = [color_dict[outcome] for outcome in outcomes_labels]

            # Set up the y-positions for the bars
            y_positions = np.arange(len(diff_values))

            # Create horizontal bar chart
            bars = ax.barh(y_positions, diff_values, color=bar_colors[::-1])

            # Add a dashed line at 0 to show the baseline
            ax.axvline(x=0, color='black', linestyle='--', alpha=0.7)

            # Add labels and customize plot
            ax.set_yticks(y_positions)
            # Create a list of y-tick labels that shows only category names once per category
            y_labels = []
            category_occurrences = {}
            
            # Count outcomes per category to determine middle position
            for cat in categories_labels:
                if cat not in category_occurrences:
                    category_occurrences[cat] = 0
                category_occurrences[cat] += 1
            
            # Track occurrences as we build labels
            current_occurrences = {}
            
            for i, cat in enumerate(categories_labels):
                if cat not in current_occurrences:
                    current_occurrences[cat] = 0
                current_occurrences[cat] += 1
                
                # Calculate middle position based on number of outcomes
                outcomes_count = category_occurrences[cat]
                if outcomes_count in [3, 5, 7]:  # Odd number of outcomes
                    middle_pos = (outcomes_count // 2) +2  # Middle position (1-indexed)
                else:  # Even number of outcomes
                    middle_pos = outcomes_count // 2  # Position just before middle (1-indexed)
                
                # Show label only at the calculated position
                if current_occurrences[cat] == middle_pos:
                    y_labels.append("|" + cat + "|")
                else:
                    y_labels.append("")
            
            ax.set_yticklabels(y_labels, fontsize=font_size-1, rotation = 90)
            ax.set_xlabel('% Difference', fontsize=font_size)

            # Set reasonable x-axis limits based on the data
            max_abs_diff = max(abs(np.max(diff_values)), abs(np.min(diff_values)))
            limit = min(max(20, np.ceil(max_abs_diff / 10) * 10), 100)
            ax.set_xlim(-limit, limit)
            for tick in ax.xaxis.get_majorticklabels():  # example for xaxis
                tick.set_fontsize(font_size) 

            # Create a grid for readability
            ax.grid(axis='x', linestyle='-', alpha=0.3, zorder=0)

            # Add a legend for the outcomes
            handles = [plt.Rectangle((0,0),1,1, color=color_dict[outcome]) for outcome in unique_outcomes[::-1]]
            ax.legend(handles[::-1], unique_outcomes[::-1], loc='upper center', bbox_to_anchor=(0.5, -0.15), 
                     fontsize=font_size-1, ncol=min(len(unique_outcomes), 3))

            # Add value labels to the bars
            for i, v in enumerate(diff_values):
                text_color = 'black'
                if abs(v) > limit * 0.9:  # If value is close to the limit, put label inside
                    text_pos = v - np.sign(v) * 5
                else:
                    text_pos = v + np.sign(v) * 2
                ax.text(text_pos, i, f"{v:.1f}%", va='center', ha='center' if v < 0 else 'left',
                        color=text_color, fontsize=font_size-1)
            
            if many_categories:
                ax.set_position([0.65, 0.11, 0.25, 0.3])

            pdf.savefig(fig)
            plt.close(fig)

            if many_categories:
                # NEW PDF PAGE - T-Test results, Descriptive Statistics, Data Time Series
                    fig2, axes2 = plt.subplot_mosaic([
                        ["Descriptive Statistics 1"],
                        ["Descriptive Statistics 2"],
                        ["Empty 1"],
                        ["Empty 2"]],
                        figsize=(8.27, 11.69), dpi=300)  # A4 size in inches
                    add_header_or_footer_to_a4_portrait(fig, header_image_path, position='header')
                    add_header_or_footer_to_a4_portrait(fig, footer_image_path, position='footer', page_number=2, total_pages=total_pages)

                    difference = np.array(observed_count) - np.array(results['expected_counts'])

                    total_cols_1 = 2 + (len(categories[:4]) * 3)
                    total_cols_2 = 2 + (len(categories[4:]) * 3)


                    if len(outcomes) <= 3:
                        bbox_1 = [0, 0.3, 1, 0.5]
                        bbox_2 = [0, 0.5, 1, 0.5]
                    elif 3 < len(outcomes) <= 5:
                        bbox_1 = [0, 0.2, 1, 0.5]
                        bbox_2 = [0, 0.4, 1, 0.5]
                    else:
                        bbox_1 = [0, 0.1, 1, 0.5]
                        bbox_2 = [0, 0.3, 1, 0.5]
                        

                    ax = axes2["Descriptive Statistics 1"]
                    ax.set_title("Descriptive Statistics", loc='left', pad=-30, y=1.1)
                    ax.axis('off')

                    descriptive_table_widths_1 = [0.15, 0.05] + [0.075] * (len(categories[:4]) * 3)
                    descriptive_table_data_1 = [
                        ["\n\nOutcome", "\n\nN"] + [""] * (len(categories[:4]) * 3),
                        ["", ""]
                    ]

                    for i, category in enumerate(categories[:4]):
                        col_index = 2 + (i * 3)
                        descriptive_table_data_1[0][col_index] = f"Cat {i + 1} / {category}"
                    
                    for i in range(len(categories[:4])):
                        # col_index = 2 + (i * 3)
                        descriptive_table_data_1[1].extend(["E", "O", r"$\Delta$"])

                    for i, outcome in enumerate(outcomes):
                        expected_counts = results['expected_counts'][i][:4]
                        observed_counts = observed_count[i][:4]
                        sample_size = sum(observed_counts)
                        differences = difference[i][:4]

                        # Create a row with maximum 14 elements
                        row = [
                            outcome,
                            f"{sample_size}",
                            f"{expected_counts[0]}",
                            f"{observed_counts[0]}",
                            f"{differences[0]}",
                            f"{expected_counts[1]}",
                            f"{observed_counts[1]}",
                            f"{differences[1]}",
                            f"{expected_counts[2]}",
                            f"{observed_counts[2]}",
                            f"{differences[2]}",
                            f"{expected_counts[3]}",
                            f"{observed_counts[3]}",
                            f"{differences[3]}"
                        ]
                        descriptive_table_data_1.append(row)

                    descriptive_table_bg_colors_1 = [
                        [grey] * total_cols_1,
                        [grey] * total_cols_1
                    ]

                    bg_none_1 = [
                        ["none"] * total_cols_1,
                        ["none"] * total_cols_1
                    ]

                    for _ in range(len(outcomes)):
                        descriptive_table_bg_colors_1.append(["#ffffff"] * total_cols_1)
                        bg_none_1.append(["none"] * total_cols_1)

                    table_bg_1 = ax.table(bbox=bbox_1, cellColours=descriptive_table_bg_colors_1)
                    for cell in table_bg_1._cells.values():
                        cell.set_edgecolor("none")

                    descriptive_table_1 = ax.table(
                        cellText=descriptive_table_data_1,
                        cellColours=bg_none_1,
                        colWidths=descriptive_table_widths_1,
                        loc='upper left',
                        cellLoc='center',
                        bbox=bbox_1
                    )

                    descriptive_table_1.auto_set_font_size(False)
                    descriptive_table_1.set_fontsize(font_size)

                    for cell in descriptive_table_1._cells.values():
                        cell.set_edgecolor(edge_color)
                        cell.set_linewidth(0.5)

                    mergecells(descriptive_table_1, [(0, 0), (1, 0)])
                    mergecells(descriptive_table_1, [(0, 1), (1, 1)])

                    for i in range(len(categories[:4])):
                        mergecells(descriptive_table_1, [(0, 2 + i * 3), (0, 2 + i * 3 + 1), (0, 2 + i * 3 + 2)])
                        cell = descriptive_table_1.get_celld()[(0, 2 + i * 3)]
                        cell.set_text_props(ha='left')




                    # Second table
                    ax = axes2["Descriptive Statistics 2"]
                    ax.axis('off')
                    descriptive_table_widths_2 = [0.15, 0.05] + [0.075] * (len(categories[4:]) * 3)
                    descriptive_table_data_2 = [
                        ["\n\nOutcome", "\n\nN"] + [""] * (len(categories[4:]) * 3),
                        ["", ""]
                    ]
                    for i, category in enumerate(categories[4:]):
                        col_index = 2 + (i * 3)
                        descriptive_table_data_2[0][col_index] = f"Cat {i + 1} / {category}"

                    for i in range(len(categories[4:])):
                        # col_index = 2 + (i * 3)
                        descriptive_table_data_2[1].extend(["E", "O", r"$\Delta$"])

                    for i, outcome in enumerate(outcomes):
                        expected_counts = results['expected_counts'][i][4:]
                        observed_counts = observed_count[i][4:]
                        sample_size = sum(observed_counts)
                        differences = difference[i][4:]

                        # Start with the basic row elements
                        row = [outcome, f"{sample_size}"]
                        
                        # Dynamically add data for each category in categories[4:]
                        for j in range(len(categories[4:])):
                            if j < len(expected_counts):
                                row.extend([
                                    f"{expected_counts[j]}",
                                    f"{observed_counts[j]}",
                                    f"{differences[j]}"
                                ])
                            else:
                                row.extend(["", "", ""])
                        
                        # Fill with empty strings if needed to match total_cols_2
                        while len(row) < total_cols_2:
                            row.append("")
                            
                        descriptive_table_data_2.append(row)

                    descriptive_table_bg_colors_2 = [
                        [grey] * total_cols_2,
                        [grey] * total_cols_2
                    ]

                    bg_none_2 = [
                        ["none"] * total_cols_2,
                        ["none"] * total_cols_2
                    ]
                    for _ in range(len(outcomes)):
                        descriptive_table_bg_colors_2.append(["#ffffff"] * total_cols_2)
                        bg_none_2.append(["none"] * total_cols_2)

                    table_bg_2 = ax.table(bbox=bbox_2, cellColours=descriptive_table_bg_colors_2)
                    for cell in table_bg_2._cells.values():
                        cell.set_edgecolor("none")

                    descriptive_table_2 = ax.table(
                        cellText=descriptive_table_data_2,
                        cellColours=bg_none_2,
                        colWidths=descriptive_table_widths_2,
                        loc='upper left',
                        cellLoc='center',
                        bbox=bbox_2
                    )

                    descriptive_table_2.auto_set_font_size(False)
                    descriptive_table_2.set_fontsize(font_size)
                    for cell in descriptive_table_2._cells.values():
                        cell.set_edgecolor(edge_color)
                        cell.set_linewidth(0.5)

                    mergecells(descriptive_table_2, [(0, 0), (1, 0)])
                    mergecells(descriptive_table_2, [(0, 1), (1, 1)])
                    for i in range(len(categories[4:])):
                        mergecells(descriptive_table_2, [(0, 2 + i * 3), (0, 2 + i * 3 + 1), (0, 2 + i * 3 + 2)])
                        cell = descriptive_table_2.get_celld()[(0, 2 + i * 3)]
                        cell.set_text_props(ha='left')


                    ax = axes2["Empty 1"]
                    ax.axis('off')

                    ax = axes2["Empty 2"]
                    ax.axis('off')
                
                    pdf.savefig(fig2)
                    plt.close(fig2)

        pdf_io.seek(0)
        plt.close('all')
        return pdf_io


def _chi_square_test_general(observed_counts, expected_counts=None, alpha=0.05, category_names=None, outcome_names=None):
    """
    Führt einen Chi-Quadrat-Test für mehrere Kategorien (3-7) mit mehreren Outcomes (2-7) durch.
    
    Parameter:
    ----------
    observed_counts : list or numpy array
        Beobachtete Häufigkeiten für jede Kategorie und jeden Outcome
        Format: Liste/Array mit m Einträgen (m Kategorien), jeder Eintrag ist eine Liste/Array mit n Outcomes
    expected_counts : list or numpy array, optional
        Erwartete Häufigkeiten für jede Kategorie und jeden Outcome.
        Wenn None, werden die erwarteten Häufigkeiten automatisch berechnet,
        basierend auf der Nullhypothese der Unabhängigkeit.
    alpha : float
        Signifikanzniveau (typischerweise 0.05 oder 0.01)
    category_names : list, optional
        Namen der Kategorien
    outcome_names : list, optional
        Namen der Outcomes für die Visualisierung
    
    Returns:
    --------
    dict
        Ergebnis des Chi-Quadrat-Tests mit allen relevanten Werten
    """
    # Konvertiere zu numpy Arrays falls notwendig
    observed = np.array(observed_counts)
    
    # Anzahl der Kategorien und Outcomes bestimmen
    n_categories, n_outcomes = observed.shape
    
    # Wenn keine erwarteten Häufigkeiten angegeben, berechne sie basierend auf den Randsummen
    if expected_counts is None:
        # Berechne Randsummen
        row_sums = observed.sum(axis=1)  # Summen pro Kategorie
        col_sums = observed.sum(axis=0)  # Summen pro Outcome
        total_sum = observed.sum()       # Gesamtsumme
        
        # Berechne erwartete Häufigkeiten
        expected = np.zeros_like(observed, dtype=float)
        for i in range(n_categories):  # Für jede Kategorie
            for j in range(n_outcomes):  # Für jeden Outcome
                expected[i, j] = (row_sums[i] * col_sums[j]) / total_sum
    else:
        expected = np.array(expected_counts)
    
    # Wenn keine Namen angegeben, erzeuge Standardnamen
    if category_names is None:
        category_names = [f"Kategorie {i+1}" for i in range(n_categories)]
    
    if outcome_names is None:
        outcome_names = [f"Outcome {i+1}" for i in range(n_outcomes)]
        
    # Chi-Quadrat-Berechnung
    contingency_table = observed
    chi2_stat, p_value, df, expected_table = stats.chi2_contingency(contingency_table)
    
    # Prüfen Sie, ob die erwarteten Werte von chi2_contingency mit unseren berechneten Werten übereinstimmen
    if not np.allclose(expected, expected_table, rtol=1e-5):
        expected = expected_table

    # Calculate total sample size
    total_sample_size = contingency_table.sum()
    
    # Berechnung der Chi-Quadrat-Werte und p-Werte für jede Outcome-Gruppe (für Informationszwecke)
    chi2_values = []
    p_values = []
    for i in range(n_outcomes):
        # Erstelle mx1-Kontingenztabelle für diesen Outcome
        outcome_table = observed[:, i].reshape(n_categories, 1)
        outcome_expected = expected[:, i].reshape(n_categories, 1)
        
        # Berechne Chi-Quadrat für diesen einzelnen Outcome
        chi2_for_outcome = np.sum((outcome_table - outcome_expected)**2 / outcome_expected)
        p_for_outcome = 1 - stats.chi2.cdf(chi2_for_outcome, n_categories - 1)  # df=n_categories-1 für jede mx1-Tabelle
        
        chi2_values.append(chi2_for_outcome)
        p_values.append(p_for_outcome)
    
    # Gesamter Chi-Quadrat-Wert
    total_chi2 = chi2_stat
    total_p_value = p_value
    
    # Kritischer Wert für das gegebene alpha
    critical_value = stats.chi2.ppf(1 - alpha, df)
    
    # Ergebnis
    results = {
        "chi2_statistic": total_chi2,
        "chi2_per_outcome": chi2_values,
        "p_value": total_p_value,
        "p_values_per_outcome": p_values,
        "degrees_of_freedom": df,
        "critical_value": critical_value,
        "alpha": alpha,
        "n_outcomes": n_outcomes,
        "expected_counts": np.round(expected).astype(int).tolist(),
        "total_sample_size": total_sample_size
    }
    
    return results

def split_categories(categories, max_line_length=50, max_per_line=4):
    lines = []
    current_line = []
    current_length = 0

    for cat in categories:
        cat_str = cat if not current_line else '; ' + cat
        if (len(current_line) >= max_per_line or
            current_length + len(cat_str) > max_line_length):
            lines.append(''.join(current_line))
            current_line = [cat]
            current_length = len(cat)
        else:
            current_line.append('; ' + cat if current_line else cat)
            current_length += len(cat_str)
    if current_line:
        lines.append(''.join(current_line))
    return '\n'.join(lines)