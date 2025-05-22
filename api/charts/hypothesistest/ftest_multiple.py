import io
import numpy as np
import pandas as pd
import scipy.stats as stats
import matplotlib.pyplot as plt
from pydantic import BaseModel, Field, field_validator, conlist
from matplotlib.backends.backend_pdf import PdfPages
from typing import Dict, List, Union
from api.schemas import BusinessLogicException

from ...utils.pdf_utils import add_header_or_footer_to_a4_portrait

header_image_path = 'assets/img/Header.png'
footer_image_path = 'assets/img/Footer.png'

from ...utils.mpl_table_utils import merge_mpl_table_cells as mergecells

class FtestMultipleConfig(BaseModel):
    title: str
    alphalevel: float

class FtestMultipleDataSeparate(BaseModel):
    """
    e.g.:
    {
      "values": {
        "Dataset1": [0.9, 1.0, 1.1],
        "Dataset2": [1.2, 1.3, 1.4],
        "Dataset3": [0.7, 1.5, 1.4]
      }
    }
    Accepts between 3 and 6 separate datasets.
    """
    values: Dict[str, conlist(float, min_length=1)] = Field(..., min_length=3) # type: ignore

    @field_validator('values')
    def check_datasets_count_and_finite(cls, v):
        # Ensure 3 to 6 datasets
        if not 3 <= len(v) <= 6:
            raise BusinessLogicException(
                error_code="error_datasets_number",
                field="datasets",
                details={"message": "Number of datasets must be between 3 and 6"}
            )
        # Check for NaN or infinite values
        for name, data_list in v.items():
            if any(not np.isfinite(x) for x in data_list):
                raise ValueError(f"Dataset '{name}' contains NaN or infinite values")
        return v

class FtestMultipleDataCombined(BaseModel):
    """
    e.g.:
    {
      "values": [0.9, 1.0, 1.1, 1.3, 1.4, 0.8, ...],
      "groups": ["A", "A", "A", "B", "B", "C", ...]
    }
    Accepts between 3 and 6 distinct group labels.
    """
    values: conlist(float, min_length=1) # type: ignore
    groups: conlist(str, min_length=1) # type: ignore

    @field_validator('groups')
    def check_same_length(cls, groups, info):
        # Get the values field from the data being validated
        values_data = info.data.get('values', [])
        if len(groups) != len(values_data):
            raise BusinessLogicException(
                error_code="error_column_length",
                field="values",
                details={"message": "Values and groups must have the same length"}
            )
        return groups

    @field_validator('groups')
    def check_group_count(cls, groups):
        distinct_groups = set(groups)
        if not 3 <= len(distinct_groups) <= 6:
            raise BusinessLogicException(
                error_code="error_group_number",
                field="groups",
                details={"message": "Number of groups must be between 3 and 6"}
            )
        return groups

    @field_validator('values')
    def check_finite_values(cls, values):
        if any(not np.isfinite(x) for x in values):
            raise ValueError("Values contain NaN or infinite values.")
        return values

FtestMultipleDataUnion = Union[FtestMultipleDataSeparate, FtestMultipleDataCombined]

class FtestMultipleRequest(BaseModel):
    project: str
    step: str
    config: FtestMultipleConfig
    data: FtestMultipleDataUnion

