import io
import numpy as np
import pandas as pd
import scipy.stats as stats
import matplotlib.pyplot as plt
from pydantic import BaseModel, Field, field_validator
from matplotlib.backends.backend_pdf import PdfPages
from typing import Dict, List, Optional, Any
from api.schemas import BusinessLogicException

from ...utils.pdf_utils import add_header_or_footer_to_a4_portrait

header_image_path = 'assets/img/Header.png'
footer_image_path = 'assets/img/Footer.png'

from ...utils.mpl_table_utils import merge_mpl_table_cells as mergecells


class OneWayAnovaConfig(BaseModel):
    title: str
    alphalevel: float
    power: Optional[float] = None

# Existing separate data format
class OneWayAnovaDataSeparate(BaseModel):
    values: Dict[str, List[float]] = Field(..., min_length=1)
    
    @field_validator('values')
    def check_valid_groups(cls, v):
        # Check the number of datasets
        num_datasets = len(v)
        if num_datasets < 2 or num_datasets > 6:
            raise ValueError("Number of datasets must be between 2 and 6")
        
        # Check for empty datasets
        for group, values in v.items():
            if len(values) < 5:
                raise ValueError(f"Group '{group}' has less than 5 samples")
                
        # Check for NaN or infinite values
        for group, values in v.items():
            if any(not np.isfinite(x) for x in values):
                raise ValueError(f"Group '{group}' contains NaN or infinite values")
                
        return v

# New combined data format
class OneWayAnovaDataCombined(BaseModel):
    values: List[float]
    groups: List[str]
    
    @field_validator('groups')
    def check_valid_groups(cls, v, info):
        # Get values from the info.data dictionary which contains all input values
        if 'values' not in info.data:
            return v
            
        if len(v) != len(info.data['values']):
            raise ValueError("Values and groups must have the same length")
        
        # Check the unique group count
        unique_groups = set(v)
        if len(unique_groups) < 2 or len(unique_groups) > 6:
            raise ValueError("Number of groups must be between 2 and 6")
        
        # Count samples per group to ensure minimum samples
        group_counts = {}
        for group in v:
            group_counts[group] = group_counts.get(group, 0) + 1
            
        # Check minimum sample size per group
        for group, count in group_counts.items():
            if count < 5:
                raise ValueError(f"Group '{group}' has less than 5 samples")
                
        return v
    
    @field_validator('values')
    def check_valid_numbers(cls, v):
        if any(not np.isfinite(x) for x in v):
            raise ValueError("Data contains NaN or infinite values")
        return v

class OneWayAnovaRequest(BaseModel):
    project: str
    step: str
    config: OneWayAnovaConfig
    data: Any  # validate this separately
    
    @field_validator('data')
    def validate_data_format(cls, v):
        try:
            if isinstance(v, dict) and 'values' in v:
                if isinstance(v['values'], dict):
                    return OneWayAnovaDataSeparate(**v)
                elif isinstance(v['values'], list) and 'groups' in v:
                    return OneWayAnovaDataCombined(**v)
            
            raise ValueError("Data format not recognized")
        except Exception as e:
            raise ValueError(f"Invalid data format: {str(e)}")

