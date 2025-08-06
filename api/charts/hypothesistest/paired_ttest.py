import io
import pandas as pd
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt
import textwrap
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages
from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Optional, Union, Any
from statsmodels.stats.power import TTestPower
from api.schemas import BusinessLogicException

from ...utils.pdf_utils import add_header_or_footer_to_a4_portrait

header_image_path = 'assets/img/Header.png'
footer_image_path = 'assets/img/Footer.png'

from ...utils.mpl_table_utils import merge_mpl_table_cells as mergecells

class PairedTtestConfig(BaseModel):
    title: str
    alphalevel: float = Field(..., gt=0, lt=0.5)
    power: Optional[float] = Field(None, gt=0, lt=1)

# Current format with separate columns for each sample
class PairedTtestDataSeparate(BaseModel):
    values: Dict[str, List[float]]
    
    @field_validator('values')
    def check_exactly_two_series_with_equal_length(cls, v):
        if len(v) != 2:
            raise BusinessLogicException(
                error_code="error_data_size",
                field="values",
                details={"message": "Exactly two data series are required"}
            )
        
        # Get keys and check lengths
        keys = list(v.keys())
        if len(v[keys[0]]) != len(v[keys[1]]):
            raise BusinessLogicException(
                error_code="error_data_length_paired",
                field="values",
                details={"message": "Both series must have the same length for paired analysis"}
            )
            
        # Check for NaNs or infinites
        for series_name, data in v.items():
            if any(not np.isfinite(x) for x in data):
                raise ValueError(f"Series '{series_name}' contains NaN or infinite values")
            
        return v

# Alternative format with all values in a single column
class PairedTtestDataCombined(BaseModel):
    values: List[float]
    groups: List[str]
    
    @field_validator('groups')
    def check_exactly_two_groups(cls, v, values):
        if 'values' not in values:
            return v
            
        if len(v) != len(values['values']):
            raise BusinessLogicException(
                error_code="error_column_length",
                field="groups",
                details={"message": "Values and groups must have the same length"}
            )
            
        unique_groups = set(v)
        if len(unique_groups) != 2:
            raise BusinessLogicException(
                error_code="error_group_identifiers",
                field="groups",
                details={"message": "Exactly two different group identifiers are required"}
            )
            
        # Count samples per group to ensure equal counts
        group_counts = {}
        for group in v:
            group_counts[group] = group_counts.get(group, 0) + 1
            
        # Get the unique group names
        groups = list(group_counts.keys())
        if len(groups) == 2 and group_counts[groups[0]] != group_counts[groups[1]]:
            raise BusinessLogicException(
                error_code="error_data_length_paired",
                field="groups",
                details={"message": "Both series must have the same length for paired analysis"}
            )
            
        return v
    
    @field_validator('values')
    def check_valid_numbers(cls, v):
        if any(not np.isfinite(x) for x in v):
            raise ValueError("Data contains NaN or infinite values")
        return v

class PairedTtestRequest(BaseModel):
    project: str
    projectNumber: Optional[str] = None
    step: str
    config: PairedTtestConfig
    data: Any  #  validate this separately
    
    @field_validator('data')
    def validate_data_format(cls, v):
        # Try the separate format first
        try:
            if 'values' in v and isinstance(v['values'], dict):
                return PairedTtestDataSeparate(**v)
            elif 'values' in v and isinstance(v['values'], list) and 'groups' in v:
                return PairedTtestDataCombined(**v)
            else:
                raise ValueError("Data format not recognized")
        except Exception as e:
            raise ValueError(f"Invalid data format: {str(e)}")
    
