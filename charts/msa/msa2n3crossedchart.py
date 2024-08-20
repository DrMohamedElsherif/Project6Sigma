# Import required libraries
import io
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.api as sm
from matplotlib.backends.backend_pdf import PdfPages
from statsmodels.formula.api import ols

from charts.basechart import BaseChart


class Msa2n3crossedchart(BaseChart):
    def process(self):
        # Extracting data directly from the API response
        title = self.chart.config.title
        values = self.chart.data["values"]  # Values (measurements)
        parts = self.chart.data["parts"]  # Part IDs

        # Check if the chart has operators else use devices else throw an error
        if "operators" in self.chart.data:
            operators = self.chart.data["operators"]
        elif "devices" in self.chart.data:
            operators = self.chart.data["devices"]
        else:
            raise ValueError("The chart data must have either 'operators' or 'devices'")

        label = self.chart.config.labelx  # Label (Operator or Device)

        # Create DataFrame from the API data
        data = pd.DataFrame({
            "Part": parts,
            "Operator": operators,
            "Value": values
        })

        # Sort data frame by Part and Operator
        data = data.sort_values(["Part", "Operator"])

        # Reset index
        data.reset_index(inplace=True, drop=True)

        # Get operators count
        operators_count = data["Operator"].nunique()

        # Get parts count
        parts_count = data["Part"].nunique()

        # Get replicates by part
        replicates_per_part = len(data.loc[(data["Part"] == parts[0])]["Part"]) / data.loc[(data["Part"] == parts[0])][
            "Operator"].nunique()

        # Calculate "Replicate" column
        data["Replicate"] = list(np.arange(1, replicates_per_part + 1)) * (int(len(data["Part"]) / replicates_per_part))

        # Calculate "Part Measurement" column
        data["Part Measurement"] = list(np.arange(1, data["Part"].value_counts().iloc[0] + 1)) * (
            int(len(data["Part"]) / data["Part"].value_counts().iloc[0]))

        # Group data frame by Part, obtain mean and reset index
        data_grouped_by_part = data[["Part", "Value"]].groupby(["Part"]).mean().reset_index()

        # Group data frame by Operator, obtain mean and reset index
        data_grouped_by_operator = data[["Operator", "Value"]].groupby(["Operator"]).mean().reset_index()

        # Group data frame by Operator and Part, obtain mean and reset index
        data_grouped_by_operator_and_part = data.groupby(["Operator", "Part"]).mean()[["Value"]].reset_index()

        # Calculate mean, max and min values
        mean_value = round(data.groupby(["Operator", "Part"]).mean()[["Value"]].reset_index()["Value"], 2)
        max_value = data.groupby(["Operator", "Part"]).max()[["Value"]].reset_index()["Value"]
        min_value = data.groupby(["Operator", "Part"]).min()[["Value"]].reset_index()["Value"]

        # Get data frame by operator and part
        data_grouped_by_operator_and_part_stats = pd.DataFrame({
            "Operator": data_grouped_by_operator_and_part["Operator"],
            "Part": data_grouped_by_operator_and_part["Part"],
            "Mean": mean_value,
            "Max": max_value,
            "Min": min_value
        })

        # Calculate "Range" column
        data_grouped_by_operator_and_part_stats["Range"] = abs(
            data_grouped_by_operator_and_part_stats["Max"] - data_grouped_by_operator_and_part_stats["Min"])

        # Create a PDF file to save all the plots
        pdf_io = io.BytesIO()

        # Perform two-way ANOVA and get results
        (model_2way_interaction_results, model_2way_no_interaction_results, gage_rr_var_comp_no_interaction_df,
         gage_evaluation_df) = self._perform_two_way_anova(data, operators_count, parts_count, replicates_per_part)

        with PdfPages(pdf_io) as pdf:
            # NEW PDF PAGE - Value by Part, Value by Operator, Part * Operator Interaction
            fig, axes = plt.subplots(3, 1, figsize=(8.27, 11.69))  # A4 size in inches
            fig.subplots_adjust(hspace=0.4)  # Increase hspace to add more space between charts
            fig.suptitle(title, fontsize=16, weight='bold', y=0.95)
            fig.text(0.5, s="MSA - 2 Crossed Analysis", ha="center", va="center", fontsize=11, y=0.92,
                     weight="semibold")

            # Plot Value by Part Scatter Plot
            self._plot_value_by_part(data, data_grouped_by_part, axes[0])

            # Plot Value by Operator Boxplot
            self._plot_value_by_operator(data, label, data_grouped_by_operator, axes[1])

            # Plot Part by Operator Interaction Scatter Plot
            self._plot_part_operator_interaction(data_grouped_by_operator_and_part, label, axes[2])

            pdf.savefig(fig)  # Save the current page
            plt.close(fig)

            # NEW PDF PAGE - X-bar and R Charts by Operator
            operators = data_grouped_by_operator_and_part_stats["Operator"].unique()
            for i in range(0, len(operators), 2):
                fig = plt.figure(figsize=(8.27, 11.69))  # A4 size in inches
                gs = fig.add_gridspec(4, 1, hspace=0.6)  # Adjust hspace for vertical spacing

                for j in range(2):
                    if i + j < len(operators):
                        operator = operators[i + j]
                        operator_data = data_grouped_by_operator_and_part_stats[
                            data_grouped_by_operator_and_part_stats["Operator"] == operator]
                        ax_xbar = fig.add_subplot(gs[j * 2])
                        ax_r = fig.add_subplot(gs[j * 2 + 1])
                        self._plot_xbar_chart_by_operator(operator_data, label, ax_xbar)
                        self._plot_r_chart_by_operator(operator_data, label, ax_r)
                    else:
                        # Hide unused subplots
                        ax_xbar = fig.add_subplot(gs[j * 2])
                        ax_r = fig.add_subplot(gs[j * 2 + 1])
                        ax_xbar.axis('off')
                        ax_r.axis('off')

                pdf.savefig(fig)  # Save the current page
                plt.close(fig)

            # NEW PDF PAGE - Tables
            fig, axes = plt.subplots(4, 1, figsize=(8.27, 11.69))  # A4 size in inches
            fig.subplots_adjust(hspace=0.5)

            edge_color = '#D3D3D3'
            desired_height = 0.12
            font_size = 7

            # Nachher: Die "Source"-Spalte bleibt erhalten und wird nicht als Index gesetzt
            model_2way_interaction_results.reset_index(inplace=True)
            model_2way_no_interaction_results.reset_index(inplace=True)
            gage_rr_var_comp_no_interaction_df.reset_index(inplace=True)
            gage_evaluation_df.reset_index(inplace=True)

            # Runden der Werte auf 6 Nachkommastellen
            model_2way_interaction_results = model_2way_interaction_results.round(6)
            model_2way_no_interaction_results = model_2way_no_interaction_results.round(6)
            gage_rr_var_comp_no_interaction_df = gage_rr_var_comp_no_interaction_df.round(6)
            gage_evaluation_df = gage_evaluation_df.round(6)

            # Add tables to subplots
            axes[0].axis('off')
            axes[0].set_title("Two-Way ANOVA Table With Interaction", pad=0)
            table_0 = axes[0].table(cellText=model_2way_interaction_results.values, cellLoc="left",
                                    colLabels=model_2way_interaction_results.columns, loc='center')
            table_0.auto_set_font_size(False)
            table_0.set_fontsize(font_size)
            table_0.scale(1, 2)  # Adjust scaling if needed
            for key, cell in table_0.get_celld().items():
                cell.set_linewidth(1)
                cell.set_edgecolor(edge_color)
                cell.set_height(desired_height)

            # Two-Way ANOVA Table Without Interaction
            axes[1].axis('off')
            axes[1].set_title("Two-Way ANOVA Table Without Interaction")
            table_1 = axes[1].table(cellText=model_2way_no_interaction_results.values, cellLoc="left",
                                    colLabels=model_2way_no_interaction_results.columns, loc='center')
            table_1.auto_set_font_size(False)
            table_1.set_fontsize(font_size)
            table_1.scale(1, 2)  # Adjust scaling if needed
            for key, cell in table_1.get_celld().items():
                cell.set_linewidth(1)
                cell.set_edgecolor(edge_color)
                cell.set_height(desired_height)

            # Gage R&R Components of Variation
            axes[2].axis('off')
            axes[2].set_title("Gage R&R Components of Variation")
            table_2 = axes[2].table(cellText=gage_rr_var_comp_no_interaction_df.values, cellLoc="left",
                                    colLabels=gage_rr_var_comp_no_interaction_df.columns, loc='center')
            table_2.auto_set_font_size(False)
            table_2.set_fontsize(font_size)
            table_2.scale(1, 2)  # Adjust scaling if needed
            for key, cell in table_2.get_celld().items():
                cell.set_linewidth(1)
                cell.set_edgecolor(edge_color)
                cell.set_height(desired_height)

            # Gage Evaluation
            axes[3].axis('off')
            axes[3].set_title("Gage Evaluation")
            table_3 = axes[3].table(cellText=gage_evaluation_df.values, cellLoc="left",
                                    colLabels=gage_evaluation_df.columns, loc='center')
            table_3.auto_set_font_size(False)
            table_3.set_fontsize(font_size)
            table_3.scale(1, 2)  # Adjust scaling if needed
            for key, cell in table_3.get_celld().items():
                cell.set_linewidth(1)
                cell.set_edgecolor(edge_color)
                cell.set_height(desired_height)

            pdf.savefig(fig)
            plt.close(fig)

            # NEW PDF PAGE - Two-way ANOVA
            fig, ax = plt.subplots(1, 1, figsize=(8.27, 11.69))  # A4 size in portrait
            fig.subplots_adjust(bottom=0.20, top=0.85)  # Increase bottom space and headspace

            # Perform two-way ANOVA with and without interaction and plot the results
            self._perform_two_way_anova(data, operators_count, parts_count,
                                        replicates_per_part, ax, pdf)

            pdf.savefig(fig)
            plt.close(fig)

        pdf_io.seek(0)
        return pdf_io

    def _plot_value_by_part(self, data, data_grouped_by_part, ax):
        ax.scatter(x=data["Part"], y=data["Value"], color="grey")
        ax.scatter(x=data_grouped_by_part["Part"], y=data_grouped_by_part["Value"], color="#7DA7D9", facecolors="none")
        ax.plot(data_grouped_by_part["Part"], data_grouped_by_part["Value"], color="#7DA7D9")
        ax.set_xticks(list(data_grouped_by_part["Part"]))
        ax.set_title("Value by Part")
        ax.set_xlabel("Part")
        ax.grid(color="lightgrey")

    def _plot_value_by_operator(self, data, label, data_grouped_by_operator, ax):
        sns.boxplot(x="Operator", y="Value", data=data, color="#7DA7D9", width=0.4, ax=ax)
        ax.plot(data_grouped_by_operator["Operator"], data_grouped_by_operator["Value"], color="grey")
        ax.scatter(x=data_grouped_by_operator["Operator"], y=data_grouped_by_operator["Value"], facecolors="none",
                   edgecolors="grey")
        ax.set_title(f"Value by {label}")
        ax.set_xlabel(label)
        ax.grid(color="lightgrey")

    def _plot_part_operator_interaction(self, data_grouped_by_operator_and_part, label, ax):
        colors = ["#0051A5", "#971817", "#4DA862", "orange", "yellow", "pink", "lightgreen", "purple", "brown", "grey"]
        markers = ["o", "s", "D", "^", "v", "+", "x", "H", "<", ">"]
        linestyles = ["solid", "dashed", "dotted", "dashdot", "solid", "dotted", "dashed", "dashdot", "solid", "dotted"]

        i = 0
        for operator in data_grouped_by_operator_and_part["Operator"].unique():
            operator_data = data_grouped_by_operator_and_part[data_grouped_by_operator_and_part["Operator"] == operator]
            ax.scatter(
                x=operator_data["Part"],
                y=operator_data["Value"],
                c=colors[i],
                marker=markers[i],
                label=operator)
            ax.plot(
                operator_data["Part"],
                operator_data["Value"],
                color=colors[i],
                linestyle=linestyles[i])
            i += 1

        ax.set_xticks(list(data_grouped_by_operator_and_part["Part"]))
        ax.set_title(f"Part * {label} Interaction")
        ax.set_xlabel("Part")
        ax.set_ylabel("Average")
        ax.legend()
        ax.grid(color="lightgrey")

    @staticmethod
    def _plot_xbar_chart_by_operator(operator_data, label, ax):
        ax.scatter(x=operator_data["Part"], y=operator_data["Mean"])
        ax.plot(operator_data["Part"], operator_data["Mean"])
        ax.axhline(operator_data["Mean"].mean(), color="green", label="X-bar", linewidth=0.7)
        ax.axhline(operator_data["Mean"].mean() + (1.023 * operator_data["Range"].mean()), color="red", label="UCL",
                   linewidth=0.7)
        ax.axhline(operator_data["Mean"].mean() - (1.023 * operator_data["Range"].mean()), color="red", label="LCL",
                   linewidth=0.7)
        ax.set_xticks(list(operator_data["Part"]))
        ax.set_title(f"Xbar Chart by {label} - {operator_data['Operator'].iloc[0]}")
        ax.set_xlabel("Part")
        ax.set_ylabel("Sample Mean")
        ax.set_ylim(operator_data["Mean"].min() - 1, operator_data["Mean"].max() + 1)
        ax.legend(fontsize='small')

    @staticmethod
    def _plot_r_chart_by_operator(operator_data, label, ax):
        ax.scatter(x=operator_data["Part"], y=operator_data["Range"])
        ax.plot(operator_data["Part"], operator_data["Range"])
        ax.axhline(operator_data["Range"].mean(), color="green", label="R-bar", linewidth=0.7)
        ax.axhline(operator_data["Range"].mean() + (1.023 * operator_data["Range"].std()), color="red", label="UCL",
                   linewidth=0.7)
        ax.axhline(operator_data["Range"].mean() - (1.023 * operator_data["Range"].std()), color="red", label="LCL",
                   linewidth=0.7)
        ax.set_xticks(list(operator_data["Part"]))
        ax.set_title(f"R Chart by {label} - {operator_data['Operator'].iloc[0]}")
        ax.set_xlabel("Part")
        ax.set_ylabel("Range")
        ax.set_ylim(operator_data["Range"].min() - 1, operator_data["Range"].max() + 1)
        ax.legend(fontsize='small')

    @staticmethod
    def _perform_two_way_anova(data, operators_count, parts_count,
                               replicates_per_part, ax=None, pdf=None):
        # Perform two-way ANOVA with interaction
        model_2way_interaction = ols('Value ~ C(Part) + C(Operator) + C(Part):C(Operator)', data=data).fit()
        model_2way_interaction_results = sm.stats.anova_lm(model_2way_interaction, type=2)
        model_2way_interaction_results.rename(columns={"df": "DF", "sum_sq": "SS", "mean_sq": "MS", "PR(>F)": "P"},
                                              inplace=True)
        model_2way_interaction_results.reset_index(inplace=True, drop=True)
        model_2way_interaction_results["Source"] = ["Part", "Operator", "Part * Operator", "Repeatability"]
        model_2way_interaction_results = model_2way_interaction_results[["Source", "DF", "SS", "MS", "F", "P"]]
        model_2way_interaction_results = model_2way_interaction_results.set_index("Source")

        # Perform two-way ANOVA without interaction
        model_2way_no_interaction = ols('Value ~ C(Part) + C(Operator)', data=data).fit()
        model_2way_no_interaction_results = sm.stats.anova_lm(model_2way_no_interaction, type=2)
        model_2way_no_interaction_results.rename(columns={"df": "DF", "sum_sq": "SS", "mean_sq": "MS", "PR(>F)": "P"},
                                                 inplace=True)
        model_2way_no_interaction_results.reset_index(inplace=True, drop=True)
        model_2way_no_interaction_results["Source"] = ["Part", "Operator", "Repeatability"]
        model_2way_no_interaction_results = model_2way_no_interaction_results[["Source", "DF", "SS", "MS", "F", "P"]]
        model_2way_no_interaction_results = model_2way_no_interaction_results.set_index("Source")

        # Plot bar chart with components of variation
        var_comp_repeatability = model_2way_interaction_results.loc["Repeatability"]["MS"]
        var_comp_operator = (model_2way_interaction_results.loc["Operator"]["MS"] -
                             model_2way_interaction_results.loc["Repeatability"]["MS"]) / (
                                    parts_count * replicates_per_part)
        var_comp_part_part = (model_2way_interaction_results.loc["Part"]["MS"] -
                              model_2way_interaction_results.loc["Repeatability"]["MS"]) / (
                                     operators_count * replicates_per_part)
        var_comp_reproducibility = var_comp_operator
        var_comp_total_gage_rr = var_comp_repeatability + var_comp_reproducibility
        var_comp_total_variation = var_comp_total_gage_rr + var_comp_part_part

        gage_rr_var_comp_no_interaction_df = pd.DataFrame({
            "Source": ["Total Gage R&R", "Repeatability", "Reproducibility", "Operator", "Part-To-Part",
                       "Total Variation"],
            "VarComp": [var_comp_total_gage_rr, var_comp_repeatability, var_comp_reproducibility, var_comp_operator,
                        var_comp_part_part, var_comp_total_variation]
        })

        gage_rr_var_comp_no_interaction_df["%Contribution (of VarComp)"] = gage_rr_var_comp_no_interaction_df[
                                                                               "VarComp"] / \
                                                                           gage_rr_var_comp_no_interaction_df[
                                                                               gage_rr_var_comp_no_interaction_df[
                                                                                   "Source"] == "Total Variation"][
                                                                               "VarComp"].iloc[0] * 100
        gage_rr_var_comp_no_interaction_df = gage_rr_var_comp_no_interaction_df.set_index("Source")

        # Calculate and get Gage Evaluation data frame with results
        gage_evaluation_df = np.sqrt(gage_rr_var_comp_no_interaction_df[["VarComp"]])
        gage_evaluation_df = gage_evaluation_df.rename(columns={"VarComp": "StdDev (SD)"})
        gage_evaluation_df["Study Var (6 x SD)"] = gage_evaluation_df["StdDev (SD)"] * 6
        gage_evaluation_df["%Study Var (%SV)"] = gage_evaluation_df["Study Var (6 x SD)"] / \
                                                 gage_evaluation_df.loc["Total Variation"]["Study Var (6 x SD)"] * 100
        gage_evaluation_df["%Tol. (SV/Toler)"] = gage_evaluation_df["Study Var (6 x SD)"] / 8 * 100
        gage_evaluation_df["%Contrib. (VarComp)"] = gage_rr_var_comp_no_interaction_df[
            "%Contribution (of VarComp)"]

        gage_evaluation_df.loc[["Total Gage R&R", "Repeatability", "Reproducibility", "Part-To-Part"]][
            ["%Contrib. (VarComp)", "%Study Var (%SV)", "%Tol. (SV/Toler)"]].plot(kind="bar",
                                                                                  figsize=(10, 6), ax=ax)

        if pdf:
            ax.set_title("Components of Variation")
            ax.set_ylabel("Percent")
            ax.set_xlabel("")
            ax.grid(color="lightgrey")
            ax.set_xticklabels(ax.get_xticklabels(), rotation=45)

        return (model_2way_interaction_results, model_2way_no_interaction_results, gage_rr_var_comp_no_interaction_df,
                gage_evaluation_df)
