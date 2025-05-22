import io
import pandas as pd
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from matplotlib.backends.backend_pdf import PdfPages
from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Optional, Union, Any
from api.schemas import BusinessLogicException
import seaborn as sns
from statsmodels.stats.power import TTestIndPower

from ...utils.pdf_utils import add_header_or_footer_to_a4_portrait

header_image_path = 'assets/img/Header.png'
footer_image_path = 'assets/img/Footer.png'

from ...utils.mpl_table_utils import merge_mpl_table_cells as mergecells

# check data format
class TwoTtestConfig(BaseModel):
    title: str
    alphalevel: float
    power: Optional[float] = Field(None, gt=0, le=1)    # Optional field with a value between 0 and 1


# class TwoTtestData(BaseModel):
#     values: Dict[str, List[float]] = Field(..., min_length=1)

class TwoTtestDataSeparate(BaseModel):
    values: Dict[str, List[float]]
    
    @field_validator('values')
    def check_exactly_two_series(cls, v):
        if len(v) != 2:
            raise BusinessLogicException(
                error_code="error_validation",
                field="values",
                details={"message": "Exactly two data series are required"}
            )

        return v

# Alternative data format with values in a single column
class TwoTtestDataCombined(BaseModel):
    values: List[float]
    groups: List[str]
    
    @field_validator('groups')
    def check_exactly_two_groups(cls, v, values):
        unique_groups = set(v)
        if len(unique_groups) != 2:
            raise BusinessLogicException(
                error_code="error_validation",
                field="groups",
                details={"message": "Exactly two different group identifiers are required"}
            )
        
        # Check if we have the data values too
        if 'values' in values and len(values['values']) != len(v):
            raise BusinessLogicException(
                error_code="error_data_length_mismatch",
                field="values",
                details={"message": "Data lengths do not match the expected number inputs"}
            )
            
        # Count samples per group
        group_counts = {}
        for group in v:
            group_counts[group] = group_counts.get(group, 0) + 1
        
        return v

# Union type to accept either format
TwoTtestData = Union[TwoTtestDataSeparate, TwoTtestDataCombined]

class TwoTtestRequest(BaseModel):
    project: str
    step: str
    config: TwoTtestConfig
    data: Any  # Use Any type to handle both formats
    
    @field_validator('data')
    def validate_data_format(cls, v):
        # Check if the data is in separate format
        if 'values' in v and isinstance(v['values'], dict):
            try:
                return TwoTtestDataSeparate(**v)
            except Exception as e:
                raise ValueError(f"Invalid separate data format: {str(e)}")
        
        # Check if the data is in combined format
        elif 'values' in v and isinstance(v['values'], list) and 'groups' in v:
            try:
                return TwoTtestDataCombined(**v)
            except Exception as e:
                raise ValueError(f"Invalid combined data format: {str(e)}")
        
        # If neither format matches
        else:
            raise ValueError("Data must be either in separate format (dictionary of lists) or combined format (list of values with group identifiers)")

