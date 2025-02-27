import io
import pandas as pd
import scipy.stats as stats
import matplotlib.pyplot as plt
from pydantic import BaseModel, Field
from matplotlib.backends.backend_pdf import PdfPages
from typing import Dict, List
from api.schemas import BusinessLogicException
from .mergecells import mergecells


class OneWayAnovaConfig(BaseModel):
    title: str
    alphalevel: float

class OneWayAnovaData(BaseModel):
    values: Dict[str, List[float]] = Field(..., min_length=1)

class OneWayAnovaRequest(BaseModel):
    project: str
    step: str
    config: OneWayAnovaConfig
    data: OneWayAnovaData

class OneWayAnova:

    def __init__(self, data: Dict):
        try:
            validated_data = OneWayAnovaRequest(**data)
            self.project = validated_data.project
            self.step = validated_data.step
            self.config = validated_data.config
            self.data = validated_data.data

            # Check the number of datasets
            num_datasets = len(self.data.values)
            if num_datasets < 2 or num_datasets > 6:
                raise BusinessLogicException(
                    error_code="error_validation",
                    field="values",
                    details={"message": "Number of datasets must be between 2 and 6"}
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
        # Extract the datasets from the data
        keys = list(self.data.values.keys())
        datasets = list(self.data.values.values())
        dataframes = {key: pd.DataFrame({key: dataset}) for key, dataset in zip(keys, datasets)}

        # Create a string with all keys in a new line
        keys_string = "\n".join(keys)

        # Perform the one-way ANOVA test
        f_stat, p_value = stats.f_oneway(*dataframes.values()) # Werte stimmen überein!
        # Degrees of freedom (Factor, Error, Total)
        df_factor = len(dataframes) - 1
        df_error = sum([len(dataset) - 1 for dataset in datasets])
        df_total = sum([len(dataset) for dataset in datasets]) - 1
        df_all = (f"Factor = {df_factor}\nError = {df_error}\nTotal = {df_total}")


        # Check if the null hypothesis is rejected
        if p_value[0] < alpha:
            difference_string = "Minimum one mean value is different from the other\nmean values"
        else:
            difference_string = "No mean value is different from the other mean values"


        # Pooled standard deviation
        samples_stdev = pd.concat(dataframes.values()).std()
        std_devs = []
        for i in range(len(samples_stdev)):
            std_devs.append(samples_stdev.iloc[i])
        n = 50
        k = len(std_devs)
        numerator = sum((n-1)* (s**2) for s in std_devs)
        denominator = (n*k) - k

        pooled_std = (numerator/denominator)**0.5

        # Descriptive Statistics
        stats_summary = {
            key: {
            "Quelle": key,
            "N": df[key].count(),
            "Mean": df[key].mean().round(5),
            "Median": df[key].median().round(5),
            "StDev": df[key].std().round(5),
            "SE Mean": (df[key].std() / (df[key].count() ** 0.5)).round(5),
            "95% CI for $mu$": f"({(df[key].mean() - stats.t.ppf(0.975, df[key].count()-1) * pooled_std / (df[key].count() ** 0.5)).round(5)}; {(df[key].mean() + stats.t.ppf(0.975, df[key].count()-1) * pooled_std / (df[key].count() ** 0.5)).round(5)})",
            "Range": (df[key].max() - df[key].min()).round(5)
            }
            for key, df in dataframes.items()
        }
        descriptive_stats = pd.DataFrame(stats_summary).T

        pdf_io = io.BytesIO()

        with PdfPages(pdf_io) as pdf:
            # NEW PDF PAGE - T-Test results, Descriptive Statistics, Data Time Series, Chance and Detectable Difference
            fig, axs = plt.subplot_mosaic([
                ["Anova Results", "Anova Results"],
                ["Descriptive Statistics", "Descriptive Statistics"],
                ["Mean Comparison", "Mean Differ"]],    # Chance and Detectable Difference
                figsize=(8.27, 11.69))  # A4 size in inches
            # fig.subplots_adjust(hspace=0.4)  # Increase hspace to add more space between charts

            fig.suptitle(title, fontsize=16, weight='bold', y=0.94)

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
                ["Each sample in its own column", "", r"$H_{0}:$ all $\mu_{i}$ = $\mu_{j}$", "F-value", "df", "p-Value*"],
                ["\nSamples", f"{keys_string}", r"$H_{1}:$ one $\mu_{i}$ $\neq$ $\mu_{j}$", f"\n \n{f_stat[0]:.2f}", f"\n \n{df_all}", f"\n \n{p_value[0]:.3f}"],
                ["", "", "", "", "", ""],
                ["", "", "", "", "", ""],
                ["Test-Setup", "Different", "", "", "For detail information look\non the descriptive statistic", ""],
                [r"$\alpha$-Level", alpha, "", "", f"Pooled standard deviation = {pooled_std:.3f}", ""],
                ["Interested\ndifference**", "-", "", f"{difference_string}", "", ""],
                ["", "", "", "", "", ""]
            ]
            # Set the column widths as needed
            col_widths = [0.15, 0.15, 0.15, 0.15, 0.15, 0.15]

            # Background color for the table
            bg_colors = [
                ["#e7e6e6", "#e7e6e6", "#e7e6e6", "#e7e6e6", "#e7e6e6", "#e7e6e6"],
                ["#ffffff", "#ffffff", "#d6ed5f", "#ffffff", "#ffffff", "#ffffff"],
                ["#ffffff", "#ffffff", "#9cc563", "#ffffff", "#ffffff", "#9cc563"],
                ["#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff", "#9cc563"],
                ["#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff"],
                ["#ffffff", "#ffffff", "#ffffff", "#e7e6e6", "#e7e6e6", "#e7e6e6"],
                ["#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff"],
                ["#ffffff", "#ffffff", "#ffffff", "#9cc563", "#9cc563", "#9cc563"],
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
                cell.set_edgecolor("#7c7c7c")
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
            # cell_text_centered_4 = table.get_celld()[(3, 4)]
            # cell_text_centered_4.set_text_props(
            #     text='Difference of means',
            #     x=1.5,
            #     y=0.5,
            #     visible=True,
            #     ha='center'
            # )
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


            

            # Mean Comparison Chart
            ax = axs["Mean Comparison"]
            ax.set_title("Means Comparison Chart", loc='center')
            # Extract means and confidence intervals
            means = []
            ci_lower = []
            ci_upper = []
            labels = []

            for key, stats_dict in stats_summary.items():
                mean = stats_dict['Mean']
                means.append(mean)
                
                # Extract CI values from string like "(1.234; 5.678)"
                ci_str = stats_dict['95% CI for $mu$']
                lower_str, upper_str = ci_str.strip('()').split('; ')
                lower = float(lower_str)
                upper = float(upper_str)
                
                ci_lower.append(lower)
                ci_upper.append(upper)
                labels.append(key)

            # # Calculate error values for errorbars
            xerr_lower = [mean - lower for mean, lower in zip(means, ci_lower)]
            xerr_upper = [upper - mean for mean, upper in zip(means, ci_upper)]
            xerr = [xerr_lower, xerr_upper]

            # # Plot horizontal errorbars
            y_positions = range(len(means))
            ax.errorbar(means, y_positions, xerr=xerr, fmt='o', markersize=3, 
                        capsize=0, linewidth=0.5, color=green_table)

            # Add labels for each point
            for i, (label, mean) in enumerate(zip(labels, means)):
                ax.text(mean, i-0.3, f"  {mean:.3f}",  fontsize=font_size)
            
            # Set y-ticks and labels
            ax.set_yticks(y_positions)
            ax.set_ylim(-0.5, len(means)-0.5)
            ax.set_yticklabels(labels, fontsize=font_size)
            ax.set_xticklabels(ax.get_xticks().round(1), fontsize=font_size)
            ax.grid(True, alpha=0.7, linewidth=0.1)
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
                        # Check if confidence intervals overlap
                        if not (ci_lower[i] <= ci_upper[j] and ci_lower[j] <= ci_upper[i]):
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
                ts_layout.append(["TS1", "TS2"])
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
            
            fig, axes = plt.subplot_mosaic(ts_layout, figsize=(8.27, 11.69))  # A4 size in inches
            #fig.subplots_adjust(hspace=0.4)  # Increase hspace to add more space between charts
            fig.suptitle(title, fontsize=16, weight='bold', y=0.94)

            # Track the min and max values for each row to set shared y-axis limits
            row_min_max = {}  # Will store {row_number: (min_value, max_value)}

            # First pass: calculate min/max values for each row
            for i, (key, values) in enumerate(self.data.values.items(), 1):
                if i <= 6:  # Only process up to 6 datasets
                    # Determine which row this plot belongs to
                    row = (i - 1) // 2
                    if row not in row_min_max:
                        row_min_max[row] = (min(values), max(values))
                    else:
                        current_min, current_max = row_min_max[row]
                        row_min_max[row] = (min(current_min, min(values)), max(current_max, max(values)))

            # Second pass: plot with shared y-axis limits
            for i, (key, values) in enumerate(self.data.values.items(), 1):
                if i <= 6:  # Only process up to 6 datasets
                    ts_key = f"TS{i}"
                    if ts_key in axes:  # Check if the subplot exists in the layout
                        ax = axes[ts_key]
                        # Create time indices for x-axis
                        time_indices = list(range(len(values)))
                        
                        # Plot the time series
                        ax.plot(time_indices, values, color='black', marker='o', linewidth=0.5)
                        ax.set_title(f"{key}", loc='center', fontsize=font_size)
                        # ax.set_xlabel("Observation", fontsize=8)
                        # ax.set_ylabel("Value", fontsize=8)
                        ax.grid(True, linestyle='--', alpha=0.7)
                        ax.tick_params(axis='both', which='major', labelsize=8)
                        
                        # Apply shared y-axis limits for plots in the same row
                        row = (i - 1) // 2
                        y_min, y_max = row_min_max[row]
                        # Add a small buffer to the limits for better visualization
                        y_range = y_max - y_min
                        buffer = y_range * 0.05  # 5% buffer
                        ax.set_ylim(y_min - buffer, y_max + buffer)


            pdf.savefig(fig)
            plt.close(fig)

        pdf_io.seek(0)
        plt.close('all')
        return pdf_io