import io
import pandas as pd
import numpy as np
import scipy.stats as stats
from scipy.stats import norm
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from matplotlib.backends.backend_pdf import PdfPages
from pydantic import BaseModel, Field
from typing import List, Dict
from api.schemas import BusinessLogicException
import seaborn as sns
from .mergecells import mergecells


# check data format
class FtestConfig(BaseModel):
    title: str
    target_sigma: float
    alphalevel: float


class FtestData(BaseModel):
    values: Dict[str, List[float]] = Field(..., min_length=1)

class FtestRequest(BaseModel):
    project: str
    step: str
    config: FtestConfig
    data: FtestData

def bonett_confidence_interval(data, alpha):
        """
        Bonett's confidence interval for the population standard deviation.
        alpha=0.10 gives a 90% confidence interval.
        """
        n = len(data)
        s2 = np.var(data, ddof=1)  # Unbiased sample variance

        # Step 1: G = ln(s^2)
        G = np.log(s2)

        # Step 2: z-value for (1 - alpha/2)
        z = norm.ppf(1 - alpha/2)  # e.g., alpha=0.10 => z=1.645 for 90% CI

        # Step 3: Var(G) ~ 2/(n-1)
        varG = 2.0 / (n - 1)
        seG = np.sqrt(varG)  # standard error of G

        # Step 4: Confidence interval for ln(s^2)
        lower_ln = G - z * seG
        upper_ln = G + z * seG

        # Step 5: Confidence interval for s^2
        lower_s2 = np.exp(lower_ln)
        upper_s2 = np.exp(upper_ln)

        # Step 6: Confidence interval for s
        lower_s = np.sqrt(lower_s2)
        upper_s = np.sqrt(upper_s2)

        return lower_s, upper_s
    
def bonett_test(data, sigma0):
    """
    Bonett test for H0: sigma = sigma0  vs.  H1: sigma != sigma0.
    Returns Z-statistic and two-sided p-value.
    """    
    n = len(data)
    s2 = np.var(data, ddof=1)
    # G = ln(s^2 / sigma0^2)
    G = np.log(s2) - np.log(sigma0**2)

    varG = 2.0 / (n - 1)
    seG = np.sqrt(varG)

    Z = G / seG
    # Two-sided p-value
    p_value = 2 * (1 - norm.cdf(abs(Z)))
    
    return Z, p_value

def chi_square_confidence_interval(data, alpha):
    """
    Returns the (1-alpha) confidence interval for sigma using the Chi-Square distribution.
    alpha=0.10 => 90% confidence interval.
    """
    from scipy.stats import chi2
    n = len(data)
    s2 = np.var(data, ddof=1)
    df = n - 1
    
    # Chi-square critical values
    chi2_lower = chi2.ppf(alpha/2, df)      # for lower tail
    chi2_upper = chi2.ppf(1 - alpha/2, df)  # for upper tail
    
    lower_sigma = np.sqrt((df * s2) / chi2_upper)
    upper_sigma = np.sqrt((df * s2) / chi2_lower)
    
    return lower_sigma, upper_sigma


def chi_square_test(data, sigma0):
    """
    Chi-Square test for H0: sigma = sigma0  vs.  H1: sigma != sigma0.
    Returns the chi-square statistic and two-sided p-value.
    """
    n = len(data)
    s2 = np.var(data, ddof=1)
    chi_square_stat = (n - 1) * s2 / (sigma0**2)
    df = n - 1
    
    # Two-sided p-value:
    # p = P(X <= chi_square_stat) for X ~ Chi2(df)
    # But for a two-sided test we consider both tails.
    p_one_side = stats.chi2.cdf(chi_square_stat, df)
    # lower tail is p_one_side
    # upper tail is 1 - p_one_side
    # two-sided p-value is how extreme chi_square_stat is in either tail:
    if chi_square_stat < df:
        # If chi_square_stat is below the mean (df), then the lower tail is p_one_side
        p_value = 2 * p_one_side
    else:
        # If chi_square_stat is above the mean, the upper tail is (1 - p_one_side)
        p_value = 2 * (1 - p_one_side)
    
    # But ensure p_value <= 1
    p_value = min(p_value, 1.0)
    
    return chi_square_stat, df, p_value