class TwoTtest:
    """
    A class to perform a two-sample t-test and generate a PDF report with the results.
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
    def __init__(self, data:dict):
        try:
            # Try to validate with either data format
            if 'values' in data['data'] and isinstance(data['data']['values'], dict):
                # Separate format - multiple columns
                validated_data = TwoTtestRequest(**data)
                self.project = validated_data.project
                self.step = validated_data.step
                self.config = validated_data.config
                self.data = validated_data.data
            elif 'values' in data['data'] and isinstance(data['data']['values'], list) and 'groups' in data['data']:
                # Combined format - need to convert
                self.project = data['project']
                self.step = data['step']
                self.config = TwoTtestConfig(**data['config'])
                
                # Store original data format temporarily
                combined_data = {
                    'values': data['data']['values'],
                    'groups': data['data']['groups']
                }
                
                # Convert to separate format
                separate_data = self._convert_combined_to_separate(combined_data)
                
                # Replace with converted data
                self.data = TwoTtestDataSeparate(values=separate_data)
            else:
                raise ValueError("Unrecognized data format")
                
        except Exception as e:
            raise BusinessLogicException(
                error_code="error_validation",
                field=str(e),
                details={"message": f"Invalid or missing field: {str(e)}"}
            )

    def process(self):
        title = self.config.title
        alpha = self.config.alphalevel
        power = self.config.power
        source_1 = list(self.data.values.keys())[0]
        source_2 = list(self.data.values.keys())[1]
        # Create two dataframes for each dataset
        data_keys = list(self.data.values.keys())
        df1 = pd.DataFrame(self.data.values[data_keys[0]], columns=[data_keys[0]])
        df2 = pd.DataFrame(self.data.values[data_keys[1]], columns=[data_keys[1]])
        df_combined = pd.concat([df1, df2], axis=1)
        confidence_percent = int((1 - alpha) * 100)

        results = _calculate_statistics(df1, df2, power, alpha)

        # Hypothesis test result
        if results['p_value'] > alpha:
            difference_string = f"The mean value from ”{source_1}” is not significantly\ndifferent from the mean value of ”{source_2}”"
            difference_color = "#d6ed5f"
        else:
            difference_string = f"The mean value from ”{source_1}” is  significantly\ndifferent from the mean value of ”{source_2}”"
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

        # Create a PDF report
        pdf_io = io.BytesIO()

        with PdfPages(pdf_io) as pdf:
            # NEW PDF PAGE - T-Test results, Descriptive Statistics, Data Time Series, Chance and Detectable Difference
            fig, axs = plt.subplot_mosaic([
                ["T-Test Results", "T-Test Results"],
                ["Descriptive Statistics", "Descriptive Statistics"],
                ["TS1", "TS2"],         # Time Series Plots for each dataset
                ["Chance", "Detectable"]],    # Chance and Detectable Difference
                figsize=(8.27, 11.69), dpi=300)  # A4 size in inches
            # fig.subplots_adjust(hspace=0.4)  # Increase hspace to add more space between charts
            fig.suptitle(title, fontsize=14, y=0.92, ha='left', x=0.1)		

            add_header_or_footer_to_a4_portrait(fig, header_image_path, position='header')
            add_header_or_footer_to_a4_portrait(fig, footer_image_path, position='footer', page_number=1, total_pages=2)

            # Define the colors + font size
            edgecolor = "#7c7c7c"
            grey = "#e7e6e6"
            green_table = "#9cc563"
            lightgreen_table = "#d6ed5f"
            font_size=7
            edge_color="#7c7c7c"

            # T-Test Results Table
            ax = axs["T-Test Results"]
            ax.axis('off')

            # Define table data
            table_data = [
                ["Configuration", "", "Hypothesis", "", "", ""],
                ["Each sample in its own column", "", r"$\mathrm{H_{0}: \mu_{1} = \mu_{2}}$", "t-Value", "df", "p-Value*"],
                ["Sample 1", f"{source_1}", r"$\mathrm{H_{1}: \mu_{1} \neq \mu_{2}}$", f"{results['t_statistic'][0].round(2)}", f"{results['degrees_of_freedom']}", f"{results['p_value'][0]:.3f}"],
                ["Sample 2", f"{source_2}", "", "", "", ""],
                ["Test-Setup", "Different", "", "", "", f"{results['observed_difference']:.6f}"],
                ["Alpha-Level", f"{alpha}", "empty", "", "", f"({results['observed_difference_interval'][0][0]:.4f}; {results['observed_difference_interval'][1][0]:.4f})"],
                ["Interested\ndifference**", f"{power if power is not None else '-'}", "empty", f"{difference_string}", "", ""],
                ["", "", "", "", "", ""]
            ]
            # Set the column widths as needed
            col_widths = [0.15, 0.15, 0.15, 0.15, 0.15, 0.15]

            # Background color for the table
            bg_colors = [
                ["#e7e6e6", "#e7e6e6", "#e7e6e6", "#e7e6e6", "#e7e6e6", "#e7e6e6"],
                ["#ffffff", "#ffffff", "#d6ed5f", "#ffffff", "#ffffff", "#ffffff"],
                ["#ffffff", "#ffffff", "#9cc563", "#ffffff", "#ffffff", difference_color],
                ["#ffffff", "#ffffff", "#ffffff", "#e7e6e6", "#e7e6e6", "#e7e6e6"],
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
                cell.set_edgecolor("#7c7c7c")
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
            table_1_widths = [0.18, 0.06, 0.11, 0.11, 0.11, 0.11, 0.21, 0.11]
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
                cell.set_edgecolor(edge_color)
                cell.set_linewidth(0.5)

            # Set the top row color to grey
            for col in range(len(descriptive_statistics.columns)):
                cell = table_1[(0, col)]
                cell.set_facecolor(grey)

            # Data Time series plot first dataset
            ax = axs["TS1"]
            ax.plot(df1, color='black', marker='o', linewidth=0.5)
            ax.set_title("Data Time Series", loc='left')
            ax.hlines(results['data1_stats']['mean'].iloc[0], 0, results['data1_stats']['sample_size'], colors='grey', linestyles='dashed', alpha=0.7, lw=0.5)
            ax.text(0.2, 0.1, source_1, transform=ax.transAxes, fontsize=7, verticalalignment='top', horizontalalignment='center')

            # Mark outliers of TS1 data
            Q1_TS1 = df1.quantile(0.25)
            Q3_TS1 = df1.quantile(0.75)
            IQR_TS1 = Q3_TS1 - Q1_TS1
            lower_bound_TS1 = Q1_TS1 - 1.5 * IQR_TS1
            upper_bound_TS1 = Q3_TS1 + 1.5 * IQR_TS1

            for i, value in enumerate(df1.values):
                if value < lower_bound_TS1.values or value > upper_bound_TS1.values:
                    ax.plot(i, value, color='red', marker='s')

            # Data Time series plot second dataset
            ax = axs["TS2"]
            ax.plot(df2, color='black', marker='o', linewidth=0.5)
            ax.hlines(results['data2_stats']['mean'].iloc[0], 0, results['data2_stats']['sample_size'], colors='grey', linestyles='dashed', alpha=0.7, lw=0.5)
            ax.set_yticks([])
            ax.text(0.2 , 0.1, source_2, transform=ax.transAxes, fontsize=7, verticalalignment='top', horizontalalignment='center')

            # Mark outliers of TS2 data
            Q1_TS2 = df2.quantile(0.25)
            Q3_TS2 = df2.quantile(0.75)
            IQR_TS2 = Q3_TS2 - Q1_TS2
            lower_bound_TS2 = Q1_TS2 - 1.5 * IQR_TS2
            upper_bound_TS2 = Q3_TS2 + 1.5 * IQR_TS2

            for i, value in enumerate(df2.values):
                if value < lower_bound_TS2.values or value > upper_bound_TS2.values:
                    ax.plot(i, value, color='red', marker='s')

            # Set y-limits for both plots
            max_y = max(df1.max().values[0], df2.max().values[0])
            min_y = min(df1.min().values[0], df2.min().values[0])
            y_margin = 0.20 * (max_y - min_y)
            axs["TS1"].set_ylim(min_y - y_margin, max_y + y_margin)
            axs["TS2"].set_ylim(min_y - y_margin, max_y + y_margin)


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
                if results['observed_difference'] < results['detectable_difference']['Power 60%']:
                    observed_difference_interval = "<60%"
                    observed_difference_color = "#c00000"
                    observed_difference_text_color = "#ffffff"
                elif results['detectable_difference']['Power 60%'] <= results['observed_difference'] < results['detectable_difference']['Power 70%']:
                    observed_difference_interval = "60%-70%"
                    observed_difference_color = "#f9b002"
                    observed_difference_text_color = "#000000"
                elif results['detectable_difference']['Power 70%'] <= results['observed_difference'] < results['detectable_difference']['Power 80%']:
                    observed_difference_interval = "70%-80%"
                    observed_difference_color = "#f9b002"
                    observed_difference_text_color = "#000000"
                elif results['detectable_difference']['Power 80%'] <= results['observed_difference'] < results['detectable_difference']['Power 90%']:
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
                    [f"{results['detectable_difference']['Power 60%']:.6f}", "", f"{results['detectable_difference']['Power 60%']:.6f}"],
                    ["Sample size", "Observed difference", ""],
                    [f"{results['data1_stats']['sample_size']}", f"{results['observed_difference']:.6f}", f"{observed_difference_interval}"]
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
            ax = axs["Detectable"]
            ax.axis('off')
            
            # Create table data
            # Create table data from power analysis results
            if power is not None:
                # If power was provided, show required sample sizes
                ax.set_title(f"What sample size is required to detect a difference\nof {power}?", loc='center', pad=-70, y=1.02, fontsize=font_size)
                power_column = ["60%", "70%", "80%", "90%"]
                sample_sizes = [
                    f"{results['required_sample_sizes'][f'Power {p}']:.0f}" if isinstance(results['required_sample_sizes'][f'Power {p}'], (int, float))
                    else results['required_sample_sizes'][f'Power {p}']
                    for p in power_column
                ]
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
                cell.set_edgecolor(edge_color)
                cell.set_linewidth(0.5)

            # Set the top row color to grey
            for cell in table._cells:
                if cell[0] == 0:
                    table._cells[cell].set_facecolor(grey)

            pdf.savefig(fig)
            plt.close(fig)

            # NEW PDF PAGE - Histograms and Boxplots
            fig, axs = plt.subplot_mosaic([
                ["Hist1", "Hist2"],
                ["Boxplot", "Boxplot"]],
                figsize=(8.27, 11.69), dpi=300)  # A4 size in inches
            #fig.subplots_adjust(hspace=0.4)  # Increase hspace to add more space between charts
            # fig.suptitle(title, fontsize=16, weight='bold', y=0.94)

            add_header_or_footer_to_a4_portrait(fig, header_image_path, position='header')
            add_header_or_footer_to_a4_portrait(fig, footer_image_path, position='footer', page_number=2, total_pages=2)

            # Define gaussian function for fits
            def gaussian(x, a, mu, sigma):
                return a * np.exp(-(x-mu)**2 / (2*sigma**2))
            
            # Histogram of first dataset
            ax = axs["Hist1"]
            counts_1, bins_1, _ = ax.hist(df1.values, color='#95b92a', edgecolor='black', zorder=2)
            ax.set_title(f"Histogram of {source_1}")
            ax.set_ylabel("Frequency")
            ax.grid(True, alpha=0.3, zorder=0)            

            # Calculate the bin centers
            bin_center_1 = (bins_1[:-1] + np.diff(bins_1) / 2)

            x_values_to_fit_1 = np.linspace(bins_1[0], bins_1[-1], 1000)
            param_1, _ = curve_fit(gaussian, bin_center_1, counts_1, p0=(10, 10, 10))
            ax.plot(x_values_to_fit_1, gaussian(x_values_to_fit_1, *param_1), color='#a03130', lw=1, zorder=5)


            # Histogram of second dataset
            ax = axs["Hist2"]
            counts_2, bins_2, _ = ax.hist(df2.values, color='#95b92a', edgecolor='black', zorder=2)
            ax.set_title(f"Histogram of {source_2}")
            ax.grid(True, alpha=0.3, zorder=0)

            # Calculate the bin centers
            bin_center_2 = (bins_2[:-1] + np.diff(bins_2) / 2)

            x_values_to_fit_2 = np.linspace(bins_2[0], bins_2[-1], 1000)
            param_2, _ = curve_fit(gaussian, bin_center_2, counts_2, p0=(10, 10, 10))
            ax.plot(x_values_to_fit_2, gaussian(x_values_to_fit_2, *param_2), color='#a03130', lw=1, zorder=5)

            # Boxplot of both datasets
            ax = axs["Boxplot"]
            sns.boxplot(data=df_combined.values, ax=ax, palette=['#a1d111', '#a1d111'], linecolor='black', showcaps=False, linewidth=0.3, width=0.3, flierprops={"marker": "x"})
            ax.set_title(f"Boxplots of {source_1} and {source_2}")
            ax.set_xticks([0, 1])
            ax.set_xticklabels([f"{source_1}", f"{source_2}"])
            ax.set_ylabel("Data")

            # Add the means to the boxplot and draw a line between them
            ax.plot([0, 1], [results['data1_stats']['mean'].iloc[0], results['data2_stats']['mean'].iloc[0]], color='black', lw=0.5, marker='+', label='Mean')
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
    
def _convert_combined_to_separate(self, combined_data):
        """
        Convert data from combined format (single column with group identifiers)
        to separate format (dictionary with group names as keys).
        
        Args:
            combined_data: Dictionary with 'values' (list) and 'groups' (list) keys
            
        Returns:
            Dictionary with group names as keys and lists of values as values
        """
        values = combined_data['values']
        groups = combined_data['groups']
        
        # Create dictionary of separate data series
        separate_data = {}
        unique_groups = set(groups)
        
        for group in unique_groups:
            # Extract values for this group
            group_values = [values[i] for i in range(len(values)) if groups[i] == group]
            separate_data[group] = group_values
        
        return separate_data


def _calculate_statistics(data1, data2, p, alpha=0.05):
    # Calculate descriptive statistics
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

    std_err_2 = data2.std(ddof=1) / np.sqrt(len(data1))
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

    # Perform 2-sample t-test
    t_statistic, p_value = stats.ttest_ind(data1, data2, equal_var=False)
    degrees_of_freedom = len(data1) + len(data2) - 2

    # Calculate observed difference of means
    observed_difference = np.mean(data1) - np.mean(data2)

    observed_difference_ci = stats.t.interval(
        1-alpha,
        df=len(data1) + len(data2) - 2,
        loc=observed_difference,
        scale=np.sqrt(stats.sem(data1, axis=0)**2 + stats.sem(data2, axis=0)**2)
    )

    # Calculate detectable difference for each power level
    power_levels = [0.6, 0.7, 0.8, 0.9]
    detectable_differences = {}
    for power in power_levels:
        effect_size = stats.norm.ppf(1 - alpha / 2) + stats.norm.ppf(power)
        # Extract numpy arrays from pandas DataFrames
        data1_values = data1.values.flatten()
        data2_values = data2.values.flatten()
        pooled_std = np.sqrt((data1_values.std(ddof=1) ** 2 + data2_values.std(ddof=1) ** 2) / 2)
        detectable_difference = effect_size * pooled_std * np.sqrt(2 / len(data1_values))
        detectable_differences[f'Power {int(power * 100)}%'] = detectable_difference

    # Calculate required sample size to detect difference p at each power level
    required_sample_sizes = {}
    power_analysis = {"Detection Chance": None, "Sample Size": len(data1)}
    
    if p is not None:
        # Calculate the chance of detecting the difference p with current sample size
        # Extract numpy arrays from pandas DataFrames
        data1_values = data1.values.flatten()
        data2_values = data2.values.flatten()
        # pooled_std = np.sqrt((data1_values.std(ddof=1) ** 2 + data2_values.std(ddof=1) ** 2) / 2)
        pooled_std = np.sqrt((data1.values.flatten().std(ddof=1) ** 2 + data2.values.flatten().std(ddof=1) ** 2) / 2)
        effect_size_observed = abs(np.mean(data1) - np.mean(data2)) / pooled_std
        
        # Calculate the power (chance of detection) for the given difference p
        try:
            detection_power = TTestIndPower().solve_power(
                effect_size=effect_size,
                nobs1=len(data1),
                alpha=alpha,
                power=None,
                ratio=1,
                alternative='two-sided'
            )
            power_analysis["Detection Chance"] = round(detection_power * 100)
        except Exception as e:
            # Handle the case where power calculation fails
            import warnings
            warnings.warn(f"Power calculation failed: {str(e)}. Setting detection chance to >99%.")
            power_analysis["Detection Chance"] = 99  # Set to a high value since p-value is much smaller than alpha
        
        # Calculate required sample sizes for different power levels
        required_sample_sizes = calculate_sample_size(
            effect_size=abs(p),
            std_dev1=data1.std(ddof=1).iloc[0],
            std_dev2=data2.std(ddof=1).iloc[0],
            alpha=alpha,
            power_levels=power_levels
        )


    # Combine results
    results = {
        'data1_stats': stats1,
        'data2_stats': stats2,
        't_statistic': t_statistic,
        'p_value': p_value,
        'degrees_of_freedom': degrees_of_freedom,
        'observed_difference': observed_difference,
        'observed_difference_interval': observed_difference_ci,
        'detectable_difference': detectable_differences,
        'required_sample_sizes': required_sample_sizes,
        'power_analysis': power_analysis
    }

    return results

def calculate_sample_size(effect_size, std_dev1, std_dev2, alpha=0.05, power_levels=[0.6, 0.7, 0.8, 0.9]):
    """
    Calculate the required sample size for a two-sample t-test.
    
    Parameters:
        effect_size (float): The minimum detectable difference between the two groups.
        std_dev1 (float): Standard deviation of group 1.
        std_dev2 (float): Standard deviation of group 2.
        alpha (float): Significance level (default is 0.05 for a two-tailed test).
        power_levels (list): List of desired power levels (default is [0.6, 0.7, 0.8, 0.9]).

    Returns:
        dict: A dictionary where keys are power levels and values are required sample sizes per group.
    """
    # Critical value for the significance level
    z_alpha = stats.norm.ppf(1 - alpha / 2)

    # Pre-compute sum of variances
    variance_sum = std_dev1**2 + std_dev2**2

    # Dictionary to store results
    sample_sizes = {}

    for power in power_levels:
        # Critical value for the desired power
        z_beta = stats.norm.ppf(power)
        
        # Sample size formula
        n = (variance_sum * (z_alpha + z_beta)**2) / effect_size**2
        sample_sizes[f'Power {int(power * 100)}%'] = int(round(n))  # Round to nearest integer
    
    return sample_sizes