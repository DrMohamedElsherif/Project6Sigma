import io
import pandas as pd
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from matplotlib.backends.backend_pdf import PdfPages
from pydantic import BaseModel, Field
from typing import List, Dict
from api.schemas import BusinessLogicException
import seaborn as sns
from .mergecells import mergecells

# check data format
class TwoTtestConfig(BaseModel):
    title: str
    alphalevel: float


class TwoTtestData(BaseModel):
    values: Dict[str, List[float]] = Field(..., min_length=1)

class TwoTtestRequest(BaseModel):
    project: str
    step: str
    config: TwoTtestConfig
    data: TwoTtestData

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
            validated_data = TwoTtestRequest(**data)
            self.project = validated_data.project
            self.step = validated_data.step
            self.config = validated_data.config
            self.data = validated_data.data
        except Exception as e:
            raise BusinessLogicException(
                error_code="error_validation",
                field=str(e),
                details={"message": f"Invalid or missing field: {str(e)}"}
            )
        
    def process(self):
        title = self.config.title
        alpha = self.config.alphalevel
        source_1 = list(self.data.values.keys())[0]
        source_2 = list(self.data.values.keys())[1]
        # Create two dataframes for each dataset
        data_keys = list(self.data.values.keys())
        df1 = pd.DataFrame(self.data.values[data_keys[0]], columns=[data_keys[0]])
        df2 = pd.DataFrame(self.data.values[data_keys[1]], columns=[data_keys[1]])
        df_combined = pd.concat([df1, df2], axis=1)

        # Perform the 2 sample t-test
        t_stat, p_value = stats.ttest_ind(df1, df2)
        t_stat = np.round(t_stat, 2)
        p_value = p_value[0]
        p_value = np.round(p_value, 4)
        if p_value < 0.0001:
            p_value = "0.000"

        # Calculate the descriptive statistics for each dataset
        sample_1_size = df1.count().astype(int)
        sample_1_mean = df1.mean().astype(float)
        sample_1_median = df1.median()
        sample_1_std = df1.std(ddof=1)
        sample_1_standard_error = sample_1_std / (sample_1_size ** 0.5)
        sample_1_lower_confidence_interval = sample_1_mean - stats.t.ppf(1 - alpha / 2, sample_1_size - 1) * sample_1_standard_error
        sample_1_lower_confidence_interval = sample_1_lower_confidence_interval.round(5)
        sample_1_upper_confidence_interval = sample_1_mean + stats.t.ppf(1 - alpha / 2, sample_1_size - 1) * sample_1_standard_error
        sample_1_upper_confidence_interval = sample_1_upper_confidence_interval.round(5)
        sample_1_95_confidence_interval = "(" + sample_1_lower_confidence_interval.astype(str) + "; " + sample_1_upper_confidence_interval.astype(str) + ")"
        sample_1_range = df1.max() - df1.min()

        sample_2_size = df2.count().astype(int)
        sample_2_mean = df2.mean().astype(float)
        sample_2_median = df2.median()
        sample_2_std = df2.std(ddof=1)
        sample_2_standard_error = sample_2_std / (sample_2_size ** 0.5)
        sample_2_lower_confidence_interval = sample_2_mean - stats.t.ppf(1 - alpha / 2, sample_2_size - 1) * sample_2_standard_error
        sample_2_lower_confidence_interval = sample_2_lower_confidence_interval.round(5)
        sample_2_upper_confidence_interval = sample_2_mean + stats.t.ppf(1 - alpha / 2, sample_2_size - 1) * sample_2_standard_error
        sample_2_upper_confidence_interval = sample_2_upper_confidence_interval.round(5)
        sample_2_95_confidence_interval = "(" + sample_2_lower_confidence_interval.astype(str) + "; " + sample_2_upper_confidence_interval.astype(str) + ")"
        sample_2_range = df2.max() - df2.min()

        # Further calculations for the first table
        mean_difference = sample_1_mean.iloc[0] - sample_2_mean.iloc[0]
        mean_difference = mean_difference.round(5)
        observed_difference = mean_difference
        # Calculate the 95% confidence interval for the observed difference
        observed_difference_standard_error = np.sqrt(
            (sample_1_std.values[0] ** 2 / sample_1_size.values[0]) + (sample_2_std.values[0] ** 2 / sample_2_size.values[0])
        )

        # Calculate the degrees of freedom for the total sample
        deg_freedom_total = df_combined.count().sum() - 2
        # Calculate the 95% confidence interval for the observed difference
        observed_difference_lower_confidence_interval = observed_difference - stats.t.ppf(1 - alpha / 2, deg_freedom_total) * observed_difference_standard_error
        observed_difference_upper_confidence_interval = observed_difference + stats.t.ppf(1 - alpha / 2, deg_freedom_total) * observed_difference_standard_error
        observed_difference_95_confidence_interval = f"({observed_difference_lower_confidence_interval.round(5)}; {observed_difference_upper_confidence_interval.round(5)})"

        # Determine if the observed difference is significant
        if observed_difference_lower_confidence_interval <= 0 <= observed_difference_upper_confidence_interval:
            difference_string = f"The mean values from ”{source_1}” and\n ”{source_2}” are not significantly different"
        else:
            difference_string = f"The mean values from ”{source_1}” and\n ”{source_2}” are significantly different"

        descriptive_statistics = {
            "Quelle": [source_1, source_2],
            "N": [sample_1_size.iloc[0], sample_2_size.iloc[0]],
            "Mean": [sample_1_mean.iloc[0].round(5), sample_2_mean.iloc[0].round(5)],
            "Median": [sample_1_median.iloc[0].round(5), sample_2_median.iloc[0].round(5)],
            "StDev": [sample_1_std.iloc[0].round(5), sample_2_std.iloc[0].round(5)],
            "SE Mean": [sample_1_standard_error.iloc[0].round(5), sample_2_standard_error.iloc[0].round(5)],
            "95% CI for mu": [sample_1_95_confidence_interval.iloc[0], sample_2_95_confidence_interval.iloc[0]],
            "Range": [sample_1_range.iloc[0].round(5), sample_2_range.iloc[0].round(5)]
        }

        # Calculate the detectable difference with sample size of N for different power levels
        power_levels = [0.6, 0.7, 0.8, 0.9]
        detectable_differences = {}

        for power in power_levels:
            effect_size = stats.norm.ppf(1 - alpha / 2) + stats.norm.ppf(power)
            pooled_std = np.sqrt((sample_1_std.values[0] ** 2 + sample_2_std.values[0] ** 2) / 2)
            detectable_difference = effect_size * pooled_std * np.sqrt(2 / sample_1_size)
            detectable_differences[int(power * 100)] = detectable_difference.iloc[0].round(5)

        # Check if the observed difference is lower than 0.6, between 0.6 and 0.9 or higher than 0.9
        if observed_difference < detectable_differences[60]:
            observed_difference_color = "#c00000"
        elif detectable_differences[60] <= observed_difference <= detectable_differences[90]:
            observed_difference_color = "#f9b002"
        else:
            observed_difference_color = "#a7c315"

        # Determine the interval of detectable differences the observed difference falls into
        if observed_difference < detectable_differences[60]:
            observed_difference_interval = "<60%"
        elif detectable_differences[60] <= observed_difference < detectable_differences[70]:
            observed_difference_interval = "60%-70%"
        elif detectable_differences[70] <= observed_difference < detectable_differences[80]:
            observed_difference_interval = "70%-80%"
        elif detectable_differences[80] <= observed_difference < detectable_differences[90]:
            observed_difference_interval = "80%-90%"
        else:
            observed_difference_interval = ">90%"

        # Create a PDF report
        pdf_io = io.BytesIO()

        with PdfPages(pdf_io) as pdf:
            # NEW PDF PAGE - T-Test results, Descriptive Statistics, Data Time Series, Chance and Detectable Difference
            fig, axs = plt.subplot_mosaic([
                ["T-Test Results", "T-Test Results"],
                ["Descriptive Statistics", "Descriptive Statistics"],
                ["TS1", "TS2"],         # Time Series Plots for each dataset
                ["Chance", "Detectable"]],    # Chance and Detectable Difference
                figsize=(8.27, 11.69))  # A4 size in inches
            # fig.subplots_adjust(hspace=0.4)  # Increase hspace to add more space between charts

            fig.suptitle(title, fontsize=16, weight='bold', y=0.94)
            
            # Define the colors + font size
            edgecolor = "#7c7c7c"
            grey = "#e7e6e6"
            green_table = "#9cc563"
            lightgreen_table = "#d6ed5f"
            font_size=7

            # T-Test Results Table
            ax = axs["T-Test Results"]
            ax.axis('off')

            # Define table data
            cellText = [
                ["Configuration", "", "Hypothesis", "", "", ""],
                [
                    "Each sample in its own column",
                    "",
                    r"$H_{0}: \mu_{1} = \mu_{2}$",
                    "t-Value",
                    "df",
                    "p-Value*"
                ],
                [
                    "Sample 1",
                    f"{source_1}",
                    r"$H_{1}: \mu_{1} \neq \mu_{2}$",
                    f"{t_stat[0]}",
                    f"{sample_1_size.iloc[0] - 1}",
                    f"{p_value}"
                ],
                [
                    "Sample 2",
                    f"{source_2}",
                    "",
                    "",
                    "",
                    ""
                ],
                [
                    "Test-Setup",
                    "Different",
                    "",
                    "",
                    "",
                    f"{observed_difference}"
                ],
                [
                    "Alpha-Level",
                    f"{alpha}",
                    "empty",
                    "",
                    "",
                    f"{observed_difference_95_confidence_interval}"
                ],
                [
                    "Interested\ndifference**",
                    "-",
                    "empty",
                    f"{difference_string}",
                    "",
                    ""
                ],
                [
                    "",
                    "","","","",""
                ]
            ]
            # Set the column widths as needed
            col_widths = [0.15, 0.15, 0.15, 0.15, 0.15, 0.15]

            # Background color for the table
            bg_colors = [
                ["#e7e6e6", "#e7e6e6", "#e7e6e6", "#e7e6e6", "#e7e6e6", "#e7e6e6"],
                ["#ffffff", "#ffffff", "#d6ed5f", "#ffffff", "#ffffff", "#ffffff"],
                ["#ffffff", "#ffffff", "#9cc563", "#ffffff", "#ffffff", "#9cc563"],
                ["#ffffff", "#ffffff", "#ffffff", "#e7e6e6", "#e7e6e6", "#e7e6e6"],
                ["#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff"],
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
            mergecells(table, [(1, 0), (1, 1)])
            mergecells(table, [(3, 2), (4, 2), (5, 2), (6, 2)])
            mergecells(table, [(3, 3), (3, 4), (3, 5)])
            mergecells(table, [(4, 3), (4, 4)])
            mergecells(table, [(5, 3), (5, 4)])
            mergecells(table, [(6, 3), (6, 4), (6, 5)])
            mergecells(table, [(7, 0), (7, 1), (7, 2), (7, 3), (7, 4), (7, 5)])

            # Fix the cells, that cannot be defined before mergecells
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
                text='Mean difference between\nsample 1 and sample 2',

                x=1.5,
                y=0.5,
                visible=True,
                ha='right'
            )
            cell_text_centered_3 = table.get_celld()[(5, 4)]
            cell_text_centered_3.set_text_props(
                text='95% CI (confidence interval)',
                x=1.5,
                y=0.5,
                visible=True,
                ha='right'
            )     
            cell_text_centered_4 = table.get_celld()[(3, 4)]
            cell_text_centered_4.set_text_props(
                text='Difference of means',
                x=1.5,
                y=0.5,
                visible=True,
                ha='center'
            )
            cell_text_small = table.get_celld()[(7, 0)]
            cell_text_small.set_text_props(
                text='* If the p-value is less than the α-level, then H0 is to be rejected and the alternative hypothesis H1 is to be accepted.\n** Optional: What difference between the two means has a practical value? (Power and sample size)',
                visible=True,
                color='grey',
                ha='right'
            )
            bold_text = [(1, 3), (1, 4), (1, 5)]
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


            # Descriptive Statistics Table
            axs["Descriptive Statistics"].axis('off')
            axs["Descriptive Statistics"].set_title("Descriptive Statistics", loc='left', pad=-50, y=1.02)
            descriptive_table_widths = [0.18, 0.06, 0.11, 0.11, 0.11, 0.11, 0.21, 0.11]
            cellText = list(zip(*descriptive_statistics.values()))
            descriptive_table = axs["Descriptive Statistics"].table(
                cellText=cellText,
                colLabels=list(descriptive_statistics.keys()),
                cellLoc='center',
                loc='center',
                colWidths=descriptive_table_widths
            )
            # Change edgecolor of table
            for cell in descriptive_table._cells.values():
                cell.set_edgecolor(edgecolor)
                cell.set_linewidth(0.5)
            
            # Set the top row color to #e7e6e6
            for cell in descriptive_table._cells:
                if cell[0] == 0:
                    descriptive_table._cells[cell].set_facecolor(grey)





            # Data Time series plot first dataset
            axs["TS1"].plot(df1, color='black', marker='o', linewidth=0.5)
            axs["TS1"].set_title("Data Time Series", loc='left')
            axs["TS1"].hlines(sample_1_mean, 0, sample_1_size, colors='grey', linestyles='dashed', alpha=0.7)
            axs["TS1"].text(0.2 , 0.1, source_1, transform=axs["TS1"].transAxes, fontsize=7, verticalalignment='top', horizontalalignment='center')

            # Mark outliers of TS1 data
            Q1_TS1 = df1.quantile(0.25)
            Q3_TS1 = df1.quantile(0.75)
            IQR_TS1 = Q3_TS1 - Q1_TS1
            lower_bound_TS1 = Q1_TS1 - 1.5 * IQR_TS1
            upper_bound_TS1 = Q3_TS1 + 1.5 * IQR_TS1

            for i, value in enumerate(df1.values):
                if value < lower_bound_TS1.values or value > upper_bound_TS1.values:
                    axs["TS1"].plot(i, value, color='red', marker='s')

            # Data Time series plot second dataset
            axs["TS2"].plot(df2, color='black', marker='o', linewidth=0.5)
            axs["TS2"].hlines(sample_2_mean, 0, sample_2_size, colors='grey', linestyles='dashed', alpha=0.7)
            axs["TS2"].set_yticks([])
            axs["TS2"].text(0.2 , 0.1, source_2, transform=axs["TS2"].transAxes, fontsize=7, verticalalignment='top', horizontalalignment='center')

            # Mark outliers of TS2 data
            Q1_TS2 = df2.quantile(0.25)
            Q3_TS2 = df2.quantile(0.75)
            IQR_TS2 = Q3_TS2 - Q1_TS2
            lower_bound_TS2 = Q1_TS2 - 1.5 * IQR_TS2
            upper_bound_TS2 = Q3_TS2 + 1.5 * IQR_TS2

            for i, value in enumerate(df2.values):
                if value < lower_bound_TS2.values or value > upper_bound_TS2.values:
                    axs["TS2"].plot(i, value, color='red', marker='s')

            # Set y-limits for both plots
            max_y = max(df1.max().values[0], df2.max().values[0])
            min_y = min(df1.min().values[0], df2.min().values[0])
            y_margin = 0.20 * (max_y - min_y)
            axs["TS1"].set_ylim(min_y - y_margin, max_y + y_margin)
            axs["TS2"].set_ylim(min_y - y_margin, max_y + y_margin)


            # Power and detected difference
            ax = axs["Chance"]
            ax.axis('off')
            ax.set_title("Power and detected difference", loc='left', pad=-50, y=1.02)

            # Define table data
            cellText = [
                ["60%", "", "90%"],
                ["", "", ""],
                [f"{detectable_differences[60]}", "", f"{detectable_differences[90]}"],
                ["Sample size", "Observed difference", ""],
                [f"{sample_1_size.iloc[0]}", f"{observed_difference}", f"{observed_difference_interval}"]
            ]

            # Determine color of the bottom right cell

            # Define background 
            bg_colors = [
                ["#e7e6e6", "#e7e6e6", "#e7e6e6"],
                ["#c00000", "#f9b002", "#a7c315"],
                ["#ffffff", "#ffffff", "#ffffff"],
                ["#e7e6e6", "#e7e6e6", "#e7e6e6"],
                ["#ffffff", "#ffffff", f"{observed_difference_color}"]
            ]

            # Create table with background colors only and remove edgecolor
            table_bg = ax.table(bbox=[0, 0, 1, 0.5], cellColours=bg_colors, colWidths=[0.18, 0.44, 0.20])
            for cell in table_bg._cells.values():
                cell.set_edgecolor("none")

            # Recreate the table layout with "none" as the color
            bg_none = [
                ["none", "none", "none"],
                ["none", "none", "none"],
                ["none", "none", "none"],
                ["none", "none", "none"],
                ["none", "none", "none"]
            ]

            # Create the table with the data + "none" as the color
            table = ax.table(
                bbox=[0, 0, 1, 0.5],
                cellText=cellText,
                cellLoc='center',
                loc='lower left',
                colWidths=[0.12, 0.17, 0.12],  # Set column widths for the left table
                cellColours=bg_none,
                edges='open'
            )

            for cell in table._cells.values():
                cell.set_linewidth(0.5)


            # Add visible edges to the table
            n_rows, n_cols = 5, 3
            for (i, j), cell in table.get_celld().items():
                # Top row: set top edge visible
                if i == 0:
                    cell.visible_edges = cell.visible_edges + "T"
                    cell.set_edgecolor("#7c7c7c")
                # Bottom row: set bottom edge visible
                if i == n_rows - 1:
                    cell.visible_edges = cell.visible_edges + "B"
                    cell.set_edgecolor("#7c7c7c")
                # 2nd to last row: set bottom edge visible
                if i == n_rows - 2:
                    cell.visible_edges = cell.visible_edges + "B"
                    cell.set_edgecolor("#7c7c7c")
                # Middle row: set the bottom edge visible
                if i == n_rows - 3:
                    cell.visible_edges = cell.visible_edges + "B"
                    cell.set_edgecolor("#7c7c7c")
                # First column: set left edge visible
                if j == 0:
                    cell.visible_edges = cell.visible_edges + "L"
                    cell.set_edgecolor("#7c7c7c")
                # Last column: set right edge visible
                if j == n_cols - 1:
                    cell.visible_edges = cell.visible_edges + "R"
                    cell.set_edgecolor("#7c7c7c")
                # Last row, first column: set bottom, left, and right edges visible
                if i == n_rows - 1 and j == 0:
                    cell.visible_edges = "BLR"
                    cell.set_edgecolor("#7c7c7c")

            for key, cell in table.get_celld().items():
                if key == (0, 0):
                    cell.set_text_props(ha='right')
                if key == (0, 2):
                    cell.set_text_props(ha='left')
                # if key == (1, 0):
                #     cell.visible_edges = 'BTL'
                if key == (2, 0):
                    cell.set_text_props(ha='right')
                if key == (2, 2):
                    cell.set_text_props(ha='left')
                # if key == (1, 2):
                #     cell.visible_edges = 'BTR'
                if key == (3, 1):
                    cell.set_text_props(ha='right')
                
            # Merge table cells
            mergecells(table, [(3, 1), (3, 2)])

            # Set the font size for the table
            table.auto_set_font_size(False)
            table.set_fontsize(font_size)

            # Detectable difference with samples of N
            ax = axs["Detectable"]
            ax.axis('off')
            # Create table data for detectable differences
            power_column = list(detectable_differences.keys())
            difference_column = list(detectable_differences.values())
            table_data = list(zip(power_column, difference_column))

            # Define table column widths
            col_widths = [0.5, 0.5]

            # Create the table
            table = ax.table(
                bbox=[0, 0, 1, 0.5],
                cellText=table_data,
                colLabels=["Power", "Difference"],
                cellLoc='center',
                loc='center',
                colWidths=col_widths
            )

            # Set the font size for the table
            table.auto_set_font_size(False)
            table.set_fontsize(font_size)

            # Change edgecolor of table
            for cell in table._cells.values():
                cell.set_edgecolor(edgecolor)
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
                figsize=(8.27, 11.69))  # A4 size in inches
            #fig.subplots_adjust(hspace=0.4)  # Increase hspace to add more space between charts
            fig.suptitle(title, fontsize=16, weight='bold', y=0.94)

            # Define gaussian function for fits
            def gaussian(x, a, mu, sigma):
                return a * np.exp(-(x-mu)**2 / (2*sigma**2))
            
            # Histogram of first dataset
            counts_1, bins_1, _ = axs["Hist1"].hist(df1.values, color='#95b92a', edgecolor='black')
            axs["Hist1"].set_title(f"Histogram of {source_1}")
            axs["Hist1"].set_ylabel("Frequency")            

            # Calculate the bin centers
            bin_center_1 = (bins_1[:-1] + np.diff(bins_1) / 2)

            x_values_to_fit_1 = np.linspace(bins_1[0], bins_1[-1], 1000)
            param_1, _ = curve_fit(gaussian, bin_center_1, counts_1)
            axs["Hist1"].plot(x_values_to_fit_1, gaussian(x_values_to_fit_1, *param_1), color='#a03130', lw=1)


            # Histogram of second dataset
            counts_2, bins_2, _ = axs["Hist2"].hist(df2.values, color='#95b92a', edgecolor='black')
            axs["Hist2"].set_title(f"Histogram of {source_2}")

            # Calculate the bin centers
            bin_center_2 = (bins_2[:-1] + np.diff(bins_2) / 2)

            x_values_to_fit_2 = np.linspace(bins_2[0], bins_2[-1], 1000)
            param_2, _ = curve_fit(gaussian, bin_center_2, counts_2, p0=(10, 10, 10))
            axs["Hist2"].plot(x_values_to_fit_2, gaussian(x_values_to_fit_2, *param_2), color='#a03130', lw=1)
            print(param_2)




            # Boxplot of both datasets
            sns.boxplot(data=df_combined.values, ax=axs["Boxplot"], palette=['#a1d111', '#a1d111'], linecolor='black', showcaps=False, linewidth=0.3, width=0.3)
            axs["Boxplot"].set_title(f"Boxplots of {source_1} and {source_2}")
            axs["Boxplot"].set_xticks([0, 1])
            axs["Boxplot"].set_xticklabels([f"{source_1}", f"{source_2}"])
            axs["Boxplot"].set_ylabel("Data")

            # Add the means to the boxplot and draw a line between them
            axs["Boxplot"].plot([0, 1], [sample_1_mean.iloc[0], sample_2_mean.iloc[0]], color='black', lw=0.5, marker='+', label='Mean')
            legend = axs["Boxplot"].legend()
            for text in legend.get_texts():
                text.set_fontsize('x-small')
            for line in legend.get_lines():
                line.set_linewidth(0)

            pdf.savefig(fig)
            plt.close(fig)

        pdf_io.seek(0)
        plt.close('all')
        return pdf_io