def calculate_detectable_differences(n=50, alpha=0.10, sigma0=0.30, powers=[0.60, 0.70, 0.80, 0.90]):
    # Two-sided z critical value for alpha=0.1
    z_alpha = norm.ppf(1 - alpha/2)  # ~1.645

    # Function to get the z-value for a given power
    def z_for_power(power):
        # power = 1 - beta -> beta = 1 - power
        return norm.ppf(power)

    results = {
        "Power": [],
        "Greater": [],
        "Less": []
    }
    # Add top labels here, so that the table is correctly formatted
    results["Power"].append("\nPower")
    results["Greater"].append("")
    results["Less"].append("")
    results["Power"].append("")
    results["Greater"].append("greater")
    results["Less"].append("less")

    for p in powers:
        beta = 1 - p
        z_beta = z_for_power(p)

        # Combined z factor: (z_alpha + z_beta)
        z_factor = z_alpha + z_beta

        # sqrt(1 / [2*(n-1)])
        sqrt_factor = np.sqrt(1 / (2 * (n - 1)))

        # Calculate sigma_greater
        sigma_greater = sigma0 * np.exp(z_factor * sqrt_factor)
        diff_greater = sigma_greater - sigma0
        diff_greater = round(diff_greater, 6)

        # Calculate sigma_less
        sigma_less = sigma0 * np.exp(-z_factor * sqrt_factor)
        diff_less = sigma0 - sigma_less
        diff_less = round(diff_less, 6)
        
        results["Power"].append(f"{int(p*100)}%")
        results["Greater"].append(diff_greater)
        results["Less"].append(diff_less)

    return pd.DataFrame(results)