class PairedTtest:
    """
    A class to perform paired t-tests on two datasets and generate a PDF report with the results.
    Attributes:
        project (str): The project name.
        step (str): The step name.
        config (object): The configuration object containing title and alpha level.
        data (dict): The dictionary containing the datasets.
    Methods:
        __init__(data: dict):
            Initializes the PairedTtest object with the provided data.
        process():
            Processes the paired t-test, calculates descriptive statistics, and generates a PDF report.
    """
    def __init__(self, data:dict):
        try:
            validated_data = PairedTtestRequest(**data)
            self.project = validated_data.project
            self.step = validated_data.step
            self.config = validated_data.config
            self.data = validated_data.data
            self.projectNumber = validated_data.projectNumber
            
            # Convert combined format to separate format if needed
            if isinstance(self.data, PairedTtestDataCombined):
                self._convert_combined_to_separate()
                
        except Exception as e:
            raise BusinessLogicException(
                error_code="error_validation",
                field=str(e),
                details={"message": f"Invalid or missing field: {str(e)}"}
            )
    
    def _convert_combined_to_separate(self):
        """Convert combined data format to separate format for paired t-test"""
        values = self.data.values
        groups = self.data.groups
        
        # Create pair IDs based on position in the list
        # For paired data, we assume the data is already ordered so that
        # the first element of group A and the first element of group B form a pair, and so on
        pairs = []
        group_counts = {group: 0 for group in set(groups)}
        for group in groups:
            pairs.append(group_counts[group])
            group_counts[group] += 1
        
        # Get unique group names
        unique_groups = sorted(set(groups))
        if len(unique_groups) != 2:
            raise ValueError("Exactly two groups are required")
        
        # Create dictionary of paired data
        separate_data = {group: [] for group in unique_groups}
        
        # Sort by pair ID to ensure proper ordering
        paired_data = sorted(zip(values, groups, pairs), key=lambda x: x[2])
        
        # Create a dictionary to store values by pair ID and group
        pair_dict = {}
        for value, group, pair_id in paired_data:
            if pair_id not in pair_dict:
                pair_dict[pair_id] = {}
            pair_dict[pair_id][group] = value
        
        # Reconstruct separate data ensuring pairs are aligned
        for pair_id, group_values in pair_dict.items():
            if len(group_values) != 2:
                raise ValueError(f"Pair {pair_id} does not have exactly two values")
            
            for group in unique_groups:
                if group not in group_values:
                    raise ValueError(f"Group {group} missing for pair {pair_id}")
                separate_data[group].append(group_values[group])
        
        # Create a new PairedTtestDataSeparate object
        self.data = PairedTtestDataSeparate(values=separate_data)
        
    def process(self):
        title = self.config.title
        alpha = self.config.alphalevel
        power = self.config.power
        source_1 = list(self.data.values.keys())[0]
        source_2 = list(self.data.values.keys())[1]
        projectNumber = self.projectNumber

        # Create two dataframes for each dataset
        data_keys = list(self.data.values.keys())
        df1 = pd.DataFrame(self.data.values[data_keys[0]], columns=[data_keys[0]])
        df2 = pd.DataFrame(self.data.values[data_keys[1]], columns=[data_keys[1]])
        # Combined dataframe
        df_combined = pd.concat([df1, df2], axis=1)
        df_combined["Difference"] = df_combined[f"{source_1}"] - df_combined[f"{source_2}"]
        confidence_percent = int((1 - alpha) * 100)

        results = _calculate_paired_statistics(df1, df2, power, alpha)

        # Hypothesis test result
        if results['p_value'] > alpha:
            difference_string = f"The mean values from ”{source_1}” and\n ”{source_2}” are not significantly different"
            difference_color = "#d6ed5f"
        else:
            difference_string = f"The mean values from ”{source_1}” and\n ”{source_2}” are significantly different"
            difference_color = "#9cc563"
        
        descriptive_statistics = pd.DataFrame({
            "Quelle": [source_1, source_2],
            "N": [results['data1_stats']['sample_size'], results['data2_stats']['sample_size']],
            "Mean": [results['data1_stats']['mean'].iloc[0].round(5), results['data2_stats']['mean'].iloc[0].round(5)],
            "Median": [results['data1_stats']['median'].iloc[0].round(5), results['data2_stats']['median'].iloc[0].round(5)],
            "StDev": [results['data1_stats']['std_dev'].iloc[0].round(5), results['data2_stats']['std_dev'].iloc[0].round(5)],
            "SE Mean": [results['data1_stats']['std_err'].iloc[0].round(5), results['data2_stats']['std_err'].iloc[0].round(5)],
            f"{confidence_percent}% CI for µ": [f"({results['data1_stats']['confidence_interval'][0][0].round(5)}; {results['data1_stats']['confidence_interval'][1][0].round(5)})", f"({results['data2_stats']['confidence_interval'][0][0].round(5)}; {results['data2_stats']['confidence_interval'][1][0].round(5)})"],
            "Range": [results['data1_stats']['range'].iloc[0].round(5), results['data2_stats']['range'].iloc[0].round(5)]
        })

        pdf_io = io.BytesIO()

        with PdfPages(pdf_io) as pdf:
            # NEW PDF PAGE - T-Test results, Descriptive Statistics, Data Time Series, Chance and Detectable Difference
            fig, axs = plt.subplot_mosaic([
                ["T-Test Results", "T-Test Results"],
                ["Descriptive Statistics", "Descriptive Statistics"],
                ["TS1", "TS1"],         # Time Series Plots for each dataset
                ["Chance", "Detectable"]],    # Chance and Detectable Difference
                figsize=(8.27, 11.69), dpi=300)  # A4 size in inches
            # fig.subplots_adjust(hspace=0.4)  # Increase hspace to add more space between charts
            fig.suptitle(title, fontsize=14, y=0.92, ha='left', x=0.1)		

            add_header_or_footer_to_a4_portrait(fig, header_image_path, position='header')
            add_header_or_footer_to_a4_portrait(fig, footer_image_path, position='footer', page_number=1, total_pages=2, projectNumber=projectNumber)

            # Define the colors + font size
            edgecolor = "#7c7c7c"
            grey = "#e7e6e6"
            green_table = "#9cc563"
            lightgreen_table = "#d6ed5f"
            data_time_series_blue = "#0054a6"
            data_time_series_black = "#333333"
            font_size=7

            # T-Test Results Table
            ax = axs["T-Test Results"]
            ax.axis('off')

            # Define table data
            table_data = [
                ["Configuration", "", "Hypothesis", "", "", ""],
                ["Each sample in its own column", "", r"$\mathrm{H_{0}: \mu_{difference} = 0}$", "t-Value", "df", "p-Value*"],
                ["Sample 1",f"{source_1}",r"$\mathrm{H_{1}: \mu_{difference} \neq 0}$",f"{results['t_statistic'][0].round(2)}", f"{results['degrees_of_freedom']}", f"{results['p_value'][0].round(3)}"],
                ["Sample 2",f"{source_2}","","","",""],
                ["Test-Setup","Different","","","",f"{results['mean_difference'].round(5)}"],
                ["Alpha-Level",f"{alpha}","empty","","",f"({results['mean_difference_interval'][0].round(5)}; {results['mean_difference_interval'][1].round(5)})"],
                ["Interested\ndifference**",f"{power if power is not None else '-'}","empty",f"{difference_string}","",""],
                ["","","","","",""]
            ]
            # Wrap text of the sources if it is too long
            for row in table_data:
                for i in range(len(row)):
                    if row[i] == f"{source_1}" or row[i] == f"{source_2}":
                        row[i] = textwrap.fill(row[i], width=20)
            # Set the column widths as needed
            col_widths = [0.15, 0.15, 0.15, 0.15, 0.15, 0.15]

            # Background color for the table
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

            # Create table with background colors only and remove edgecolor
            table_bg = ax.table(bbox=[0, 0, 1, 1], cellColours=bg_colors)
            for cell in table_bg._cells.values():
                cell.set_edgecolor("none")

            # Recreate the table layout with "none" as the color
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

            # Create the table with the data + "none" as the color
            table = ax.table(
                bbox=[0, 0, 1, 1],
                cellText=table_data,
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
                cell.set_edgecolor(edgecolor)
                cell.set_linewidth(0.5)

            # Merge the cells of the table
            mergecells(table, [(0, 0), (0, 1)])
            mergecells(table, [(0, 3), (0, 4), (0, 5)])
            mergecells(table, [(1, 0), (1, 1)])
            mergecells(table, [(3, 2), (4, 2), (5, 2), (6, 2)])
            mergecells(table, [(3, 3), (3, 4), (3, 5)])
            mergecells(table, [(4, 3), (4, 4)])
            mergecells(table, [(5, 3), (5, 4)])
            mergecells(table, [(6, 3), (6, 4), (6, 5)])
            mergecells(table, [(7, 0), (7, 1), (7, 2), (7, 3), (7, 4), (7, 5)])

            # Fix the cells, that cannot be defined before mergecells
            table.get_celld()[7, 0].set_fontsize(5)
            

            # Define a dictionary of cell configurations for better organization
            cell_configs = {
                (0, 4): {
                    'text': 'Results',
                    'x': 1.5,
                    'y': 0.5,
                    'ha': 'center'
                },
                (4, 4): {
                    'text': 'Mean difference between\nsample 1 and sample 2',
                    'x': 1.5,
                    'y': 0.5,
                    'ha': 'right'
                },
                (5, 4): {
                    'text': f'{confidence_percent}% CI (confidence interval)',
                    'x': 1.5,
                    'y': 0.5,
                    'ha': 'right'
                },
                (3, 4): {
                    'text': 'Difference of means',
                    'x': 1.5,
                    'y': 0.5,
                    'ha': 'center'
                },
                (7, 0): {
                    'text': '* If the p-value is less than the α-level, then H0 is to be rejected and the alternative hypothesis H1 is to be accepted.\n** Optional: What difference between the two means has a practical value? (Power and sample size)',
                    'color': 'grey',
                    'ha': 'right',
                    'fontsize': 5
                }
            }

            # Apply configurations to cells using a loop
            for (row, col), config in cell_configs.items():
                cell = table.get_celld()[(row, col)]
                props = {
                    'text': config['text'],
                    'x': config.get('x', 0.5),
                    'y': config.get('y', 0.5),
                    'visible': True
                }
                
                # Add optional properties if they exist
                for prop in ['ha', 'color', 'fontsize']:
                    if prop in config:
                        props[prop] = config[prop]
                        
                cell.set_text_props(**props)
            # Define cell text styling configurations in a dictionary
            text_styles = {
                'bold': [(1, 3), (1, 4), (1, 5), (4, 1)],
                'align_left': [(1, 0), (5, 3), (6, 3), (7, 0)],
                'align_right': [(0, 0), (3, 3), (4, 3)]
            }

            # Apply styles to cells using a loop
            for style, cell_positions in text_styles.items():
                for row, col in cell_positions:
                    cell = table.get_celld()[(row, col)]
                    if style == 'bold':
                        cell.set_text_props(weight='bold')
                    elif style == 'align_left':
                        cell.set_text_props(ha='left')
                    elif style == 'align_right':
                        cell.set_text_props(ha='right')

            # Descriptive Statistics Table
            ax = axs['Descriptive Statistics']
            ax.axis('off')
            ax.set_title("Descriptive Statistics", loc='left', pad=-50, y=1.02)
            ax.axis('tight')
            
            # Adjust column widths as needed
            table_1_widths = [0.20, 0.06, 0.11, 0.11, 0.11, 0.11, 0.19, 0.11]
            table_1 = axs["Descriptive Statistics"].table(
                cellText=descriptive_statistics.values, 
                colLabels=descriptive_statistics.columns, 
                loc='center', 
                cellLoc='center', 
                colWidths=table_1_widths
            )
            table_1.auto_set_font_size(False)
            table_1.set_fontsize(font_size)
            
            for cell in table_1._cells.values():
                cell.set_edgecolor(edgecolor)
                cell.set_linewidth(0.5)

            # Set the top row color to grey
            for col in range(len(descriptive_statistics.columns)):
                cell = table_1[(0, col)]
                cell.set_facecolor(grey)

            # Data Time series plot
            ax = axs["TS1"]
            ax.scatter(df1.index, df1.iloc[:, 0], color=data_time_series_black,s=10, label=source_1)
            ax.scatter(df2.index, df2.iloc[:, 0], color=data_time_series_blue, marker='s', s=10, label=source_2)
            for i in range(len(df1)):
                ax.plot([i, i], [df1.iloc[i, 0], df2.iloc[i, 0]], color='gray', linestyle='--', linewidth=0.5)
            ax.set_title("Data Time Series (paired)", loc='left', y=1.02)
            ax.legend(loc="upper right", fontsize=font_size)
            ax.set_axisbelow(True)
            # Set y-axis limits for the time series plot
            min_val = min(df1.min().iloc[0], df2.min().iloc[0])
            max_val = max(df1.max().iloc[0], df2.max().iloc[0])
            ax.set_ylim(min_val*0.95, max_val * 1.05)
            ax.grid(True, alpha=0.3)

            # Chance of detecting a difference table
            ax = axs["Chance"]
            ax.axis('off')
            ax.set_title("Power and detected difference", loc='left', pad=-50, y=1.2)

            if power is not None:

                if results['power_analysis']['Detection Chance'] < 60:
                    observed_difference_color = "#c00000"
                    observed_difference_text_color = "#ffffff"
                elif 60 <= results['power_analysis']['Detection Chance'] <= 90:
                    observed_difference_color = "#f9b002"
                    observed_difference_text_color = "#000000"
                else:
                    observed_difference_color = "#a7c315"
                    observed_difference_text_color = "#000000"
                
                ax.set_title(f"What is the chance of detecting a difference of {power}?", pad=-70, y=1.02, fontsize=font_size)
                cellText = [
                    ["60%", "", "90%"],
                    ["", "", ""],
                    [f"{results['detectable_difference']['Power 60%']:.6f}", "", f"{results['detectable_difference']['Power 90%']:.6f}"],
                    ["Sample size", "Chance of Detecting a difference", ""],
                    [f"{results['data1_stats']['sample_size']}", "", f"{results['power_analysis']['Detection Chance']}%"]
                ]
            else:
                if results['mean_difference'] < results['detectable_difference']['Power 60%']:
                    observed_difference_interval = "<60%"
                    observed_difference_color = "#c00000"
                    observed_difference_text_color = "#ffffff"
                elif results['detectable_difference']['Power 60%'] <= results['mean_difference'] < results['detectable_difference']['Power 70%']:
                    observed_difference_interval = "60%-70%"
                    observed_difference_color = "#f9b002"
                    observed_difference_text_color = "#000000"
                elif results['detectable_difference']['Power 70%'] <= results['mean_difference'] < results['detectable_difference']['Power 80%']:
                    observed_difference_interval = "70%-80%"
                    observed_difference_color = "#f9b002"
                    observed_difference_text_color = "#000000"
                elif results['detectable_difference']['Power 80%'] <= results['mean_difference'] < results['detectable_difference']['Power 90%']:
                    observed_difference_interval = "80%-90%"
                    observed_difference_color = "#9b002"
                    observed_difference_text_color = "#000000"
                else:
                    observed_difference_interval = ">90%" 
                    observed_difference_color = "#a7c315"
                    observed_difference_text_color = "#000000"

                ax.set_title("Chance of detecting a difference", loc='center', pad=-70, y=1.02, fontsize=font_size)

                cellText = [
                    ["60%", "", "90%"],
                    ["", "", ""],
                    [f"{results['detectable_difference']['Power 60%']:.6f}", "", f"{results['detectable_difference']['Power 60%']:.6f}"],
                    ["Sample size", "Observed difference", ""],
                    [f"{results['data1_stats']['sample_size']}", f"{results['mean_difference']:.6f}", f"{observed_difference_interval}"]
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

            # Set the color of the bottom right cell to see text properly
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
            ax = axs["Detectable"]
            ax.axis('off')
            
            # Create table data
            # Create table data from power analysis results
            if power is not None:
                # If power was provided, show required sample sizes
                ax.set_title(f"What sample size is required to detect a difference\nof {power}?", loc='center', pad=-70, y=1.02, fontsize=font_size)
                power_column = ["60%", "70%", "80%", "90%"]
                sample_sizes = [f"{results['required_sample_sizes'][f'Power {p}']:.0f}" for p in power_column]
                table_data = list(zip(power_column, sample_sizes))
                colLabels_difference = ["Power", "Sample Size"]
            else:
                # Otherwise show detectable differences
                ax.set_title("Detectable difference with sample sizes of N", loc='center', pad=-70, y=1.02, fontsize=font_size)
                power_column = ["60%", "70%", "80%", "90%"]
                differences = [f"{results['detectable_difference'][f'Power {p}']:.6f}" for p in power_column]
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
            figsize=(8.27, 11.69), dpi=300)  # A4 size in inches
            #fig.subplots_adjust(hspace=0.4)  # Increase hspace to add more space between charts
            # fig.suptitle(title, fontsize=16, weight='bold', y=0.94)
            fig.subplots_adjust(hspace=0.4)

            header_ax = add_header_or_footer_to_a4_portrait(fig, header_image_path, position='header')
            footer_ax = add_header_or_footer_to_a4_portrait(fig, footer_image_path, position='footer', page_number=2, total_pages=2, projectNumber=projectNumber)

            # Histogram
            ax = axes["Hist"]
            # Calculate the difference between datapoints, then plot them in a histogram
            ax.hist(df_combined["Difference"], bins=7, color='#95b92a', edgecolor='black', zorder=1)
            ax.set_title("Histogram of Differences", loc='center', y=1.02)
            ax.set_xlabel("Differences")
            ax.set_ylabel("Frequency")
            ax.plot(0, -0.3, color="red", marker="*", label=r"$H_{0}$")
            ax.errorbar(results['mean_difference'], -0.5, xerr=[[results['mean_difference'] - results['mean_difference_interval'][0]], [results['mean_difference_interval'][1] - results['mean_difference']]], fmt='|', capsize=5, color='lightblue', label=r"$\overline{x}$")
            ax.set_ylim(bottom=-1 * axes["Boxplot"].get_ylim()[1])
            ax.set_axisbelow(True)
            ax.grid(True, alpha=0.3, zorder=0)

            legend = ax.legend()
            for text in legend.get_texts():
                text.set_fontsize('x-small')
            # Remove the horizontal line through the target_mu marker
            for line in legend.get_lines():
                line.set_linewidth(0)




            # Boxplot of the difference
            ax = axes["Boxplot"]
            sns.boxplot(x=df_combined["Difference"], ax=ax, color='#a1d111', linecolor='black', showcaps=False, linewidth=1, width=0.3)
            ax.plot(0, -0.45, color="red", marker="*", label=r"$H_{0}$")
            ax.errorbar(results['mean_difference'], -0.5, xerr=[[results['mean_difference'] - results['mean_difference_interval'][0]], [results['mean_difference_interval'][1] - results['mean_difference']]], fmt='|', capsize=5, color='lightblue', label=r"$\overline{x}$")
            ax.set_title("Boxplot of the differences", loc='center', y=1.02)
            ax.set_xlabel("Differences")
            ax.set_ylim(-0.6, 0.6)
            ax.grid(True, alpha=0.3)
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

def _calculate_paired_statistics(data1, data2, p, alpha=0.05):
    """
    Calculate statistics for paired data samples, including a paired t-test.
    
    Parameters:
    - data1: First data sample (pandas Series or DataFrame column)
    - data2: Second data sample (pandas Series or DataFrame column), paired with data1
    - p: Expected difference to detect (for power analysis)
    - alpha: Significance level (default: 0.05)
    
    Returns:
    - Dictionary containing comprehensive statistical results
    """
    
    # Calculate differences between paired observations
    differences = data1.iloc[:, 0] - data2.iloc[:, 0]  # Extract and subtract the first column values
    
    # Calculate descriptive statistics for individual samples
    confidence_level = 1 - alpha
    
    std_err_1 = data1.std(ddof=1) / np.sqrt(len(data1))
    deg_f_1 = len(data1) - 1
    stats1 = {
        'sample_size': len(data1),
        'mean': data1.mean(),
        'median': data1.median(),
        'std_dev': data1.std(ddof=1),
        'std_err': std_err_1,
        'range': data1.max()-data1.min(),
        'confidence_interval': stats.t.interval(confidence_level, deg_f_1, loc=data1.mean(), scale=std_err_1)
    }

    std_err_2 = data2.std(ddof=1) / np.sqrt(len(data2))
    deg_f_2 = len(data2) - 1
    stats2 = {
        'sample_size': len(data2),
        'mean': data2.mean(),
        'median': data2.median(),
        'std_dev': data2.std(ddof=1),
        'std_err': std_err_2,
        'range': data2.max()-data2.min(),
        'confidence_interval': stats.t.interval(confidence_level, deg_f_2, loc=data2.mean(), scale=std_err_2)
    }
    
    # Descriptive statistics for the differences
    std_err_diff = differences.std(ddof=1) / np.sqrt(len(differences))
    deg_f_diff = len(differences) - 1
    diff_stats = {
        'sample_size': len(differences),
        'mean': differences.mean(),
        'median': differences.median(),
        'std_dev': differences.std(ddof=1),
        'std_err': std_err_diff,
        'range': differences.max() - differences.min(),
        'confidence_interval': stats.t.interval(confidence_level, deg_f_diff, loc=differences.mean(), scale=std_err_diff)
    }
    
    # Perform paired t-test
    t_statistic, p_value = stats.ttest_rel(data1, data2)
    degrees_of_freedom = len(differences) - 1
    
    # Mean difference and confidence interval
    mean_difference = stats1['mean'].iloc[0] - stats2['mean'].iloc[0]
    mean_difference_ci = stats.t.interval(
        confidence_level,
        df=degrees_of_freedom,
        loc=mean_difference,
        scale=std_err_diff
    )
    
    # Calculate detectable difference for each power level
    power_levels = [0.6, 0.7, 0.8, 0.9]
    detectable_differences = {}
    for power in power_levels:
        effect_size = stats.norm.ppf(1 - alpha / 2) + stats.norm.ppf(power)
        # We use the standard deviation of differences for paired tests
        std_diff = differences.std(ddof=1)
        detectable_difference = effect_size * std_diff / np.sqrt(len(differences))
        detectable_differences[f'Power {int(power * 100)}%'] = detectable_difference
    
    # Calculate required sample size to detect difference p at each power level
    required_sample_sizes = {}
    power_analysis = {"Detection Chance": None, "Sample Size": len(differences)}
    
    if p is not None:
        # Calculate the chance of detecting the difference p with current sample size
        std_diff = differences.std(ddof=1)
        effect_size = abs(p) / std_diff
        
        # For paired t-test, we use TTestPower instead of TTestIndPower
        detection_power = TTestPower().solve_power(
            effect_size=effect_size,
            nobs=len(differences),
            alpha=alpha,
            power=None,
            alternative='two-sided'
        )
        power_analysis["Detection Chance"] = round(detection_power * 100)
        
        # Calculate required sample sizes for different power levels
        for power in power_levels:
            sample_size = TTestPower().solve_power(
                effect_size=effect_size,
                nobs=None,
                alpha=alpha,
                power=power,
                alternative='two-sided'
            )
            required_sample_sizes[f'Power {int(power * 100)}%'] = int(np.ceil(sample_size))
    
    # Combine results
    results = {
        'data1_stats': stats1,
        'data2_stats': stats2,
        'difference_stats': diff_stats,
        't_statistic': t_statistic,
        'p_value': p_value,
        'degrees_of_freedom': degrees_of_freedom,
        'mean_difference': mean_difference,
        'mean_difference_interval': mean_difference_ci,
        'detectable_difference': detectable_differences,
        'required_sample_sizes': required_sample_sizes,
        'power_analysis': power_analysis
    }
    
    return results