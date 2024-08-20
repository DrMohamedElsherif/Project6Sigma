# msa_charts.py

import io
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.api as sm
from matplotlib.backends.backend_pdf import PdfPages
from statsmodels.formula.api import ols


def plot_value_by_part(data, data_grouped_by_part, ax):
    ax.scatter(x=data["Part"], y=data["Value"], color="grey")
    ax.scatter(x=data_grouped_by_part["Part"], y=data_grouped_by_part["Value"], color="#7DA7D9", facecolors="none")
    ax.plot(data_grouped_by_part["Part"], data_grouped_by_part["Value"], color="#7DA7D9")
    ax.set_xticks(list(data_grouped_by_part["Part"]))
    ax.set_title("Value by Part")
    ax.set_xlabel("Part")
    ax.grid(color="lightgrey")


def plot_value_by_operator(data, label, data_grouped_by_operator, ax):
    sns.boxplot(x="Operator", y="Value", data=data, color="#7DA7D9", width=0.4, ax=ax)
    ax.plot(data_grouped_by_operator["Operator"], data_grouped_by_operator["Value"], color="grey")
    ax.scatter(x=data_grouped_by_operator["Operator"], y=data_grouped_by_operator["Value"], facecolors="none",
               edgecolors="grey")
    ax.set_title(f"Value by {label}")
    ax.set_xlabel(label)
    ax.grid(color="lightgrey")


def plot_part_operator_interaction(data_grouped_by_operator_and_part, label, ax):
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


def plot_xbar_chart_by_operator(operator_data, label, ax):
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


def plot_r_chart_by_operator(operator_data, label, ax):
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


def perform_two_way_anova(data, operators_count, parts_count, replicates_per_part, ax=None, pdf=None):
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
