import io
import numpy as np
import pandas as pd
import scipy.stats as stats
import scipy.optimize as optimize
import matplotlib.pyplot as plt
import seaborn as sns
from pydantic import BaseModel, Field
from matplotlib.backends.backend_pdf import PdfPages
from typing import List, Dict
from api.schemas import BusinessLogicException
from .mergecells import mergecells

class TwoFtestConfig(BaseModel):
    title: str
    alphalevel: float

class TwoFtestData(BaseModel):
    values: Dict[str, List[float]] = Field(..., min_length=1)

class TwoFtestRequest(BaseModel):
    project: str
    step: str
    config: TwoFtestConfig
    data: TwoFtestData

def calculate_detectable_stddev_ratio(n1, n2, alpha=0.05, power_levels=[0.6, 0.7, 0.8, 0.9]):
    """Calculate detectable standard deviation ratios at various power levels."""    
    df1 = n1 - 1
    df2 = n2 - 1
    
    def objective_function(var_ratio, desired_power):
        # Critical values for rejection
        f_crit_lower = stats.f.ppf(alpha/2, df1, df2)
        f_crit_upper = stats.f.ppf(1-alpha/2, df1, df2)
        
        # Power calculation for two-sided test
        power = (1 - stats.f.cdf(f_crit_upper, df1, df2, scale=var_ratio) + 
                stats.f.cdf(f_crit_lower, df1, df2, scale=var_ratio))
        return power - desired_power
    
    results = {}
    for power in power_levels:
        try:
            var_ratio = optimize.brentq(objective_function, 1.001, 100, args=(power,))
            std_ratio = np.sqrt(var_ratio)
            percent_diff = (std_ratio - 1) * 100
            results[int(power*100)] = (std_ratio, percent_diff)
        except ValueError:
            results[int(power*100)] = (None, None)
    
    return results

