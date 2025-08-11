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


class TwoChiSquaredConfig(BaseModel):
    title: str
    variant: str
    alphalevel: float

    '''
    categories: ["Männer", "Frauen"]
    outcomes: ["Produkt A", "Produkt B"]
    observed_count: [[count("Männer")("Produkt A"), count("Männer")("Produkt B")], [count("Frauen")("Produkt A"), count("Frauen")("Produkt B")]]
    '''

    categories: Optional[List[str]] = None  # Variant 1
    outcomes: Optional[List[str]] = None 
    observed_count: Optional[List[List[int]]] = None    # Variant 1

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

class TwoChiSquaredData(BaseModel):
    
    '''
    "values": {
    "Männer": {"expected_percent": [], "samples": []},
    "Frauen": {"expected_percent": [], "samples": []}
    }
    '''

    values: Optional[Dict[str, Dict[str, List[Union[float, str]]]]] = Field(None)     # Variant 2

class TwoChiSquaredRequest(BaseModel):
    project: str
    projectNumber: Optional[str] = None
    step: str
    config: TwoChiSquaredConfig
    data: Optional[TwoChiSquaredData] = None

class TwoChiSquared:
    def __init__(self, data:dict):
        try:
            validated_data = TwoChiSquaredRequest(**data)
            self.project = validated_data.project
            self.step = validated_data.step
            self.config = validated_data.config
            self.data = validated_data.data
            self.projectNumber = validated_data.projectNumber
            

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
        outcomes = self.config.outcomes
        projectNumber = self.projectNumber

        if variant == "Summarized data":

            categories = self.config.categories
            observed_count = self.config.observed_count
            # Calculate sample size for each category
            sample_sizes = []
            # Calculate sample size for each outcome
            for outcome_idx in range(len(outcomes)):
                outcome_total = 0
                for cat_idx in range(len(categories)):
                    outcome_total += observed_count[cat_idx][outcome_idx]
                sample_sizes.append(outcome_total)

        else:
            # Obtain categories
            categories = list(self.data.values.keys())
            observed_count = []
            for cat_idx, category in enumerate(categories):
                cat_counts = []
                for outcome in outcomes:
                    cat_counts.append(self.data.values[category]['samples'].count(outcome))
                observed_count.append(cat_counts)
            # Calculate sample size for each category
            sample_sizes = []
            # Calculate sample size for each outcome
            for outcome_idx in range(len(outcomes)):
                outcome_total = 0
                for cat_idx in range(len(categories)):
                    outcome_total += observed_count[cat_idx][outcome_idx]
                sample_sizes.append(outcome_total)

        results = _chi_square_test(observed_count, expected_counts=None, alpha=alphalevel, category_names=categories)
        # variant_str = "     Data in columns" if variant == "Data in columns" else "     Summarized Data"

        if results['p_value'] < alphalevel:
            hypothesis_string = "The $\mathrm{Cat_{1}}$ is significantly different from $\mathrm{Cat_{2}}$"
            table_color = "#9cc563"
        else:
            hypothesis_string = "The $\mathrm{Cat_{1}}$ is not significantly different from $\mathrm{Cat_{2}}$"
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

            add_header_or_footer_to_a4_portrait(fig, header_image_path, position='header')
            add_header_or_footer_to_a4_portrait(fig, footer_image_path, position='footer', page_number=1, total_pages=1, projectNumber=projectNumber)


            # Define the colors + fontsize
            grey = "#e7e6e6"
            green_table = "#9cc563"
            lightgreen_table = "#d6ed5f"
            font_size=7
            edge_color = "#7c7c7c"

            # Table overview of the defective test results
            ax = axes["Defective-Test Results"]
            ax.axis('off')

            # Format outcomes string with line break if more than 4 outcomes
            if len(outcomes) > 4:
                outcomes_str = '\n'.join([', '.join(outcomes[:4]), ', '.join(outcomes[4:])])
            else:
                outcomes_str = ', '.join(outcomes)

            table_data = [
                ["Configuration", "", "Hypothesis", "", ""],
                [variant, "", r"$\mathrm{H_{0}}: \mathrm{Cat_{1} = Cat_{2}}$", "", "p-Value*"],
                ["Test-Setup", "Different", r"$\mathrm{H_{1}}: \mathrm{Cat_{1} \neq Cat_{2}}$", "", f"{results['p_value']:.3f}"],
                ["Sample size:", f"{results['total_sample_size']}", "", "", ""],
                ["Outcomes", f"{outcomes_str}", "empty", "Degree of freedom", f"{results['degrees_of_freedom']}"],
                ["Category 1", f"{categories[0]}", "", "", ""],
                ["Category 2", f"{categories[1]}", "empty", "", ""],
                ["Chi-Square", f"{results['chi2_statistic']:.2f}", "empty", "", ""],
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
            # mergecells(table, [(1, 0), (1, 1)])
            mergecells(table, [(4, 1), (4, 2)])
            mergecells(table, [(5, 2), (6, 2), (7, 2), (8, 2)])
            mergecells(table, [(1, 3), (2, 3), (3, 3)])
            mergecells(table, [(5, 3), (6, 3), (7, 3)])
            mergecells(table, [(5, 4), (6, 4), (7, 4)])
            mergecells(table, [(8, 3), (8, 4)])
            mergecells(table, [(9, 0), (9, 1), (9, 2), (9, 3), (9, 4)])

            table.get_celld()[9, 0].set_fontsize(5)

            cell_text_centered_1 = table.get_celld()[(0, 3)]
            cell_text_centered_1.set_text_props(
                text='Results',
                x=1.5,
                y=0.5,
                visible=True,
                ha='center'
            )
            cell_text_small = table.get_celld()[(9, 0)]
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

            left_text = [(4, 1), (5, 3), (8, 3), (9, 0)]
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

            if len(outcomes) < 3:
                pad = -50
                bbox = [0, 0.3, 1, 0.3]
            elif 3 <= len(outcomes) <= 5:
                pad = -35
                bbox = [0, 0.3, 1, 0.45]
            else:
                pad = -20
                bbox = [0, 0.3, 1, 0.6]

            ax.set_title("Descriptive Statistics", loc='left', pad=pad, y=1.1)
            descriptive_table_widths = [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]
            descriptive_table_data = [
                ["\n\nOutcome", "\n\nN", "", f"Cat 1 / {categories[0]}", "", "", f"Cat 2 / {categories[1]}", ""],
                ["", "", "Expected", "Observed", "Difference", "Expected", "Observed", "Difference"]
            ]

            for i, outcome in enumerate(outcomes):

                expected_count_1 = round(results['expected_counts'][0][i], 0)
                observed_count_1 = observed_count[0][i]
                delta_1 = observed_count_1 - expected_count_1

                expected_count_2 = round(results['expected_counts'][1][i], 0)
                observed_count_2 = observed_count[1][i]
                delta_2 = observed_count_2 - expected_count_2

                row = [
                    outcome,
                    f"{sample_sizes[i]}",
                    f"{expected_count_1}",
                    f"{observed_count_1}",
                    f"{delta_1}",
                    f"{expected_count_2}",
                    f"{observed_count_2}",
                    f"{delta_2}"
                ]
                descriptive_table_data.append(row)

            # Create table colors
            descriptive_bg_colors = []
            descriptive_bg_colors.append([grey] * 8)  # Header row 1
            descriptive_bg_colors.append([grey] * 8)     # Header row 2

            # Add colors for data rows
            for i in range(len(outcomes)):
                row_color = ["#ffffff"] * 8
                descriptive_bg_colors.append(row_color)
            
            bg_table = ax.table(bbox=bbox, cellColours=descriptive_bg_colors)
            for cell in bg_table._cells.values():
                cell.set_edgecolor("none")

            bg_none = []
            for _ in range(len(outcomes) + 2):
                row_color = ["none"] * 8
                bg_none.append(row_color)
            
            descriptive_table = ax.table(
                cellText=descriptive_table_data,
                colWidths=descriptive_table_widths,
                cellLoc='center',
                loc='upper left',
                cellColours=bg_none,
                bbox=bbox
            )

            mergecells(descriptive_table, [(0, 0), (1, 0)])
            mergecells(descriptive_table, [(0, 1), (1, 1)])
            mergecells(descriptive_table, [(0, 2), (0, 3), (0, 4)])
            mergecells(descriptive_table, [(0, 5), (0, 6), (0, 7)])

            descriptive_cell_text_1 = descriptive_table.get_celld()[(0, 3)]
            descriptive_cell_text_1.set_text_props(
                text=f"Cat 1 / {categories[0]}",
                x=1.5,
                y=0.5,
                visible=True,
                ha='center'
            )
            descriptive_cell_text_2 = descriptive_table.get_celld()[(0, 6)]
            descriptive_cell_text_2.set_text_props(
                text=f"Cat 1 / {categories[1]}",
                x=1.5,
                y=0.5,
                visible=True,
                ha='center'
            )

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

            # Create the comparison bar chart
            ax = axes["Comparison Bar"]
            ax.set_title("Percentage Profiles Chart\nCompare the profiles", loc='center', fontsize=font_size)

            # Calculate percentages for each category
            cat_percentages = []
            for cat_idx, cat_counts in enumerate(observed_count):
                total = sum(cat_counts)
                percentages = [count / total * 100 for count in cat_counts]
                cat_percentages.append(percentages)
            cat_percentages = cat_percentages[::-1]
            # Calculate average percentages across categories
            avg_percentages = []
            for outcome_idx in range(len(outcomes)):
                avg = sum(cat_percentages[cat_idx][outcome_idx] for cat_idx in range(len(categories))) / len(categories)
                avg_percentages.append(avg)

            # Add average to cat_percentages
            cat_percentages.append(avg_percentages)
            categories = categories[::-1]
            categories_with_avg = categories + ["Average"]

            bar_width = 0.35 if len(outcomes) <= 3 else 0.25 if len(outcomes) <= 5 else 0.11

            # Reorganize data for plotting (transpose categories and outcomes)
            transposed_percentages = []
            for outcome_idx in range(len(outcomes)):
                outcome_data = [cat_percentages[cat_idx][outcome_idx] for cat_idx in range(len(categories_with_avg))]
                transposed_percentages.append(outcome_data)

            transposed_percentages = transposed_percentages[::-1]

            # Plot the bars for each outcome
            x = np.arange(len(categories_with_avg))
            for i, outcome in enumerate(outcomes):
                offset = i - (len(outcomes)-1)/2
                ax.barh(x + offset*bar_width, 
                       transposed_percentages[i], 
                       bar_width, 
                       label=outcome,
                       color=COLOR_PALETTE[i * 2 % 7], edgecolor=edge_color, zorder=5)  # Use modulo to handle more than 10 outcomes

            # Add labels and legend
            ax.tick_params(axis='x', labelsize=font_size)
            ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.0f}%'))
            ax.set_yticks(x)
            ax.set_yticklabels(categories_with_avg, fontsize=font_size)
            ax.set_xlim(0, max(max(transposed_percentages))*1.2)
            handles, labels = ax.get_legend_handles_labels()
            ax.legend(handles[::-1], labels[::], fontsize=font_size, loc='upper left', bbox_to_anchor=(0, -0.1), 
                     ncol=min(len(outcomes), 3), frameon=True, framealpha=0.8)
            ax.grid(True, alpha=0.3, zorder=0)


            # Add percentage labels to the bars
            for i, outcome_data in enumerate(transposed_percentages):
                offset = i - (len(outcomes)-1)/2
                for j, percentage in enumerate(outcome_data):
                    ax.text(percentage + 1, x[j] + offset*bar_width, 
                           f'{percentage:.1f}%',
                           ha='left', va='center', 
                           fontsize=font_size-1)
                
            # Create the difference bar chart
            ax = axes["Difference Bar"]
            ax.set_title("% Difference between Observed and\nExpected Counts", loc='center', fontsize=font_size)

            # Calculate the percentage difference between observed and expected counts
            differences = []
            for cat_idx, cat in enumerate(categories):
                cat_diff = []
                for outcome_idx, outcome in enumerate(outcomes):
                    observed = observed_count[cat_idx][outcome_idx]
                    # Fix the index order here:
                    expected = results['expected_counts'][cat_idx][outcome_idx]
                    # Calculate percentage difference
                    if expected > 0:  # Avoid division by zero
                        diff_percent = ((observed - expected) / expected) * 100
                    else:
                        diff_percent = 0
                    cat_diff.append(diff_percent) 
                differences.append(cat_diff[::-1])

            # Transpose the differences for plotting by outcome
            transposed_diff = []
            for outcome_idx in range(len(outcomes)):
                # Reverse the order of categories
                outcome_data = [differences[cat_idx][outcome_idx] for cat_idx in range(len(categories)-1, -1, -1)]
                transposed_diff.append(outcome_data)

            # Reverse the categories list for display
            # reversed_categories = categories[::-1]
            
            # Plot bars for each outcome
            x = np.arange(len(categories))
            for i, outcome in enumerate(outcomes):
                offset = i - (len(outcomes)-1)/2
                bars = ax.barh(x + offset*bar_width, 
                             transposed_diff[i], 
                             bar_width*0.8, 
                             label=outcome,
                             color=COLOR_PALETTE[i * 2 % 7], edgecolor=edge_color, zorder=5)

                # Add percentage labels to the bars
                for j, diff in enumerate(transposed_diff[i]):
                    # Position the text based on the sign of the difference
                    if diff >= 0:
                        ha_pos = 'left'
                        x_pos = - 1
                    else:
                        ha_pos = 'right'
                        x_pos = + 1
                    
                    ax.text(x_pos, x[j] + offset*bar_width, 
                           f'{diff:.1f}%',
                           ha=ha_pos, va='center', 
                           fontsize=font_size-1)

            # Add a vertical line at x=0 to show the baseline
            ax.axvline(x=0, color='black', linestyle='-', linewidth=0.8, zorder=4)

            # Configure the chart
            ax.tick_params(axis='x', labelsize=font_size)
            ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.0f}%'))
            ax.set_yticks(x)
            ax.set_yticklabels(categories, fontsize=font_size)

            # Determine x-axis limits based on the range of differences
            max_diff = max([max(abs(min(diffs)), abs(max(diffs))) if diffs else 0 for diffs in transposed_diff])
            ax.set_xlim(-max_diff*1.2, max_diff*1.2)

            # Add a grid
            ax.grid(True, alpha=0.3, zorder=0)
            handles, labels = ax.get_legend_handles_labels()
            ax.legend(handles[::-1], labels[::], fontsize=font_size, loc='upper left', 
                      bbox_to_anchor=(0, -0.1), ncol=min(len(outcomes), 3), 
                      frameon=True, framealpha=0.8)

            pdf.savefig(fig)
            plt.close(fig)

        pdf_io.seek(0)
        plt.close('all')
        return pdf_io
        
        



