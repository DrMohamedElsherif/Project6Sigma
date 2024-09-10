# Import required libraries
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scipy.stats
import os
from charts.basechart import BaseChart
from charts.constants import FIGURE_SIZE_DEFAULT


class Msa1chart(BaseChart):
    def process(self):
        # Define data and parameters
        title = self.chart.config.title
        data = self.chart.data["values"]
        reference = float(self.chart.config.reference)  # Reference value
        tolerance = float(self.chart.config.tolerance)  # Tolerance value
        percentage_of_tolerance = float(self.chart.config.percentage_of_tolerance)  # Percentage of tolerance

        # Define Upper and Lower Control Limits
        UCL = reference + (0.1 * tolerance)
        LCL = reference - (0.1 * tolerance)

        below_LCL = [i for i in range(len(data)) if data[i] < LCL]
        above_UCL = [i for i in range(len(data)) if data[i] > UCL]

        # Plot Run chart
        self.figure, ax1 = plt.subplots(figsize=FIGURE_SIZE_DEFAULT)
        plt.plot(data, linestyle="-", marker="o", color="black")

        ax1.plot(below_LCL, [data[i] for i in below_LCL], linestyle="", marker="s", color="red")
        ax1.plot(above_UCL, [data[i] for i in above_UCL], linestyle="", marker="s", color="red")
        ax1.axhline(reference, color="green", label="Reference")
        ax1.axhline(UCL, color="#A50021", label="UCL")
        ax1.axhline(LCL, color="#A50021", label="LCL")
        ax1.axhline(np.median(data), color="blue", linestyle="--", label="Median")

        ax1.set_title(title, fontsize=28, pad=20)
        ax1.set_xlabel("Observation")
        ax1.set_ylabel("Individual Value")
        ax1.legend(loc='upper right', framealpha=1)

        # Get basic statistics values and data frame
        mean_X = np.mean(data)
        reference_Xm = reference
        basic_statistics_df = pd.DataFrame({
            "Metric": ["Reference", "Mean", "StDev", "6 x StDev (SV)", "Tolerance (Tol)"],
            "Value": [reference, np.mean(data), np.std(data, ddof=1), 6 * np.std(data, ddof=1), tolerance]
        })

        cg = (percentage_of_tolerance*tolerance)/(3*np.std(data, ddof=1))
        cgk = (percentage_of_tolerance*tolerance-(abs(np.mean(data)-reference)))/(3*np.std(data, ddof=1))

        K = 20  # Constant used in the formula
        bias = np.mean(data) - reference
        repeatability_std_dev = np.std(data, ddof=1)
        t_statistic = abs(bias) / (repeatability_std_dev / np.sqrt(len(data)))
        p_value = scipy.stats.t.sf(np.abs(t_statistic), len(data) - 1) * 2

        var_repeatability = K / cg
        var_repeatability_and_bias = K / cgk

        capability_df = pd.DataFrame({
            "Metric": ["Cg", "Cgk", "%Var(Repeatability)", "%Var(Rep. and Bias)"],
            "Value": [cg, cgk, var_repeatability, var_repeatability_and_bias]
        })

        bias_df = pd.DataFrame({
            "Metric": ["Bias", "T", "PValue"],
            "Value": [bias, t_statistic, p_value]
        })

        # Replace the existing code for creating subplots and tables with this:

        self.figure, axs = plt.subplots(2, 1, figsize=(FIGURE_SIZE_DEFAULT[0], FIGURE_SIZE_DEFAULT[1] * 0.8),
                                        gridspec_kw={'height_ratios': [3, 1]})

        # Plot in the first row (this remains the same as before)
        axs[0].plot(data, linestyle="-", marker="o", color="black")
        axs[0].plot(below_LCL, [data[i] for i in below_LCL], linestyle="", marker="s", color="red")
        axs[0].plot(above_UCL, [data[i] for i in above_UCL], linestyle="", marker="s", color="red")
        axs[0].axhline(reference, color="green", label="Reference")
        axs[0].axhline(UCL, color="#A50021", label="UCL")
        axs[0].axhline(LCL, color="#A50021", label="LCL")
        axs[0].axhline(np.median(data), color="blue", linestyle="--", label="Median")
        axs[0].set_title(title, fontsize=28, pad=20)
        axs[0].set_xlabel("Observation")
        axs[0].set_ylabel("Individual Value")
        axs[0].legend(loc='upper right', framealpha=1)

        # Turn off axes for the tables
        axs[1].axis("off")

        # Create three subplots for tables
        gs = axs[1].get_gridspec()
        subgs = gs[1].subgridspec(1, 3)
        ax_tables = [self.figure.add_subplot(subgs[0, i]) for i in range(3)]

        # Turn off axes for all table subplots
        for ax in ax_tables:
            ax.axis("off")

        # Add titles above the tables
        ax_tables[0].set_title('Basic Statistics', fontsize=12, weight='bold')
        ax_tables[1].set_title('Bias Analysis', fontsize=12, weight='bold')
        ax_tables[2].set_title('Capability', fontsize=12, weight='bold')

        # Determine the maximum number of rows across all tables
        max_rows = max(len(basic_statistics_df), len(capability_df), len(bias_df))

        # Function to add empty rows to DataFrames to match max_rows
        def add_empty_rows_and_format(df, max_rows):
            # Format cell values to a maximum of 5 decimal places
            df = df.map(lambda x: f"{x:.8f}" if isinstance(x, (int, float)) else x)

            # Add empty rows to match max_rows
            additional_rows = max_rows - len(df)
            empty_rows = pd.DataFrame({col: [''] * additional_rows for col in df.columns})
            return pd.concat([df, empty_rows], ignore_index=True)

        # Add empty rows to DataFrames to match max_rows
        basic_statistics_df_table = add_empty_rows_and_format(basic_statistics_df, max_rows)
        capability_df_table = add_empty_rows_and_format(capability_df, max_rows)
        bias_df_table = add_empty_rows_and_format(bias_df, max_rows)

        # Add tables
        table_1 = ax_tables[0].table(cellText=basic_statistics_df_table.values, colLabels=None,
                                     cellLoc="left", loc="left", edges="closed", bbox=[0, 0, 1, 1])
        table_2 = ax_tables[1].table(cellText=bias_df_table.values, colLabels=None,
                                     cellLoc="left", loc="left", edges="closed", bbox=[0, 0, 1, 1])
        table_3 = ax_tables[2].table(cellText=capability_df_table.values, colLabels=None,
                                     cellLoc="left", loc="left", edges="closed", bbox=[0, 0, 1, 1])

        # Adjust font size for tables
        for table in [table_1, table_2, table_3]:
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            table.scale(1, 1.5)

        plt.subplots_adjust(hspace=1.5, top=0.85, bottom=0.15, left=0.15, right=0.85)
        plt.tight_layout(pad=4.0)
        plt.close()

        # Return the generated plot
        return self.figure