class Ftest:
    def __init__(self, data: dict):
        try:
            validated_data = FtestRequest(**data)
            self.project = validated_data.project
            self.step = validated_data.step
            self.config = validated_data.config
            self.data = validated_data.data
        
        except ValueError as e:
            raise BusinessLogicException(
                error_code="error_validation",
                field=str(e),
                details={"message": f"Invalid or missing field: {str(e)}"}
            )
    
    def process(self):
        title = self.config.title
        target_sigma = self.config.target_sigma
        alpha = self.config.alphalevel
        source = list(self.data.values.keys())[0]
        df1 = pd.DataFrame(self.data.values)

        # Calculate Bonett's confidence interval for the population standard deviation
        lower_bonett, upper_bonett = bonett_confidence_interval(df1[source], alpha)

        # Calculate Bonett's test for H0: sigma = target_sigma
        Z_bonett, p_value_bonett = bonett_test(df1[source], target_sigma)
        
        # Calculate the confidence interval for sigma using the Chi-Square distribution
        lower_chi, upper_chi = chi_square_confidence_interval(df1[source], alpha)

        # Calculate the Chi-Square test for H0: sigma = target_sigma
        chi_square_stat, df, p_value_chi = chi_square_test(df1[source], target_sigma)

        # Determine if the observed difference is detectable
        if lower_chi > target_sigma or upper_chi < target_sigma:
            difference_string = f"The standard deviation from ”{source}” is\n significantly different from target."
        else:
            difference_string = f"The standard deviation from ”{source}” is\nnot significantly different from target."


        # Calculate descriptive statistics
        sample_1_size = len(df1)
        sample_1_mean = df1[source].mean().round(5)
        sample_1_std = df1[source].std().round(3)
        # Calculate 95% CI for sigma (standard deviation)
        # Using chi-square distribution for confidence intervals of variance/std deviation
        chi2_lower_1 = stats.chi2.ppf(alpha/2, sample_1_size-1)
        chi2_upper_1 = stats.chi2.ppf(1-alpha/2, sample_1_size-1)
        sigma_ll_1 = np.sqrt((sample_1_size-1) * sample_1_std**2 / chi2_upper_1)
        sigma_ul_1 = np.sqrt((sample_1_size-1) * sample_1_std**2 / chi2_lower_1)
        sample_1_95_sigma = f"({sigma_ll_1:.3f}; {sigma_ul_1:.3f})"

        descriptive_statistics = {
            "Quelle": [source],
            "N": [sample_1_size],
            "Mean": [sample_1_mean],
            "StDev": [sample_1_std],
            r"95% CI for $\sigma$": [sample_1_95_sigma]
        }

        # Calculate detectable differences for given power levels
        power_levels = [0.6, 0.7, 0.8, 0.9]
        detectable_differences = calculate_detectable_differences(n=sample_1_size, alpha=alpha, sigma0=target_sigma, powers=power_levels)

        pdf_io = io.BytesIO()

        with PdfPages(pdf_io) as pdf:
            # NEW PDF PAGE - T-Test results, Descriptive Statistics, Data Time Series
            fig, axes = plt.subplot_mosaic([
                ["T-Test Results", "T-Test Results"],
                ["Descriptive Statistics", "Descriptive Statistics"],
                ["TS1", "TS1"],         # Time Series Plots for each dataset
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

            # T-Test Results Table
            ax = axes["T-Test Results"]
            ax.axis('off')

            # Define table data
            cellText = [
                ["Configuration", "", "Hypothesis", "", "", "", ""],
                ["Each sample in its own column", "", f"$H_{0}: \sigma =${target_sigma}", "Method*", "Test statistic", "df", "p-Value*"],
                ["\nTest-Setup", "\nDifferent", f"\n$H_{1}: \sigma ≠${target_sigma}", "Bonett", "-", "-", f"{p_value_bonett:.3f}"],
                ["", "", "", "Chi-Square", f"{chi_square_stat:.2f}", f"{df}", f"{p_value_chi:.3f}"],
                ["Target", f"{target_sigma}", "", "", "", "", ""],
                ["Sample", f"{source}", "", "", "", "", f"{sample_1_std:.3f}"],
                ["\nα-Level", f"\n {alpha}", "", "", "Bonett CI", "", f"({lower_bonett:.3f}; {upper_bonett:.3f})"],
                ["", f"{alpha}", "", "", "", "", f"({lower_chi:.3f}; {upper_chi:.3f})"],
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
                text=r"$\sigma$ sample",
                x=1.5,
                y=0.5,
                visible=True,
                ha='right'
            )
            cell_text_centered_3 = table.get_celld()[(5, 5)]
            cell_text_centered_3.set_text_props(
                text=f"{sample_1_std:.3f}",
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
                text='90% CI (Chi-Square)',
                x=1.5,
                y=0.5,
                visible=True,
                ha='right'
            )
            cell_text_centered_6 = table.get_celld()[(6, 5)]
            cell_text_centered_6.set_text_props(
                text=f"({lower_bonett:.3f}; {upper_bonett:.3f})",
                x=1.5,
                y=0.5,
                visible=True,
                ha='left'
            )
            cell_text_centered_7 = table.get_celld()[(7, 5)]
            cell_text_centered_7.set_text_props(
                text=f"({lower_chi:.3f}; {upper_chi:.3f})",
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

            right_text = [(0, 0), (3, 3), (4, 3)]
            for row, col in right_text:
                cell = table.get_celld()[(row, col)]
                cell.set_text_props(ha='right')



            # Descriptive Statistics Table
            ax = axes["Descriptive Statistics"]
            ax.axis('off')
            ax.set_title("Descriptive Statistics", loc='left', pad=-50, y=1.02)
            descriptive_table_widths = [0.18, 0.06, 0.11, 0.11, 0.19]
            cellText = list(zip(*descriptive_statistics.values()))
            descriptive_table = ax.table(
                cellText=cellText,
                colLabels=list(descriptive_statistics.keys()),
                cellLoc='center',
                loc='upper left',
                colWidths=descriptive_table_widths,
                bbox=[0, 0.3, 0.6, 0.15]
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



            # Data time series plot
            axes["TS1"].plot(df1, color='black', marker="o", linewidth=0.5)
            axes["TS1"].set_title("Data Time Series", loc='left')
            sample_mean = df1[source].mean()
            axes["TS1"].hlines(sample_mean, 0, len(df1) - 1, colors='grey', linestyles='dashed', label=f"Sample mean: {sample_mean:.2f}", alpha=0.7)
            # Highlight points outside the mean ± standard deviation
            Q1 = df1[source].quantile(0.25)
            Q3 = df1[source].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR

            for i, value in enumerate(df1[source]):
                if value < lower_bound or value > upper_bound:
                    axes["TS1"].plot(i, value, color='red', marker="s")  # Red color, 's' marker


            # Power and detected difference
            ax = axes["Chance"]
            ax.axis('off')
            ax.set_title("Power and Detectable Differences", loc='left', pad=-50, y=1.02)

            cellText = [
                ["60%", "", "90%"],
                ["", "", ""],
                [f"{detectable_differences['Greater'][2]}|-{detectable_differences['Less'][2]}", "", f"{detectable_differences['Greater'][5]}|-{detectable_differences['Less'][5]}"],
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
                    cell.set_text_props(ha='left')
                if key == (2, 2):
                    cell.set_text_props(ha='right')
                
                # Set edge color
                cell.set_edgecolor(edgecolor)
                cell.set_linewidth(0.5)

            ax = axes["Detectable"]
            ax.axis('off')
            # Define table data
            table_data = detectable_differences.values.tolist()

            # Define column widths
            col_widths = [0.5, 0.25, 0.25]

            # Define background colors
            bg_colors = [
                ["#e7e6e6", "#e7e6e6", "#e7e6e6"],
                ["#e7e6e6", "#e7e6e6", "#e7e6e6"],
                ["#ffffff", "#ffffff", "#ffffff"],
                ["#ffffff", "#ffffff", "#ffffff"],
                ["#ffffff", "#ffffff", "#ffffff"],
                ["#ffffff", "#ffffff", "#ffffff"]
            ]

            # Create the table with background colors
            table_bg = ax.table(bbox=[0, 0, 1, 0.5], cellColours=bg_colors)
            for cell in table_bg._cells.values():
                cell.set_edgecolor("none")

            bg_none = [
                ["none", "none", "none"],
                ["none", "none", "none"],
                ["none", "none", "none"],
                ["none", "none", "none"],
                ["none", "none", "none"],
                ["none", "none", "none"]
            ]


            table = ax.table(
                bbox=[0, 0, 1, 0.5],
                cellText=table_data,
                cellLoc='center',
                loc='center',
                colWidths=col_widths,
                cellColours=bg_none
            )
            # Set the font size for the table
            table.auto_set_font_size(False)
            table.set_fontsize(font_size)

            # Change edgecolor of table
            for cell in table._cells.values():
                cell.set_edgecolor(edgecolor)
                cell.set_linewidth(0.5)

            mergecells(table, [(0, 0), (1, 0)])
            mergecells(table, [(0, 1), (0, 2)])

            # Set the top row color to grey
            # for cell in table._cells:
            #     if cell[0] == 0 or cell[0] == 1:
            #         table._cells[cell].set_facecolor(grey)

            cell_text_right = table.get_celld()[(0, 1)]
            cell_text_right.set_text_props(
                text='Difference to target',
                x=0.5,
                y=0.5,
                visible=True,
                ha='left'
            )

            pdf.savefig(fig)
            plt.close(fig)            




            # NEW PDF PAGE - Histogram and Errorbar
            fig, axs = plt.subplot_mosaic([
                ["Hist"],
                ["Errorbar"]],
                figsize=(8.27, 11.69), gridspec_kw={'height_ratios': [3, 1]})  # A4 size in inches
            fig.subplots_adjust(hspace=0.8)  # Increase hspace to add more space between charts
            fig.suptitle(title, fontsize=16, weight='bold', y=0.94)

            # Histogram
            ax = axs["Hist"]
            ax.hist(df1[source], color='#95b92a', edgecolor='black')
            ax.set_title(f"Histogram of {source}", loc='left')
            ax.set_ylabel("Frequency")

            # Fit a gaussian function to the data
            counts, bins, _ = ax.hist(df1[source], color='#95b92a', edgecolor='black')

            # Define gaussian function
            def gaussian(x, a, mu, sigma):
                return a * np.exp(-(x-mu)**2 / (2*sigma**2))
            
            # Calculate the bin centers
            bin_center = (bins[:-1] + np.diff(bins) / 2)

            x_values_to_fit = np.linspace(bins[0], bins[-1], 1000)
            param, cov = curve_fit(gaussian, bin_center, counts)
            ax.plot(x_values_to_fit, gaussian(x_values_to_fit, *param), color='red', label='Gaussian fit')

            # Errorbar
            ax = axs["Errorbar"]
            ax.errorbar(x=sample_1_std, y=1, xerr=[[sample_1_std - lower_chi], [upper_chi - sample_1_std]], fmt='o', color='#0054a7', capsize=5)
            ax.vlines(target_sigma, 0.5, 1.5, color='#67b57a', linestyles='dashed', label=f"Target: {target_sigma}")
            ax.set_title("90% CI for the Standard Deviation", loc='center')
            ax.set_ylim(0.75, 1.25)
            ax.set_yticks([])
            ax.grid(True, axis='x', zorder=0, alpha=0.7)
            legend = ax.legend()
            for text in legend.get_texts():
                text.set_fontsize('x-small')
            # Remove the horizontal line through the target_mu marker
            for line in legend.get_lines():
                line.set_linewidth(1)

            pdf.savefig(fig)
            plt.close(fig)

        pdf_io.seek(0)
        plt.close('all')
        return pdf_io