def _chi_square_test(observed_counts, expected_counts=None, alpha=0.05, category_names=None, outcome_names=None):
    """
    Führt einen Chi-Quadrat-Test für zwei Kategorien mit mehreren Outcomes durch.
    
    Parameter:
    ----------
    observed_counts : list or numpy array
        Beobachtete Häufigkeiten für jede Kategorie und jeden Outcome
        Format: Liste/Array mit 2 Einträgen, jeder Eintrag ist eine Liste/Array mit n Outcomes
    expected_counts : list or numpy array, optional
        Erwartete Häufigkeiten für jede Kategorie und jeden Outcome.
        Wenn None, werden die erwarteten Häufigkeiten automatisch berechnet,
        basierend auf der Nullhypothese der Unabhängigkeit.
    alpha : float
        Signifikanzniveau (typischerweise 0.05 oder 0.01)
    category_names : list, optional
        Namen der beiden Kategorien (z.B. ["Männer", "Frauen"])
    outcome_names : list, optional
        Namen der Outcomes für die Visualisierung
    
    Returns:
    --------
    dict
        Ergebnis des Chi-Quadrat-Tests mit allen relevanten Werten
    """
    # Konvertiere zu numpy Arrays falls notwendig
    observed = np.array(observed_counts)
    
    # Anzahl der Outcomes bestimmen
    n_outcomes = observed.shape[1]
    
    # Wenn keine erwarteten Häufigkeiten angegeben, berechne sie basierend auf den Randsummen
    if expected_counts is None:
        # Berechne Randsummen
        row_sums = observed.sum(axis=1)  # Summen pro Kategorie
        col_sums = observed.sum(axis=0)  # Summen pro Outcome
        total_sum = observed.sum()       # Gesamtsumme
        
        # Berechne erwartete Häufigkeiten
        expected = np.zeros_like(observed, dtype=float)
        for i in range(2):  # Für jede Kategorie
            for j in range(n_outcomes):  # Für jeden Outcome
                expected[i, j] = (row_sums[i] * col_sums[j]) / total_sum
    else:
        expected = np.array(expected_counts)
    
    # Wenn keine Namen angegeben, erzeuge Standardnamen
    if category_names is None:
        category_names = ["Kategorie 1", "Kategorie 2"]
    
    if outcome_names is None:
        outcome_names = [f"Outcome {i+1}" for i in range(n_outcomes)]
        
    # Chi-Quadrat-Berechnung
    # Bei zwei Kategorien (2x2 oder 2xn Tabelle) kann ^ den Test mit scipy.stats.chi2_contingency durchführen
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
        # Erstelle 2x2-Kontingenztabelle für diesen Outcome
        outcome_table = observed[:, i].reshape(2, 1)
        outcome_expected = expected[:, i].reshape(2, 1)
        
        # Berechne Chi-Quadrat für diesen einzelnen Outcome
        # Da wir nur 1 df für jeden einzelnen Test haben, können wir die Formel direkt anwenden
        chi2_for_outcome = np.sum((outcome_table - outcome_expected)**2 / outcome_expected)
        p_for_outcome = 1 - stats.chi2.cdf(chi2_for_outcome, 1)  # df=1 für jede 2x1-Tabelle
        
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
        "expected_counts": expected.tolist(),
        "total_sample_size": total_sample_size
    }
    
    
    return results