class OneWayAnova:
    def __init__(self, data: Dict):
        try:
            validated_data = OneWayAnovaRequest(**data)
            self.project = validated_data.project
            self.step = validated_data.step
            self.config = validated_data.config
            self.data = validated_data.data
            
            # Convert combined format to separate format if needed
            if isinstance(self.data, OneWayAnovaDataCombined):
                self._convert_combined_to_separate()
                
        except Exception as e:
            raise BusinessLogicException(
                error_code="error_validation",
                field=str(e),
                details={"message": f"Invalid or missing field: {str(e)}"}
            )
    
    def _convert_combined_to_separate(self):
        """Convert combined data format to separate format for ANOVA analysis"""
        values = self.data.values
        groups = self.data.groups
        
        # Create dictionary of grouped data
        separate_data = {}
        
        # Group values by their corresponding group labels
        for value, group in zip(values, groups):
            if group not in separate_data:
                separate_data[group] = []
            separate_data[group].append(value)
        
        # Create a new OneWayAnovaDataSeparate object
        self.data = OneWayAnovaDataSeparate(values=separate_data)

    def process(self):
        title = self.config.title
        alpha = self.config.alphalevel
        power = self.config.power
        # Extract the datasets from the data
        keys = list(self.data.values.keys())
        datasets = list(self.data.values.values())
        dataframes = {key: pd.DataFrame({key: dataset}) for key, dataset in zip(keys, datasets)}
        
        # Format keys for display
        keys_string = "\n".join(keys)
        
        # Perform statistical calculations
        f_stat, p_value, df_factor, df_error, df_total = self._calculate_anova_stats(datasets)
        # Prepare variable for total degrees of freedom
        df_all = (f"Factor = {df_factor}\nError = {df_error}\nTotal = {df_total}")
        
        # Check if the null hypothesis is rejected
        difference_string, difference_color = self._determine_hypothesis_rejection(p_value, alpha)
        
        # Calculate pooled standard deviation
        pooled_std = self._calculate_pooled_std(datasets)
        
        # Generate descriptive statistics
        confidence_level, confidence_percent = self._calculate_confidence_level(alpha)
        stats_summary = self._generate_descriptive_stats(dataframes, keys, pooled_std, confidence_level, confidence_percent)
        descriptive_stats = pd.DataFrame(stats_summary).T

        # Calculate power statistics
        # Calculate power statistics
        datasets = list(self.data.values.values())
        power_statistics = self._calculate_power_stats(datasets, df_factor, df_error, alpha)
        
        # Extract needed values from power statistics
        n = power_statistics["n"]
        ms_error = power_statistics["ms_error"]
        power_60 = power_statistics["detectable_diffs"][0.6]
        power_70 = power_statistics["detectable_diffs"][0.7]
        power_80 = power_statistics["detectable_diffs"][0.8]
        power_90 = power_statistics["detectable_diffs"][0.9]
        required_sample_size = power_statistics["required_sample_sizes"] if power_statistics["required_sample_sizes"] else None

        # Generate PDF report
        pdf_io = io.BytesIO()
        with PdfPages(pdf_io) as pdf:
            fig, axs = plt.subplot_mosaic([
                    ["Anova Results", "Anova Results"],
                    ["Descriptive Statistics", "Descriptive Statistics"],
                    ["Mean Comparison", "Mean Differ"]],    # Chance and Detectable Difference
                    figsize=(8.27, 11.69), dpi=300)  # A4 size in inches
                # fig.subplots_adjust(hspace=0.4)  # Increase hspace to add more space between charts

            #fig.suptitle(title, fontsize=16, weight='bold', y=0.94)


            header_ax = add_header_or_footer_to_a4_portrait(fig, header_image_path, position='header')
            footer_ax = add_header_or_footer_to_a4_portrait(fig, footer_image_path, position='footer', page_number=1, total_pages=3)


            # Define the colors + font size
            edgecolor = "#7c7c7c"
            grey = "#e7e6e6"
            green_table = "#9cc563"
            lightgreen_table = "#d6ed5f"
            font_size=7

            # Anova Results
            '''
            Adjust table row heights
            '''
            ax = axs["Anova Results"]
            ax.axis('off')

            # Define table data
            cellText = [
                ["Configuration", "", "Hypothesis", "", "", ""],
                ["Each sample in its own column", "", r"$\mathrm{H_{0}:}$ all $\mathrm{\mu_{i} = \mu_{j}}$", "F-value", "df", "p-Value*"],
                ["\nSamples", f"{keys_string}", r"$\mathrm{H_{0}:}$ one $\mathrm{\mu_{i} = \mu_{j}}$", f"\n \n{f_stat:.2f}", f"\n \n{df_all}", f"\n \n{p_value:.3f}"],
                ["", "", "", "", "", ""],
                ["", "", "", "", "", ""],
                ["Test-Setup", "Different", "", "", "For detail information look\non the descriptive statistic", ""],
                ["Alpha-Level", alpha, "", "", f"Pooled standard deviation = {pooled_std:.3f}", ""],
                ["Interested\ndifference**", f"{power if power is not None else '-'}", "", f"{difference_string}", "", ""],
                ["", "", "", "", "", ""]
            ]
            # Set the column widths as needed
            col_widths = [0.15, 0.15, 0.15, 0.15, 0.15, 0.15]

            # Background color for the table
            bg_colors = [
                [grey, grey, grey, grey, grey, grey],
                ["#ffffff", "#ffffff", lightgreen_table, "#ffffff", "#ffffff", "#ffffff"],
                ["#ffffff", "#ffffff", green_table, "#ffffff", "#ffffff", green_table],
                ["#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff", green_table],
                ["#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff"],
                ["#ffffff", "#ffffff", "#ffffff", grey, grey, grey],
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
                ["none", "none", "none", "none", "none", "none"],
                ["none", "none", "none", "none", "none", "none"]
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
                cell.set_edgecolor(edgecolor)
                cell.set_linewidth(0.5)

            # Merge the cells of the table
            mergecells(table, [(0, 0), (0, 1)])
            mergecells(table, [(0, 3), (0, 4), (0, 5)])
            mergecells(table, [(2, 3), (3, 3)])
            mergecells(table, [(2, 4), (3, 4)])
            mergecells(table, [(2, 5), (3, 5)])
            mergecells(table, [(1, 0), (1, 1)])
            mergecells(table, [(2, 0), (3, 0), (4, 0)])
            mergecells(table, [(2, 1), (3, 1), (4, 1)])
            mergecells(table, [(4, 3), (4, 4), (4, 5)])
            mergecells(table, [(5, 3), (5, 4), (5, 5)])
            mergecells(table, [(6, 3), (6, 4), (6, 5)])
            mergecells(table, [(7, 3), (7, 4), (7, 5)])
            mergecells(table, [(3, 2), (4, 2), (5, 2), (6, 2), (7, 2)])
            mergecells(table, [(8, 0), (8, 1), (8, 2), (8, 3), (8, 4), (8, 5)])

            # Fix the cells, that cannot be defined before mergecells
            table.get_celld()[8, 0].set_fontsize(5)
            

            cell_text_centered_1 = table.get_celld()[(0, 4)]
            cell_text_centered_1.set_text_props(
                text='Results',
                x=1.5,
                y=0.5,
                visible=True,
                ha='center'
            )
            cell_text_centered_2 = table.get_celld()[(5, 4)]
            cell_text_centered_2.set_text_props(
                text='For detail information look\non the descriptive statistic',

                x=1.5,
                y=0.5,
                visible=True,
                ha='center'
            )
            cell_text_centered_3 = table.get_celld()[(6, 4)]
            cell_text_centered_3.set_text_props(
                text=f'Pooled standard deviation = {pooled_std:.3f}',
                x=1.5,
                y=0.5,
                visible=True,
                ha='center'
            )
            cell_text_small = table.get_celld()[(8, 0)]
            cell_text_small.set_text_props(
                text='* If the p-value is less than the α-level, then H0 is to be rejected and the alternative hypothesis H1 is to be accepted.\n** Optional: What difference between the two means has a practical value? (Power and sample size)',
                visible=True,
                color='grey',
                ha='right'
            )

            bold_text = [(1, 3), (1, 4), (1, 5), (5, 1)]
            for row, col in bold_text:
                cell = table.get_celld()[(row, col)]
                cell.set_text_props(weight='bold')

            left_text = [(1, 0), (2, 4), (5, 3), (6, 3), (7, 3), (8, 0)]
            for row, col in left_text:
                cell = table.get_celld()[(row, col)]
                cell.set_text_props(ha='left')

            right_text = [(0, 0), (3, 3), (4, 3)]
            for row, col in right_text:
                cell = table.get_celld()[(row, col)]
                cell.set_text_props(ha='right')
            
            top_text = [(2, 1)]
            for row, col in top_text:
                cell = table.get_celld()[(row, col)]
                cell.set_text_props(va='top')
                cell.set_fontsize(5)

            # Descriptive Statistics table
            ax = axs["Descriptive Statistics"]
            ax.axis('off')
            ax.set_title("Descriptive Statistics", loc='left', pad=-50, y=1.02)
            descriptive_table_widths = [0.18, 0.06, 0.11, 0.11, 0.11, 0.11, 0.21, 0.11]
            cellText = list(zip(*descriptive_stats.T.values.tolist()))
            descriptive_table = ax.table(
                cellText=cellText,
                colLabels=descriptive_stats.columns,
                cellLoc='center',
                loc='center',
                colWidths=descriptive_table_widths
            )

            descriptive_table.auto_set_font_size(False)
            descriptive_table.set_fontsize(font_size)

            for cell in descriptive_table._cells.values():
                cell.set_edgecolor(edgecolor)
                cell.set_linewidth(0.5)
            
            # Set the top row color to #e7e6e6
            for cell in descriptive_table._cells:
                if cell[0] == 0:
                    descriptive_table._cells[cell].set_facecolor(grey)

            # Mean comparison
            ax = axs["Mean Comparison"]
            ax.set_title("Means Comparison Chart", loc='center')
            # Extract means and standard deviations
            means = []
            std_devs = []
            variance = []
            labels = []

            for key, stats_dict in stats_summary.items():
                mean = stats_dict['Mean']
                std_dev = stats_dict['StDev']
                
                means.append(mean)
                std_devs.append(std_dev)
                variance.append(std_dev**2)
                labels.append(key)

            # Plot horizontal errorbars using standard deviation
            y_positions = range(len(means))[::-1]  # Reverse the order for plotting
            ax.errorbar(means, y_positions, xerr=std_devs, fmt='o', markersize=3, 
                        capsize=0, linewidth=0.5, color='#95b92a')

            # Add labels for each point
            for i, (label, mean) in enumerate(zip(labels[::-1], means[::-1])):
                ax.text(mean, i-0.3, f"  {mean:.3f}",  fontsize=font_size, ha='center')

            # Set y-ticks and labels
            ax.set_yticks(y_positions)
            ax.set_ylim(-0.5, len(means)-0.5)

            ax.set_yticklabels(labels, fontsize=font_size)
            xticks = ax.get_xticks()
            ax.set_xticks(xticks)
            ax.set_xticklabels([f"{x:.2f}" for x in xticks], fontsize=font_size)
            ax.grid(True, alpha=0.3)
            ax.set_position([0.2, 0.1, 0.35, 0.25])

            # Mean Difference Chart
            ax = axs["Mean Differ"]
            ax.axis('off')

            # Mean Differ Table
            ax = axs["Mean Differ"]
            ax.axis('off')
            ax.set_title("Which mean differs?", loc='center')

            # Create table data
            table_data = []
            for i, label in enumerate(labels):
                differs_from = []
                for j, other_label in enumerate(labels):
                    if i != j:  # Don't compare with itself
                        # Check if confidence intervals overlap using variance instead of std_dev
                        ci_lower_i = means[i] - std_devs[i]
                        ci_upper_i = means[i] + std_devs[i]
                        ci_lower_j = means[j] - std_devs[j]
                        ci_upper_j = means[j] + std_devs[j]
                        
                        if not (ci_lower_i <= ci_upper_j and ci_lower_j <= ci_upper_i):
                            differs_from.append(str(j + 1))  # Using index numbers instead of labels
                
                table_data.append([i + 1, label, ", ".join(differs_from) if differs_from else "None"])

            # Create table
            differ_table = ax.table(
                cellText=table_data,
                colLabels=["#", "Sample", "Differs from"],
                loc='center',
                cellLoc='center',
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
            
            # Add the bottom row for Chance and Detectable
            ts_layout.append(["Chance", "Detectable"])
            
            fig, axes = plt.subplot_mosaic(ts_layout, figsize=(8.27, 11.69), dpi=300)  # A4 size in inches
            # fig.subplots_adjust(hspace=0.4)  # Increase hspace to add more space between charts
            # fig.suptitle(title, fontsize=16, weight='bold', y=0.94)


            header_ax = add_header_or_footer_to_a4_portrait(fig, header_image_path, position='header')
            footer_ax = add_header_or_footer_to_a4_portrait(fig, footer_image_path, position='footer', page_number=2, total_pages=3)


            # Track global min and max values across all datasets
            all_values = []
            for values in self.data.values.values():
                all_values.extend(values)
            
            global_min = min(all_values)
            global_max = max(all_values)
            
            # Add a buffer to the global limits for better visualization
            y_range = global_max - global_min
            buffer = y_range * 0.05  # 5% buffer
            global_min -= buffer
            global_max += buffer

            # Plot each dataset
            for i, (key, values) in enumerate(self.data.values.items(), 1):
                if i <= 6:  # Only process up to 6 datasets
                    ts_key = f"TS{i}"
                    if ts_key in axes:  # Check if the subplot exists in the layout
                        ax = axes[ts_key]
                        # Create time indices for x-axis
                        time_indices = list(range(len(values)))

                        ax.plot(time_indices, values, 'o-', color='black', linewidth=0.5, markersize=4)
                        
                        # Calculate boxplot statistics to identify outliers
                        q1 = pd.Series(values).quantile(0.25)
                        q3 = pd.Series(values).quantile(0.75)
                        iqr = q3 - q1
                        lower_bound = q1 - 1.5 * iqr
                        upper_bound = q3 + 1.5 * iqr
                        
                        # Identify outliers and non-outliers
                        outlier_indices = [idx for idx, val in enumerate(values) if val < lower_bound or val > upper_bound]
                        
                        # Plot outliers in red
                        if outlier_indices:
                            outlier_x = [time_indices[idx] for idx in outlier_indices]
                            outlier_y = [values[idx] for idx in outlier_indices]
                            ax.plot(outlier_x, outlier_y, 'rs', markersize=4)
                        
                        ax.set_title(f"{key}", loc='center', fontsize=font_size)
                        # ax.set_xlabel("Observation", fontsize=8)
                        # ax.set_ylabel("Value", fontsize=8)
                        ax.grid(True, alpha=0.3)
                        ax.tick_params(axis='both', which='major', labelsize=8)
                        
                        # Apply global y-axis limits to all plots
                        ax.set_ylim(global_min, global_max)
                        
                        # Remove ticklabels for plots on the right side (even indices)
                        if i % 2 == 0:  # Even index means it's on the right
                            ax.set_yticklabels([])

            # Setup for the power analysis and detectable difference table
            ax = axes["Chance"]
            ax.axis('off')
            ax.set_title("Power and detectable difference", loc='left', pad=-50, y=1.2, fontsize=font_size)
            
            # Calculate the observed difference (using maximum difference between means)
            means = [np.mean(dataset) for dataset in datasets]
            max_mean_diff = max(means) - min(means)
            
            # Determine color based on where the observed difference falls
            if max_mean_diff < power_60:
                observed_difference_interval = "<60%"
                observed_difference_color = "#c00000"  # Red 
                observed_difference_text_color = "#ffffff" 
            elif power_60 <= max_mean_diff < power_70:
                observed_difference_interval = "60%-70%"
                observed_difference_color = "#f9b002"  # Orange
                observed_difference_text_color = "#000000"
            elif power_70 <= max_mean_diff < power_80:
                observed_difference_interval = "70%-80%"
                observed_difference_color = "#f9b002"  # Orange
                observed_difference_text_color = "#000000"
            elif power_80 <= max_mean_diff < power_90:
                observed_difference_interval = "80%-90%"
                observed_difference_color = "#f9b002"  # Orange
                observed_difference_text_color = "#000000"
            else:
                observed_difference_interval = ">90%" 
                observed_difference_color = "#a7c315"  # Green
                observed_difference_text_color = "#000000"

            # Setup the cell text based on whether power was provided or not
            if power is not None:
                # Calculate the chance of detecting the specified difference
                # Using the non-central F-distribution to estimate the power
                f_critical = stats.f.ppf(1 - alpha, df_factor, df_error)
                non_centrality = n * df_factor * (power**2) / (2 * ms_error)
                detection_chance = (1 - stats.ncf.cdf(f_critical, df_factor, df_error, non_centrality)) * 100
                
                if detection_chance < 60:
                    observed_difference_color = "#c00000"  # Red
                    observed_difference_text_color = "#ffffff"  
                elif 60 <= detection_chance <= 90:
                    observed_difference_color = "#f9b002"  # Orange
                    observed_difference_text_color = "#000000"
                else:
                    observed_difference_color = "#a7c315"  # Green
                    observed_difference_text_color = "#000000"
                
                ax.set_title(f"What is the chance of detecting a difference of {power}?", 
                             pad=-70, y=1.02, fontsize=font_size)
                
                cellText = [
                    ["60%", "", "90%"],
                    ["", "", ""],
                    [f"{power_60:.6f}", "", f"{power_90:.6f}"],
                    ["Sample size", "Chance of detecting a difference", ""],
                    [f"{int(n)}", "", f"{detection_chance:.1f}%"]
                ]
            else:
                ax.set_title("Chance of detecting a difference", loc='center', 
                             pad=-70, y=1.02, fontsize=font_size)
                
                cellText = [
                    ["60%", "", "90%"],
                    ["", "", ""],
                    [f"{power_60:.6f}", "", f"{power_90:.6f}"],
                    ["Sample size", "Max. Observed difference", ""],
                    [f"{int(n)}", f"{max_mean_diff:.6f}", f"{observed_difference_interval}"]
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

            # Update the detectable difference table
            ax = axes["Detectable"]
            ax.axis("off")

            if power is not None:
                # If power was provided, show required sample sizes
                ax.set_title(f"What sample size is required to detect a difference\nof {power}?", loc='center', pad=-70, y=1.02, fontsize=font_size)
                detectable_cellText = [
                    ["60%", f"{required_sample_size['Power 0.6']}"],
                    ["70%", f"{required_sample_size['Power 0.7']}"],
                    ["80%", f"{required_sample_size['Power 0.8']}"],
                    ["90%", f"{required_sample_size['Power 0.9']}"]
                ]
                colLabels_difference = ["Power", "Sample Size"]
            else:
                # Otherwise show detectable differences
                ax.set_title("Detectable difference with sample sizes of N", loc='center', pad=-70, y=1.02, fontsize=font_size)
                detectable_cellText = [
                    ["60%", f"{power_60:.5f}"],
                    ["70%", f"{power_70:.5f}"],
                    ["80%", f"{power_80:.5f}"],
                    ["90%", f"{power_90:.5f}"],
                ]
                colLabels_difference = ["Power", "Difference"]

            # Define table column widths
            col_widths = [0.5, 0.5]

            # Create the table
            table = ax.table(
                bbox=[0, 0, 1, 0.5],
                cellText=detectable_cellText,
                colLabels=colLabels_difference,
                cellLoc='center',
                loc='center',
                colWidths=col_widths
            )

            # Set detectable table font size
            table.auto_set_font_size(False)
            table.set_fontsize(font_size)

            # Format detectable table
            for key, cell in table.get_celld().items():
                row, col = key
                cell.set_edgecolor(edgecolor)
                cell.set_linewidth(0.5)
                if row == 0:  # Header row
                    cell.set_facecolor(grey)

            pdf.savefig(fig)
            plt.close(fig)

            # NEW PDF PAGE - Boxplots and Means with Confidence Intervals
            fig, axs = plt.subplot_mosaic([
                ["Boxplots"],
                ["Interval plot"]
            ], figsize=(8.27, 11.69), dpi=300)  # A4 size in inches
            # fig.subplots_adjust(hspace=0.8)  # Increase hspace to add more space between charts
            # fig.suptitle(title, fontsize=16, weight='bold', y=0.94)


            header_ax = add_header_or_footer_to_a4_portrait(fig, header_image_path, position='header')
            footer_ax = add_header_or_footer_to_a4_portrait(fig, footer_image_path, position='footer', page_number=3, total_pages=3)


            # Boxplots
            ax = axs["Boxplots"]
            # Create a combined DataFrame for boxplot
            boxplot_data = []
            labels = []
            for key, values in self.data.values.items():
                boxplot_data.append(values)
                labels.append(key)

            # Create boxplot
            ax.boxplot(boxplot_data, labels=labels, patch_artist=True, showcaps=False, 
                       boxprops={'color': 'black', 'facecolor': '#95b92a', 'linewidth': 0.3},
                       whiskerprops={'color': 'black', 'linewidth': 0.5},
                       medianprops={'color': 'black', 'linewidth': 0.5}, flierprops={"marker": "x"}
            )

            # Add the means to the boxplots and draw a line between them
            ax.plot(range(1, len(labels)+1), [sum(values) / len(values) for values in boxplot_data], color='black', markersize=4, lw=0.5, marker='+')

            # Set labels and grid
            ax.set_title("Boxplots of all datasets", loc='left', fontsize=10)
            ax.set_ylabel("Value", fontsize=font_size)
            yticks = ax.get_yticks()
            ax.set_yticks(yticks)
            ax.set_yticklabels([f"{y:.2f}" for y in yticks], fontsize=font_size)
            ax.set_xticklabels(labels, fontsize=font_size)
            ax.grid(True, alpha=0.3)

            # Add a legend for the mean marker
            ax.plot([], [], '+', color='black', markersize=6, label='Mean')
            legend = ax.legend(fontsize='x-small')

            # Interval plot
            ax = axs["Interval plot"]
            ax.set_title("Means with 95% Confidence Intervals", loc='left', fontsize=10)

            # Plot means with confidence intervals
            x_positions = range(len(labels))
            means = []
            ci_low = []
            ci_high = []

            for key, stats_dict in stats_summary.items():
                mean = stats_dict['Mean']
                means.append(mean)
                # Extract the CI values from the pre-calculated "95% CI for $mu$" string
                ci_string = stats_dict[f"{confidence_percent}% CI for µ"]
                # Parse the string to extract lower and upper bounds
                ci_bounds = ci_string.strip('()').split('; ')
                ci_low.append(float(ci_bounds[0]))
                ci_high.append(float(ci_bounds[1]))

            # Calculate the error bar sizes for plt.errorbar
            yerr = [[mean - low for mean, low in zip(means, ci_low)], 
                   [high - mean for mean, high in zip(means, ci_high)]]

            # Plot vertical error bars
            ax.errorbar(x_positions, means, yerr=yerr, 
                        fmt='o', markersize=4, color='#95b92a', capsize=5, linewidth=0.5)
            
            # Plot means and draw a line between them
            ax.plot(x_positions, means, markersize=0, color='#95b92a', linewidth=0.5)

            # Set labels
            ax.set_xticks(x_positions)
            ax.set_xticklabels(labels, fontsize=font_size)
            ax.grid(True, alpha=0.3)
            ax.set_ylabel("Value", fontsize=font_size)
            ax.set_yticklabels(ax.get_yticks().round(2), fontsize=font_size)

            pdf.savefig(fig)
            plt.close(fig)

        pdf_io.seek(0)
        plt.close('all')
        return pdf_io

    def _calculate_anova_stats(self, datasets):
        """Calculate the F-statistic and p-value for one-way ANOVA."""
        f_stat, p_value = stats.f_oneway(*datasets)
        # Degrees of freedom (Factor, Error, Total)
        df_factor = len(datasets) - 1
        df_error = sum([len(dataset) - 1 for dataset in datasets])
        df_total = sum([len(dataset) for dataset in datasets]) - 1
        
        return f_stat, p_value, df_factor, df_error, df_total

    def _determine_hypothesis_rejection(self, p_value, alpha):
        """Determine if null hypothesis is rejected and return result strings and colors."""
        if p_value < alpha:
            difference_string = "Minimum one mean value is different from the other\nmean values"
            difference_color = "#9cc563"
        else:
            difference_string = "No mean value is different from the other mean values"
            difference_color = "#d6ed5f"
        
        return difference_string, difference_color

    def _calculate_pooled_std(self, datasets):
        """Calculate the pooled standard deviation."""
        std_devs = []
        for dataset in datasets:
            std_devs.append(pd.Series(dataset).std())
        
        n = 50  # This might need to be parameterized based on actual data
        k = len(std_devs)
        numerator = sum((n-1) * (s**2) for s in std_devs)
        denominator = (n*k) - k
        
        pooled_std = (numerator/denominator)**0.5
        return pooled_std

    def _calculate_confidence_level(self, alpha):
        """Calculate confidence level from alpha."""
        confidence_level = 1 - (alpha/2)
        confidence_percent = int((1 - alpha) * 100)
        return confidence_level, confidence_percent

    def _generate_descriptive_stats(self, dataframes, keys, pooled_std, confidence_level, confidence_percent):
        """Generate descriptive statistics for each dataset."""
        stats_summary = {
            key: {
                "Quelle": key,
                "N": df[key].count(),
                "Mean": df[key].mean().round(5),
                "Median": df[key].median().round(5),
                "StDev": df[key].std().round(5),
                "SE Mean": (df[key].std() / (df[key].count() ** 0.5)).round(5),
                f"{confidence_percent}% CI for µ": f"({(df[key].mean() - stats.t.ppf(confidence_level, df[key].count()-1) * pooled_std / (df[key].count() ** 0.5)).round(5)}; {(df[key].mean() + stats.t.ppf(confidence_level, df[key].count()-1) * pooled_std / (df[key].count() ** 0.5)).round(5)})",
                "Range": (df[key].max() - df[key].min()).round(5)
            }
            for key, df in dataframes.items()
        }
        return stats_summary

    def _calculate_power_stats(self, datasets, df_factor, df_error, alpha):
        """Calculate power-related statistics and detectable differences."""
        n_values = [len(group) for group in datasets]
        n = sum(n_values) / len(n_values)  # Average sample size per group
        k = len(datasets)
        total_n = sum(n_values)
        
        # Calculate mean square error for ANOVA
        overall_mean = sum(sum(g) for g in datasets) / total_n
        ss_error = sum(sum((x - np.mean(g))**2 for x in g) for g in datasets)
        ms_error = ss_error / df_error
        
        # Calculate detectable difference for different power levels
        power_levels = [0.6, 0.7, 0.8, 0.9]
        detectable_diffs = {}
        
        for p in power_levels:
            f_critical = stats.f.ppf(1 - alpha, df_factor, df_error)
            
            # Binary search to find lambda that gives the desired power
            lambda_start = 0
            lambda_end = 50
            target_power = p
            
            while lambda_end - lambda_start > 0.01:
                lambda_mid = (lambda_start + lambda_end) / 2
                achieved_power = 1 - stats.ncf.cdf(f_critical, df_factor, df_error, lambda_mid)
                
                if abs(achieved_power - target_power) < 0.001:
                    break
                elif achieved_power < target_power:
                    lambda_start = lambda_mid
                else:
                    lambda_end = lambda_mid
            
            # Calculate the detectable difference
            non_central_param = lambda_mid
            detectable_diff = np.sqrt((2 * non_central_param * ms_error) / (n * df_factor))
            
            # Store the result
            detectable_diffs[p] = detectable_diff
        
        # Calculate required sample sizes for detecting a specified difference (if power is provided)
        required_sample_sizes = {}
        power_value = self.config.power
        
        if power_value is not None:
            for p in power_levels:
                # Calculate non-centrality parameter required for this power level
                f_critical = stats.f.ppf(1 - alpha, df_factor, df_error)
                
                lambda_start = 0
                lambda_end = 100
                target_power = p
                
                while lambda_end - lambda_start > 0.01:
                    lambda_mid = (lambda_start + lambda_end) / 2
                    achieved_power = 1 - stats.ncf.cdf(f_critical, df_factor, df_error, lambda_mid)
                    
                    if abs(achieved_power - target_power) < 0.001:
                        break
                    elif achieved_power < target_power:
                        lambda_start = lambda_mid
                    else:
                        lambda_end = lambda_mid
                
                # Calculate required sample size using the rearranged formula:
                # n = (2 * lambda * ms_error) / (difference²  * df_factor)
                required_n = (2 * lambda_mid * ms_error) / (power_value**2 * df_factor)
                required_sample_sizes[f"Power {p}"] = np.ceil(required_n)
        
        results = {
            "n": n, 
            "ms_error": ms_error, 
            "detectable_diffs": detectable_diffs,
            "required_sample_sizes": required_sample_sizes if self.config.power is not None else None
        }
        
        return results

    def _determine_observed_difference_status(self, datasets, detectable_diffs):
        """Determine status of the observed difference compared to detectable differences."""
        means = [np.mean(dataset) for dataset in datasets]
        max_mean_diff = max(means) - min(means)
        
        if max_mean_diff < detectable_diffs[0.6]:
            observed_difference_interval = "<60%"
            observed_difference_color = "#c00000"  # Red
        elif detectable_diffs[0.6] <= max_mean_diff < detectable_diffs[0.7]:
            observed_difference_interval = "60%-70%"
            observed_difference_color = "#f9b002"  # Orange
        elif detectable_diffs[0.7] <= max_mean_diff < detectable_diffs[0.8]:
            observed_difference_interval = "70%-80%"
            observed_difference_color = "#f9b002"  # Orange
        elif detectable_diffs[0.8] <= max_mean_diff < detectable_diffs[0.9]:
            observed_difference_interval = "80%-90%"
            observed_difference_color = "#f9b002"  # Orange
        else:
            observed_difference_interval = ">90%"
            observed_difference_color = "#a7c315"  # Green
        
        return max_mean_diff, observed_difference_interval, observed_difference_color