class TwoFtest:
    def __init__(self, data:dict):
        try:
            validated_data = TwoFtestRequest(**data)
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
        # Create two dataframes for the two sources
        data_keys = list(self.data.values.keys())
        df1 = pd.DataFrame(self.data.values[source_1], columns=[data_keys[0]])
        df2 = pd.DataFrame(self.data.values[source_2], columns=[data_keys[1]])
        # Combine the two dataframes
        df_combined = pd.concat([df1, df2], axis=1)

        # Calculations for the F-test table
        # sample sizes
        n1, n2 = len(df1), len(df2)
        degfreedom_total = n1 + n2 - 2
        # sample variances
        s1_sq, s2_sq = np.var(df1[source_1], ddof=1), np.var(df2[source_2], ddof=1)
        # F-test statistic (ensuring F >= 1)
        if s1_sq > s2_sq:
            F_stat = s1_sq / s2_sq
            degfreedom1, degfreedom2 = n1 - 1, n2 - 1
        else:
            F_stat = s2_sq / s1_sq
            degfreedom1, degfreedom2 = n2 - 1, n1 - 1
        # p-value for the F-Test
        p_value = 2 * np.minimum(stats.f.cdf(F_stat, degfreedom1, degfreedom2), 1 - stats.f.cdf(F_stat, degfreedom1, degfreedom2))
        # Levene's test for equal variances
        levene_stat, levene_p = stats.levene(df1[source_1], df2[source_2])
        

        # Bonett's test approximation (p-value using normal approximation)
        bonett_stat = (s1_sq / s2_sq - 1) / np.sqrt(2 * (n1 - 1) / (n1 * n1) + 2 * (n2 - 1) / (n2 * n2))
        print(bonett_stat)
        bonett_p = 2 * (1 - stats.norm.cdf(abs(bonett_stat)))

        # 95% CI for Variance Ratio using Bonett’s method
        ci_lower_bonett = np.exp(np.log(F_stat) - 1.96 * np.sqrt(2 / degfreedom1 + 2 / degfreedom2))
        ci_upper_bonett = np.exp(np.log(F_stat) + 1.96 * np.sqrt(2 / degfreedom1 + 2 / degfreedom2))

        # 95% CI for Variance Ratio using Chi-Square
        chi_lower = (degfreedom1 * s1_sq) / stats.chi2.ppf(0.975, degfreedom1)
        chi_upper = (degfreedom1 * s1_sq) / stats.chi2.ppf(0.025, degfreedom1)

        # 95% CI for Standard Deviation Ratio using Bonett's method
        ci_lower_sd_bonett = np.sqrt(ci_lower_bonett)
        ci_upper_sd_bonett = np.sqrt(ci_upper_bonett)

        # 95% CI for Standard Deviation Ratio using Chi-Square (WIRD CHI ODER LEVENE VERWENDET???)
        # ci_lower_sd_chi = np.sqrt(chi_lower)
        # ci_upper_sd_chi = np.sqrt(chi_upper)

        # 95% CI for Standard Deviation Ratio using Levene's test
        # Approximate using square root of F-statistic CI bounds
        ci_lower_sd_levene = np.sqrt(F_stat / stats.f.ppf(0.975, degfreedom1, degfreedom2))
        ci_upper_sd_levene = np.sqrt(F_stat / stats.f.ppf(0.025, degfreedom1, degfreedom2))

        #Determine if the observed difference is detectable using f-test
        # Determine if the observed difference is detectable using f-test
        ratio_sigma = np.sqrt(F_stat)

        # Check if the confidence interval for sigma ratio includes 1.0
        # Using Bonett CI as it's more robust for non-normal distributions
        # Determine if the observed difference is detectable using F-test
        is_significant = not (ci_lower_sd_bonett <= 1.0 <= ci_upper_sd_bonett)
        
        # Create a descriptive string about the difference
        difference_string = (
            f"The standard deviation from ”{source_1}” is\n significantly different from ”{source_2}”."
            if is_significant else
            f"The standard deviation from ”{source_1}” is\nnot significantly different from ”{source_2}”."
        )


        # Calculations for the descriptive statistics table
        # Sample 1
        sample_1_size = len(df1)
        sample_1_mean = df1[source_1].mean().round(5)
        sample_1_std = df1[source_1].std().round(3)
        # Calculate 95% CI for sigma (standard deviation)
        # Using chi-square distribution for confidence intervals of variance/std deviation
        chi2_lower_1 = stats.chi2.ppf(alpha/2, sample_1_size-1)
        chi2_upper_1 = stats.chi2.ppf(1-alpha/2, sample_1_size-1)
        sigma_ll_1 = np.sqrt((sample_1_size-1) * sample_1_std**2 / chi2_upper_1)
        sigma_ul_1 = np.sqrt((sample_1_size-1) * sample_1_std**2 / chi2_lower_1)
        sample_1_95_sigma = f"({sigma_ll_1:.3f}; {sigma_ul_1:.3f})"

        # Sample 2
        sample_2_size = len(df2)
        sample_2_mean = df2[source_2].mean().round(5)
        sample_2_std = df2[source_2].std().round(3)
        # Calculate 95% CI for sigma (standard deviation)
        # Using chi-square distribution for confidence intervals of variance/std dev
        chi2_lower_2 = stats.chi2.ppf(alpha/2, sample_2_size-1)
        chi2_upper_2 = stats.chi2.ppf(1-alpha/2, sample_2_size-1)
        sigma_ll_2 = np.sqrt((sample_2_size-1) * sample_2_std**2 / chi2_upper_2)
        sigma_ul_2 = np.sqrt((sample_2_size-1) * sample_2_std**2 / chi2_lower_2)
        sample_2_95_sigma = f"({sigma_ll_2:.3f}; {sigma_ul_2:.3f})"

        # Standard deviation ratio

        # Create descriptive statistics table data
        desriptive_statistics = {
            "Quelle": [source_1, source_2],
            "N": [sample_1_size, sample_2_size],
            "Mean": [sample_1_mean, sample_2_mean],
            "StDev": [sample_1_std, sample_2_std],
            r"95% CI $\sigma$": [sample_1_95_sigma, sample_2_95_sigma]
        }

        # Calculate detectable difference in standard deviation ratio
        detectable_differences = calculate_detectable_stddev_ratio(sample_1_size, sample_2_size, alpha=alpha)

        pdf_io = io.BytesIO()

        with PdfPages(pdf_io) as pdf:
            # NEW PDF PAGE - T-Test results, Descriptive Statistics, Data Time Series
            fig, axes = plt.subplot_mosaic([
                ["T-Test Results", "T-Test Results"],
                ["Descriptive Statistics", "Descriptive Statistics"],
                ["TS1", "TS2"],         # Time Series Plots for each dataset
                ["Chance", "Detectable"]],    # Chance and Detectable Difference
                figsize=(8.27, 11.69))  # A4 size in inches
            #fig.subplots_adjust(hspace=0.4)  # Increase hspace to add more space between charts
            fig.suptitle(title, fontsize=16, weight='bold', y=0.94)

            # Define the colors + font size
            edgecolor = "#7c7c7c"
            grey = "#e7e6e6"
            green_table = "#9cc563"
            lightgreen_table = "#d6ed5f"
            font_size=7

            # T-Test Results
            ax = axes["T-Test Results"]
            ax.axis("off")
            # Define table data
            cellText = [
                ["Configuration", "", "Hypothesis", "", "", "", ""],
                ["Each sample in its own column", "", f"$H_{0}: \sigma_{1}$ / $\sigma_{2}$ = 1", "Method*", "Test statistic", "df", "p-Value*"],
                ["\nTest-Setup", "\nDifferent", f"\n$H_{0}: \sigma_{1}$ / $\sigma_{2}$ ≠ 1", "Bonett", f"{bonett_stat:.2f}", "-", f"{bonett_p:.3f}"],
                ["", "", "", "Levene", f"{levene_stat:.2f}", f"{degfreedom_total}", f"{levene_p:.3f}"],
                ["Sample 1", f"{source_1}", "", "", "", "", ""],
                ["Sample 2", f"{source_2}", "", "", "", "", ""],
                ["\nα-Level", f"\n {alpha}", "", "", "Bonett CI", "", f"({ci_lower_sd_bonett};{ci_upper_sd_bonett})"],
                ["", "", "", "", "", "", ""],
                ["Interested\ndifference**", "-", "", f"{difference_string}", "", "", ""],
                ["", "", "", "", "", "", ""]
            ]
            # Define column widths
            col_widths = [0.15, 0.2, 0.15, 0.1, 0.15, 0.1, 0.15]
            # Background color for the table
            bg_colors = [
                ["#e7e6e6", "#e7e6e6", "#e7e6e6", "#e7e6e6", "#e7e6e6", "#e7e6e6", "#e7e6e6"],
                ["#ffffff", "#ffffff", lightgreen_table, grey, grey, grey, grey],
                ["#ffffff", "#ffffff", green_table, "#ffffff", "#ffffff", "#ffffff", lightgreen_table],
                ["#ffffff", "#ffffff", green_table, "#ffffff", "#ffffff", "#ffffff", lightgreen_table],
                ["#ffffff", "#ffffff", "#ffffff", grey, grey, grey, grey],
                ["#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff"],
                ["#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff"],
                ["#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff"],
                ["#ffffff", "#ffffff", "#ffffff", lightgreen_table, lightgreen_table, lightgreen_table, lightgreen_table],
                ["#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff"]
            ]

            # Create table with background colors only and remove edgecolor
            table_bg = ax.table(bbox=[0, 0, 1, 1], cellColours=bg_colors, colWidths=col_widths)
            for cell in table_bg._cells.values():
                cell.set_edgecolor("none")

            # Adjust row heights for background color table
            row_heights = {2: 0.05, 3: 0.05, 6: 0.05, 7: 0.05, 8: 0.1, 9: 0.1}
            for row, height in row_heights.items():
                for col in range(7):
                    table_bg[(row, col)].set_height(height)

            # Recreate the table layout with "none" as the color
            bg_none = [
                ["none", "none", "none", "none", "none", "none", "none"],
                ["none", "none", "none", "none", "none", "none", "none"],
                ["none", "none", "none", "none", "none", "none", "none"],
                ["none", "none", "none", "none", "none", "none", "none"],
                ["none", "none", "none", "none", "none", "none", "none"],
                ["none", "none", "none", "none", "none", "none", "none"],
                ["none", "none", "none", "none", "none", "none", "none"],
                ["none", "none", "none", "none", "none", "none", "none"],
                ["none", "none", "none", "none", "none", "none", "none"],
                ["none", "none", "none", "none", "none", "none", "none"]
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
            mergecells(table, [(0, 0), (0, 1)]) #Passt
            mergecells(table, [(0, 3), (0, 4), (0, 5), (0, 6)]) #Passt
            mergecells(table, [(2, 0), (3, 0)]) #Passt
            mergecells(table, [(2, 1), (3, 1)]) #Passt
            mergecells(table, [(1, 0), (1, 1)]) #Passt
            mergecells(table, [(2, 2), (3, 2)])
            mergecells(table, [(6, 0) , (7, 0)])
            mergecells(table, [(6, 1) , (7, 1)])
            mergecells(table, [(4, 2), (5, 2), (6, 2), (7, 2), (8, 2)])
            mergecells(table, [(4, 3), (4, 4), (4, 5), (4, 6)])
            mergecells(table, [(5, 3), (5, 4)])
            mergecells(table, [(5, 5), (5, 6)])
            mergecells(table, [(6, 3), (6, 4)])
            mergecells(table, [(6, 5), (6, 6)])
            mergecells(table, [(7, 3), (7, 4)])
            mergecells(table, [(7, 5), (7, 6)])
            mergecells(table, [(8, 3), (8, 4), (8, 5), (8, 6)])
            mergecells(table, [(9, 0), (9, 1), (9, 2), (9, 3), (9, 4), (9, 5), (9, 6)])

            # Fix the cells, that cannot be defined before mergecells
            table.get_celld()[9, 0].set_fontsize(5)
            
            
            for row, height in row_heights.items():
                for col in range(7):
                    table[(row, col)].set_height(height)

            # Add text to the table
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
                text=r"$\sigma_{1}$ / $\sigma_{2}$ ",
                x=1.5,
                y=0.5,
                visible=True,
                ha='right'
            )
            cell_text_centered_3 = table.get_celld()[(5, 5)]
            cell_text_centered_3.set_text_props(
                text=f"{ratio_sigma:.5f}",
                x=1.5,
                y=0.5,
                visible=True,
                ha='right'
            )
            cell_text_centered_4 = table.get_celld()[(6, 4)]
            cell_text_centered_4.set_text_props(
                text='90% CI (Bonett)',
                x=1.5,
                y=0.5,
                visible=True,
                ha='right'
            )
            cell_text_centered_5 = table.get_celld()[(7, 4)]
            cell_text_centered_5.set_text_props(
                text='90% CI (Levene)',
                x=1.5,
                y=0.5,
                visible=True,
                ha='right'
            )
            cell_text_centered_6 = table.get_celld()[(6, 5)]
            cell_text_centered_6.set_text_props(
                text=f"({ci_lower_sd_bonett:.3f};{ci_upper_sd_bonett:.3f})",
                x=1.5,
                y=0.5,
                visible=True,
                ha='left'
            )
            cell_text_centered_7 = table.get_celld()[(7, 5)]
            cell_text_centered_7.set_text_props(
                text=f"({ci_lower_sd_levene:.3f};{ci_upper_sd_levene:.3f})",
                x=1.5,
                y=0.5,
                visible=True,
                ha='left'
            )
            cell_text_small = table.get_celld()[(9, 0)]
            cell_text_small.set_text_props(
                text= '* Method: The Bonett method is valid for any continuous distribution, while the chi-square method is valid only for the normal distribution.\n** If the p-value is less than the α-level, then H0 is to be rejected and the alternative hypothesis H1 is to be accepted\n*** Optional: What difference between the two standard deviations has a practical value? (Power and sample size)',
                visible=True,
                color='grey',
                ha='left'
            )
            bold_text = [(1, 3), (1, 4), (1, 5)]
            for row, col in bold_text:
                cell = table.get_celld()[(row, col)]
                cell.set_text_props(weight='bold')

            left_text = [(1, 0), (5, 3), (6, 3), (8, 3)]
            for row, col in left_text:
                cell = table.get_celld()[(row, col)]
                cell.set_text_props(ha='left')

            right_text = [(0, 0), (4, 3)]
            for row, col in right_text:
                cell = table.get_celld()[(row, col)]
                cell.set_text_props(ha='right')



            # Descriptive Statistics
            ax = axes["Descriptive Statistics"]
            ax.axis("off")
            ax.set_title("Descriptive Statistics", loc="left", pad=-50, y=1.02)
            descriptive_table_widths = [0.18, 0.06, 0.11, 0.11, 0.19]
            cellText = list(zip(*desriptive_statistics.values()))
            descriptive_table = ax.table(
                cellText=cellText,
                colLabels=list(desriptive_statistics.keys()),
                cellLoc="center",
                loc="upper left",
                colWidths=descriptive_table_widths,
                bbox=[0, 0.3, 0.6, 0.3]
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




            # Time Series Plots
            # Time Series 1
            ax = axes["TS1"]
            ax.plot(df1, color='black', marker='o', linewidth=0.5)
            ax.set_title("Data Time Series", loc='left')
            ax.hlines(sample_1_mean, 0, sample_1_size, colors='grey', linestyles='dashed', alpha=0.7)
            ax.text(0.2, 0.1, source_1, transform=ax.transAxes, fontsize=font_size, verticalalignment='top', horizontalalignment='center')

            # Mark outliers of TS1 data
            Q1_TS1 = df1.quantile(0.25)
            Q3_TS1 = df1.quantile(0.75)
            IQR_TS1 = Q3_TS1 - Q1_TS1
            lower_bound_TS1 = Q1_TS1 - 1.5 * IQR_TS1
            upper_bound_TS1 = Q3_TS1 + 1.5 * IQR_TS1

            for i, value in enumerate(df1.values):
                if value < lower_bound_TS1.values or value > upper_bound_TS1.values:
                    ax.plot(i, value, color='red', marker='s')

            # Time Series 2
            ax = axes["TS2"]
            ax.plot(df2, color='black', marker='o', linewidth=0.5)
            ax.hlines(sample_2_mean, 0, sample_2_size, colors='grey', linestyles='dashed', alpha=0.7)
            ax.set_yticks([])
            ax.text(0.2, 0.1, source_2, transform=ax.transAxes, fontsize=font_size, verticalalignment='top', horizontalalignment='center')

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
            y_margin = 0.2 * (max_y - min_y)
            axes["TS1"].set_ylim(min_y - y_margin, max_y + y_margin)
            axes["TS2"].set_ylim(min_y - y_margin, max_y + y_margin)




            # Chance of Detecting a Difference table
            ax = axes["Chance"]
            ax.axis("off")
            ax.set_title("What is the chance of detecting a difference?", loc="center", pad=-50, y=1.0, fontsize=font_size)

            cellText = [
                ["60%", "", "90%"],
                ["", "", ""],
                [f"{detectable_differences[60][1]:.1f}%", "% Difference", f"{detectable_differences[90][1]:.1f}%"],
            ]

            bg_colors = [
                ["#e7e6e6", "#e7e6e6", "#e7e6e6"],
                ["#c00000", "#f9b002", "#a7c315"],
                ["#ffffff", "#ffffff", "#ffffff"]
            ]

            table_bg = ax.table(bbox=[0, 0, 1, 0.5], cellColours=bg_colors, colWidths=[0.18, 0.44, 0.20])
            for cell in table_bg._cells.values():
                cell.set_edgecolor("none")

            bg_none = [
                ["none", "none", "none"],
                ["none", "none", "none"],
                ["none", "none", "none"]
            ]

            table = ax.table(
                bbox=[0, 0, 1, 0.5],
                cellText=cellText,
                cellLoc='center',
                loc='center',
                colWidths=[0.12, 0.17, 0.12],
                cellColours=bg_none
            )

            # Set table font size
            table.auto_set_font_size(False)
            table.set_fontsize(font_size)

            # Add only outer edges to the table
            for key, cell in table.get_celld().items():
                row, col = key
                
                # Remove all edges first
                cell.visible_edges = ""
                
                # Add edges only for cells on the outside
                if row == 0:  # Top row
                    cell.visible_edges += "T"
                # if row == 2:  # Bottom row
                #     cell.visible_edges += "B"
                if col == 0:  # Left column
                    cell.visible_edges += "L"
                if col == 2:  # Right column
                    cell.visible_edges += "R"
                    
                # Adjust text positioning
                if key == (0, 0):
                    cell.set_text_props(ha='right')
                if key == (0, 2):
                    cell.set_text_props(ha='left')
                if key == (2, 0):
                    cell.set_text_props(ha='right')
                if key == (2, 2):
                    cell.set_text_props(ha='left')
                
                # Set edge color
                cell.set_edgecolor(edgecolor)
                cell.set_linewidth(0.5)




            # Difference detectable with sample size N table
            ax = axes["Detectable"]
            ax.axis("off")
            table_data = [
                ["% Difference", "Power"],
                [f"{detectable_differences[60][1]:.1f}%", "60%"],
                [f"{detectable_differences[70][1]:.1f}%", "70%"],
                [f"{detectable_differences[80][1]:.1f}%", "80%"],
                [f"{detectable_differences[90][1]:.1f}%", "90%"]
            ]

            table = ax.table(
                bbox=[0, 0, 1, 0.5],
                cellText=table_data,
                cellLoc='center',
                loc='center'
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

            # NEW PDF PAGE - Histogram and Errorbar
            fig, axs = plt.subplot_mosaic([
                ["Hist1"],
                ["Hist2"],
                ["Errorbar1"],
                ["Errorbar2"],
                ["Boxplots"]],
                figsize=(8.27, 11.69), gridspec_kw={'height_ratios': [3, 3, 1, 1, 1]})  # A4 size in inches
            fig.subplots_adjust(hspace=0.8)  # Increase hspace to add more space between charts
            fig.suptitle(title, fontsize=16, weight='bold', y=0.94)

            # Plot for the Histograms
            # Histogram 1
            ax = axs["Hist1"]
            ax.hist(df1[source_1], color='#95b92a', edgecolor='black', zorder=3, label=f"{source_1}")
            ax.set_title(f"{source_1}")
            ax.set_ylabel("Frequency")
            ax.set_xticks([])
            ax.grid(True, axis='y', zorder=0, alpha=0.7)

            # Histogram 2
            ax = axs["Hist2"]
            ax.hist(df2[source_2], color='#95b92a', edgecolor='black', zorder=3, label=f"{source_2}")
            ax.set_title(f"{source_2}")
            ax.set_ylabel("Frequency")
            ax.grid(True, axis='y', zorder=0, alpha=0.7)
            ax.set_position([0.125, 0.5, 0.775, 0.2])  # Adjust the position to move it closer to the first plot

            # Set the same x-limits for both histograms
            hist_min = min(df1[source_1].min(), df2[source_2].min())
            hist_max = max(df1[source_1].max(), df2[source_2].max())
            hist_margin = (hist_max - hist_min) * 0.1
            axs["Hist1"].set_xlim(hist_min - hist_margin, hist_max + hist_margin)
            axs["Hist2"].set_xlim(hist_min - hist_margin, hist_max + hist_margin)

            # Set the same y-limits for both histograms
            hist_max = max(axs["Hist1"].get_ylim()[1], axs["Hist2"].get_ylim()[1])
            axs["Hist1"].set_ylim(0, hist_max)
            axs["Hist2"].set_ylim(0, hist_max)

            # Plot for the Errorbars
            # Bonett and Levene Errorbars
            ax = axs["Errorbar1"]
            ax.errorbar(x=ratio_sigma, y=1, xerr=[[ratio_sigma - ci_lower_sd_bonett], [ci_upper_sd_bonett - ratio_sigma]], fmt='o', color='#95b92a', capsize=3, lw=0.7, markersize=3)
            ax.errorbar(x=ratio_sigma, y=0, xerr=[[ratio_sigma - ci_lower_sd_levene], [ci_upper_sd_levene - ratio_sigma]], fmt='o', color='#95b92a', capsize=3, lw=0.7, markersize=3)
            ax.vlines(1, -1, 2, colors='grey', linestyles='dashed', alpha=0.7)
            ax.set_ylim(-0.9, 1.9)
            labels = [item.get_text() for item in ax.get_yticklabels()]
            print(labels)
            labels[1] = 'Levene'
            labels[2] = 'Bonett'
            ax.set_yticklabels(labels)
            ax.grid(True, axis='x', zorder=0, alpha=0.7)
            ax.set_position([0.3, 0.4, 0.6, 0.05])

            # Samples sigma Errorbars
            ax = axs["Errorbar2"]
            ax.errorbar(x=sample_2_std, y=1, xerr=[[sample_2_std - sigma_ll_2], [sigma_ul_2 - sample_2_std]], fmt='o', color='#95b92a', capsize=3, lw=0.7, markersize=3)
            ax.errorbar(x=sample_1_std, y=0, xerr=[[sample_1_std - sigma_ll_1], [sigma_ul_1 - sample_1_std]], fmt='o', color='#95b92a', capsize=3, lw=0.7, markersize=3)
            ax.set_ylim(-0.9, 1.9)
            labels = [item.get_text() for item in ax.get_yticklabels()]
            labels[1] = f'{source_1}'
            labels[2] = f'{source_2}'
            for label in ax.get_xticklabels()[1::2]:
                label.set_visible(False)
            ax.set_yticklabels(labels)
            ax.grid(True, axis='x', zorder=0, alpha=0.7)
            ax.set_position([0.3, 0.3, 0.6, 0.05])

            # Boxplots
            ax = axs["Boxplots"]
            sns.boxplot(data=df_combined.values, ax=ax, palette=['#a1d111', '#a1d111'], linecolor='black', showcaps=False, linewidth=0.5, width=0.5, orient='h')
            ax.set_ylim(-0.9, 1.9)
            labels = [item.get_text() for item in ax.get_yticklabels()]
            print(labels)
            labels[0] = f'{source_1}'
            labels[1] = f'{source_2}'
            ax.set_yticklabels(labels)
            ax.grid(True, axis='x', zorder=0, alpha=0.7)
            ax.set_position([0.3, 0.15, 0.6, 0.1])

            pdf.savefig(fig)
            plt.close(fig)

        pdf_io.seek(0)
        plt.close('all')
        return pdf_io