class FtestMultiple:

    def __init__(self, data: Dict):
        try:
            validated_data = FtestMultipleRequest(**data)
            self.project = validated_data.project
            self.step = validated_data.step
            self.config = validated_data.config
            self.data = validated_data.data

            # Check if data is in combined format and convert if needed
            if isinstance(validated_data.data, FtestMultipleDataCombined):
                self.data = self._convert_combined_to_separate(validated_data.data)
            else:
                self.data = validated_data.data

             # Check the number of datasets
            num_datasets = len(self.data.values)
            if num_datasets < 2 or num_datasets > 6:
                raise BusinessLogicException(
                    error_code="error_datasets_number",
                    field="values",
                    details={"message": "Number of datasets must be between 3 and 6"}
                )
            
        except Exception as e:
            raise BusinessLogicException(
                error_code="error_validation",
                field=str(e),
                details={"message": f"Invalid or missing field: {str(e)}"}
            )
        
    def process(self):
        title = self.config.title
        alpha = self.config.alphalevel
        keys = list(self.data.values.keys())
        datasets = list(self.data.values.values())
        dataframes = {key: pd.DataFrame({key: dataset}) for key, dataset in zip(keys, datasets)}

        pdf_io = io.BytesIO()

        with PdfPages(pdf_io) as pdf:
            # NEW PDF PAGE - T-Test results, Descriptive Statistics, Data Time Series, Chance and Detectable Difference
            fig, axs = plt.subplot_mosaic([
                ["Ftest Results", "Ftest Results"],
                ["Descriptive Statistics", "Descriptive Statistics"],
                ["StDev Comparison", "StDev Differ"]],    # Chance and Detectable Difference
                figsize=(8.27, 11.69), dpi=300)  # A4 size in inches
            # fig.subplots_adjust(hspace=0.4)  # Increase hspace to add more space between charts
            fig.suptitle(title, fontsize=14, y=0.92, ha='left', x=0.1)

            add_header_or_footer_to_a4_portrait(fig, header_image_path, position='header')
            add_header_or_footer_to_a4_portrait(fig, footer_image_path, position='footer', page_number=1, total_pages=3)


            # Define the colors + font size
            edgecolor = "#7c7c7c"
            grey = "#e7e6e6"
            green_table = "#9cc563"
            lightgreen_table = "#d6ed5f"
            font_size=7

            # F-Test Results
            ax = axs["Ftest Results"]
            ax.axis('off')

            # Samples
            keys_string = "\n".join(keys)

            # Define table data
            cellText = [
                ["Configuration", "", "Hypothesis", "Results", ],
                ["Each sample in its own column", "", r"$H_{0}:$ all $\sigma_{i}$ = $\sigma_{j}$", ""],
                ["Samples", f"{keys_string}", r"$H_{1}:$ one $\sigma_{i}$ $\neq$ $\sigma_{j}$", "",],
                ["", "", "", ""],
                ["Test-Setup", "Different", "", ""],
                [r"$\alpha$-Level", f"{alpha}", "", ""],
                ["", "", "", "Platzhalter difference string"]
            ]
            # Set the column widths as needed
            col_widths = [0.15, 0.15, 0.15, 0.45]

            # Background colors for the table
            bg_colors = [
                [grey, grey, grey, grey],
                ["#ffffff", "#ffffff", lightgreen_table, "#ffffff"],
                ["#ffffff", "#ffffff", green_table, "#ffffff"],
                ["#ffffff", "#ffffff", "#ffffff", "#ffffff"],
                ["#ffffff", "#ffffff", "#ffffff", "#ffffff"],
                ["#ffffff", "#ffffff", "#ffffff", "#ffffff"],
                ["#ffffff", "#ffffff", "#ffffff", green_table]
            ]

             # Create table with background colors only and remove edgecolor
            table_bg = ax.table(
                bbox=[0, 0, 1, 1],
                cellColours=bg_colors,
                colWidths=col_widths
            )
            for cell in table_bg._cells.values():
                cell.set_edgecolor("none")

            # Recreate the table layout with "none" as the color
            bg_none = [
                ["none" for _ in row] for row in cellText
            ]

            # Create the table with the data + "none" as the color
            table = ax.table(
                bbox=[0, 0, 1, 1],
                cellText=cellText,
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
            mergecells(table, [(1, 0), (1, 1)])
            mergecells(table, [(2, 0), (3, 0)])
            mergecells(table, [(2, 1), (3, 1)])
            mergecells(table, [(3, 2), (4, 2), (5, 2)])
            mergecells(table, [(6, 0), (6, 1), (6, 2)])
            mergecells(table, [(1, 3), (2, 3), (3, 3), (4, 3), (5, 3)])

            # Adjust text placement + bold the text
            bold_text = [(4, 1)]
            for row, col in bold_text:
                cell = table.get_celld()[(row, col)]
                cell.set_text_props(weight='bold')

            text_left = [(1, 0)]
            for row, col in text_left:
                cell = table.get_celld()[(row, col)]
                cell.set_text_props(ha='left')

            top_text = [(2, 1)]
            for row, col in top_text:
                cell = table.get_celld()[(row, col)]
                cell.set_text_props(va='top')
                cell.set_fontsize(5)


            # Descriptive Statistics table
            ax = axs["Descriptive Statistics"]
            ax.axis('off')

            n_samples = len(keys)
            y = 1.02 if n_samples <= 3 else 1.05 if n_samples == 4 else 1.08 if n_samples == 5 else 1.11

            ax.set_title("Descriptive Statistics", loc="left", pad=-50, y=y)

            stats_summary = {
                key: {
                    "Quelle": key,
                    "N": df[key].count(),
                    "Mean": df[key].mean().round(4),
                    "StDev": df[key].std().round(6),
                    "95% CI for $sigma$": f"({(df[key].std() * np.sqrt((df[key].count() - 1) / stats.chi2.ppf(0.975, df[key].count() - 1))).round(4)}; "
                                          f"{(df[key].std() * np.sqrt((df[key].count() - 1) / stats.chi2.ppf(0.025, df[key].count() - 1))).round(4)})"
                }
                for key, df in dataframes.items()
            }
            descriptive_table_widths = [0.18, 0.06, 0.11, 0.11, 0.19]
            cellText = [
                ["Quelle", "N", "Mean", "StDev", "95% CI for $\sigma$"],
                *[list(stats_summary[key].values()) for key in keys]
            ]
            # Dynamically adjust table height based on number of samples
            # Default bbox: [0, 0.4, 0.6, 0.3]
            if n_samples <= 3:
                bbox = [0, 0.4, 0.6, 0.3]
            elif n_samples == 4:
                bbox = [0, 0.35, 0.6, 0.38]
            elif n_samples == 5:
                bbox = [0, 0.3, 0.6, 0.46]
            else:  # 6 samples
                bbox = [0, 0.25, 0.6, 0.54]

            descriptive_table = ax.table(
                cellText=cellText,
                colWidths=descriptive_table_widths,
                cellLoc='center',
                loc='upper left',
                bbox=bbox
            )
            # Set the font size for the table
            descriptive_table.auto_set_font_size(False)
            descriptive_table.set_fontsize(font_size)

            # Change edgecolor of table
            for cell in descriptive_table._cells.values():
                cell.set_edgecolor(edgecolor)
                cell.set_linewidth(0.5)
            
            # Set the top row color to #e7e6e6
            for cell in descriptive_table._cells:
                if cell[0] == 0:
                    descriptive_table._cells[cell].set_facecolor(grey)


            # StDev Comparison
            ax = axs["StDev Comparison"]
            ax.set_title("Standard Deviations Comparison Chart", loc='center', fontsize=10)
            # Extract means and standard deviations
            std_devs = []
            std_devs_CI = []
            labels = []

            
            for key in keys:
                std_devs.append(stats_summary[key]["StDev"])
                # Extract CI values from the string format "(lower; upper)"
                ci_str = stats_summary[key]["95% CI for $sigma$"]
                lower_ci = float(ci_str.split('(')[1].split(';')[0])
                upper_ci = float(ci_str.split(';')[1].split(')')[0])
                std_devs_CI.append((lower_ci, upper_ci))
                labels.append(key)

            # Plot the standard deviations with error bars for CI
            y_pos = np.arange(len(labels))

            # Calculate proper error bar values
            xerr_left = [std - ci[0] for std, ci in zip(std_devs, std_devs_CI)]
            xerr_right = [ci[1] - std for std, ci in zip(std_devs, std_devs_CI)]
            
            # Plot with asymmetric error bars
            ax.errorbar(std_devs, y_pos, xerr=[xerr_left, xerr_right], fmt='o', markersize=3, 
                        capsize=0, linewidth=0.5, color='#95b92a')
            
            ax.set_yticks(y_pos)
            ax.set_yticklabels(labels, fontsize=font_size)
            ax.grid(True, alpha=0.3)
            ax.invert_yaxis()  # Labels read top-to-bottom
            ax.set_position([0.2, 0.1, 0.35, 0.25])

            # StDev Difference Chart
            ax = axs["StDev Differ"]
            ax.axis('off')
            ax.set_title("Which standard deviation differs?", loc='center', pad=-70, y=y, fontsize=10)

            # Create table data
            table_data = []
            for i, label in enumerate(labels):
                differs_from = []
                for j, _ in enumerate(labels):  # Changed to _ to indicate unused variable
                    if i != j:
                        # Check if confidence intervals overlap
                        ci_lower_i = std_devs_CI[i][0]  # CI already contains lower bound
                        ci_upper_i = std_devs_CI[i][1]  # CI already contains upper bound
                        ci_lower_j = std_devs_CI[j][0]
                        ci_upper_j = std_devs_CI[j][1]

                        if not (ci_lower_i <= ci_upper_j and ci_lower_j <= ci_upper_i):
                            differs_from.append(str(j+1)) # Using index numbers instead of labels

                table_data.append([i + 1, label, ", ".join(differs_from) if differs_from else "None"])

            differ_table = ax.table(
                cellText=table_data,
                colLabels=["#", "Sample", "Differs from"],
                cellLoc='center',
                loc='center',
                colWidths=[0.1, 0.6, 0.3]
            )

            # Format table
            differ_table.auto_set_font_size(False)
            differ_table.set_fontsize(font_size)
            for i in range(len(labels) + 1):  # +1 for header row
                for j in range(3):  # 3 columns
                    cell = differ_table._cells.get((i, j))
                    if cell:
                        cell.set_edgecolor(edgecolor)
                        cell.set_linewidth(0.5)
                        if i == 0:  # Header row
                            cell.set_facecolor(grey)
                            cell.set_text_props(weight='bold')

            ax.set_position([0.6, 0.1, 0.35, 0.25])

            pdf.savefig(fig)
            plt.close(fig)


            # NEW PDF PAGE - Data time series plots, Chance and Detectable Difference
            # Create dynamic layout based on number of datasets
            num_datasets = len(self.data.values)
            
            # Create layout for time series plots
            ts_layout = []
            
            # Calculate how to arrange the time series plots based on number of datasets
            if num_datasets == 3:
                ts_layout.append(["TS1", "TS1"])
                ts_layout.append(["TS2", "TS2"])
                ts_layout.append(["TS3", "TS3"])
            elif num_datasets == 4:
                ts_layout.append(["TS1", "TS2"])
                ts_layout.append(["TS3", "TS4"])
            elif num_datasets == 5 or num_datasets == 6:
                ts_layout.append(["TS1", "TS2"])
                ts_layout.append(["TS3", "TS4"])
                ts_layout.append(["TS5", f"TS{num_datasets}"] if num_datasets == 6 else ["TS5", ""])

            fig, axes = plt.subplot_mosaic(ts_layout, figsize=(8.27, 11.69), dpi=300)  # A4 size in inches
            # fig.subplots_adjust(hspace=0.4)  # Increase hspace to add more space between charts
            # fig.suptitle(title, fontsize=16, weight='bold', y=0.94)

            add_header_or_footer_to_a4_portrait(fig, header_image_path, position='header')
            add_header_or_footer_to_a4_portrait(fig, footer_image_path, position='footer', page_number=2, total_pages=3)


            # First find global min and max across all datasets
            all_values = []
            for values in self.data.values.values():
                all_values.extend(values)
            global_ymin = min(all_values)
            global_ymax = max(all_values)
            # Add a small padding (5%) to the y-axis limits for better visualization
            y_padding = (global_ymax - global_ymin) * 0.05
            global_ymin -= y_padding
            global_ymax += y_padding

            for i, (key, values) in enumerate(self.data.values.items(), 1):
                if i <= 6:
                    ts_key = f"TS{i}"
                    if ts_key in axes: # Check if the key exists in the axes
                        ax = axes[ts_key]
                        # Create time indices for the x-axis
                        time_indices = list(range(len(values)))

                        ax.plot(time_indices, values, 'o-', color='black', linewidth=0.5, markersize=4)

                        # Calculate boxplot statistics to identify outliers
                        q1 = pd.Series(values).quantile(0.25)
                        q3 = pd.Series(values).quantile(0.75)
                        iqr = q3 - q1
                        lower_bound = q1 - 1.5 * iqr
                        upper_bound = q3 + 1.5 * iqr

                        # Identify outliers
                        outlier_indices = [idx for idx, val in enumerate(values) if val < lower_bound or val > upper_bound]

                        # Plot outliers in red
                        if outlier_indices:
                            outlier_x = [time_indices[idx] for idx in outlier_indices]
                            outlier_y = [values[idx] for idx in outlier_indices]
                            ax.plot(outlier_x, outlier_y, 'rs', markersize=4)

                        # Set the same y-axis limits for all plots
                        ax.set_ylim(global_ymin, global_ymax)
                        
                        ax.set_title(f"{key}", loc='center', fontsize=font_size)
                        ax.grid(True, alpha=0.3)
                        ax.tick_params(axis='both', which='major', labelsize=8)

            pdf.savefig(fig)
            plt.close(fig)

            # NEW PDF PAGE - Boxplots and Means with Confidence Intervals
            fig, axs = plt.subplot_mosaic([
                ["Boxplots"],
                ["Interval plot"]
            ], figsize=(8.27, 11.69), dpi=300)  # A4 size in inches
            # fig.subplots_adjust(hspace=0.8)  # Increase hspace to add more space between charts
            # fig.suptitle(title, fontsize=16, weight='bold', y=0.94)

            add_header_or_footer_to_a4_portrait(fig, header_image_path, position='header')
            add_header_or_footer_to_a4_portrait(fig, footer_image_path, position='footer', page_number=3, total_pages=3)


            # Boxplots
            ax = axs["Boxplots"]
            boxplot_data = []
            labels = []

            for key, values in self.data.values.items():
                boxplot_data.append(values)
                labels.append(key)

            # Create boxplot
            ax.boxplot(boxplot_data, labels=labels, patch_artist=True, showcaps=False, 
                       boxprops={'color': 'black', 'facecolor': '#a1d111', 'linewidth': 0.3},
                       whiskerprops={'color': 'black', 'linewidth': 0.5},
                       medianprops={'color': 'black', 'linewidth': 0.5},
            )

            # Add the means to the boxplots and draw a line between them
            ax.plot(range(1, len(labels)+1), [sum(values) / len(values) for values in boxplot_data], color='black', markersize=4, lw=0.5, marker='+')

            # Set labels and grid
            ax.set_title("Boxplots of all datasets", loc='left', fontsize=10)
            ax.set_ylabel("Value", fontsize=font_size)
            ax.set_yticks(ax.get_yticks())  # Explicitly set the ticks
            ax.set_yticklabels(ax.get_yticks().round(2), fontsize=font_size)
            ax.set_xticklabels(labels, fontsize=font_size)
            ax.grid(True, alpha=0.3)

            # Interval plot
            # Interval plot
            ax = axs["Interval plot"]
            mean_data = []
            ci_data = []
            # Calculate means and 95% CIs
            for key, values in self.data.values.items():
                df = pd.DataFrame({key: values})
                mean = df[key].mean()
                mean_data.append(mean)
                # Calculate 95% CI for the mean
                se = df[key].std() / np.sqrt(df[key].count())
                ci = se * stats.t.ppf(0.975, df[key].count()-1)
                ci_data.append(ci)

            # Plot means with CI error bars
            y_pos = np.arange(len(labels))
            
            # Plot the vertical error bars
            ax.errorbar(y_pos, mean_data, yerr=ci_data, fmt='o', markersize=4, 
                        capsize=3, linewidth=0.5, color='#95b92a')

            # Format the plot
            ax.set_title("Means with 95% Confidence Intervals", loc='left', fontsize=10)
            ax.set_xticks(y_pos)
            ax.set_xticklabels(labels, fontsize=font_size)
            ax.grid(True, alpha=0.3)


            pdf.savefig(fig)
            plt.close(fig)

        pdf_io.seek(0)
        plt.close('all')
        return pdf_io
    
    def _convert_combined_to_separate(self, combined: FtestMultipleDataCombined) -> FtestMultipleDataSeparate:
        """
        Convert the combined format (one 'values' array and one 'groups' array)
        into the separate format (dictionary of named datasets).
        """
        group_map = {}
        for value, grp in zip(combined.values, combined.groups):
            if grp not in group_map:
                group_map[grp] = []
            group_map[grp].append(value)

        return FtestMultipleDataSeparate(values=group_map)