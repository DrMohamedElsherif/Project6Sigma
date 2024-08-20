import io

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.api as sm
from statsmodels.formula.api import ols
from matplotlib.backends.backend_pdf import PdfPages

from charts.basechart import BaseChart


# class Msa2n3nestedchart(BaseChart):
#     def process(self):
#         # Extracting data directly from the API response
#         title = self.chart.config.title
#         values = self.chart.data["values"]  # Values (measurements)
#         parts = self.chart.data["parts"]  # Part IDs
#         operators = self.chart.data["operators"]  # Operator IDs
#
#         # Create DataFrame from the API data
#         data = pd.DataFrame({
#             "Part": parts,
#             "Operator": operators,
#             "Value": values
#         })
#
#         # Sort data frame by Operator and Part
#         data = data.sort_values(["Operator", "Part"])
#
#         # Change "Part" column to string-type
#         data["Part"] = data["Part"].astype(str)
#
#         # Reset index
#         data.reset_index(inplace=True, drop=True)
#
#         # Get operators count
#         operators_count = data["Operator"].nunique()
#
#         # Get parts count
#         parts_count = data["Part"].nunique()
#
#         # Get replicates by part
#         replicates_per_part = len(data.loc[(data["Part"] == "1")]["Part"]) / data.loc[(data["Part"] == "1")][
#             "Operator"].nunique()
#
#         # Calculate "Replicate" column
#         data["Replicate"] = list(np.arange(1, replicates_per_part + 1)) * (int(len(data["Part"]) / replicates_per_part))
#
#         # Group data frame by Part, obtain mean, reindex based on Part number and reset index
#         data_grouped_by_part = data[["Part", "Value"]].groupby(["Part"]).mean()
#         data_grouped_by_part = data_grouped_by_part.reindex(list(dict.fromkeys(data["Part"]))).reset_index()
#
#         # Group data frame by Operator, obtain mean, reset index and change "Operator" column type to string
#         data_grouped_by_operator = data[["Operator", "Value"]].groupby(["Operator"]).mean().reset_index()
#         data_grouped_by_operator["Operator"] = data_grouped_by_operator["Operator"].astype(str)
#
#         # Group data frame by Operator and Part, obtain the mean and reset index
#         data_grouped_by_operator_and_part = data.groupby(["Operator", "Part"]).mean()[["Value"]].reset_index()
#
#         # Group dataframe by Operator and Part, obtain the mean, reset index, assign "Part" column as index, reindex based on Part number and reset index
#         data_grouped_by_operator_and_part = data.groupby(["Operator", "Part"]).mean()[["Value"]].reset_index()
#         data_grouped_by_operator_and_part = data_grouped_by_operator_and_part.set_index("Part")
#         data_grouped_by_operator_and_part = data_grouped_by_operator_and_part.reindex(
#             list(dict.fromkeys(data["Part"]))).reset_index()
#
#         model_2way_interaction_results, gage_rr_var_comp_df, gage_evaluation_df = self._perform_two_way_anova(data)
#
#         # Create a BytesIO object to save the PDF in-memory
#         pdf_io = io.BytesIO()
#
#         with PdfPages(pdf_io) as pdf:
#             # Plot Value by Part Scatter Plot
#             fig, ax = plt.subplots(figsize=(10, 5))
#             self._plot_value_by_part(data, data_grouped_by_part, ax)
#             pdf.savefig(fig)
#             plt.close(fig)
#
#             # Plot Value by Operator Boxplot
#             fig, ax = plt.subplots(figsize=(10, 5))
#             self._plot_value_by_operator(data, data_grouped_by_operator, ax)
#             pdf.savefig(fig)
#             plt.close(fig)
#
#             # Calculate mean, max, and min values
#             mean_value = \
#                 data.groupby(["Operator", "Part"]).mean()[["Value"]].reset_index()[["Part", "Value"]].set_index("Part")[
#                     "Value"]
#             max_value = \
#                 data.groupby(["Operator", "Part"]).max()[["Value"]].reset_index()[["Part", "Value"]].set_index("Part")[
#                     "Value"]
#             min_value = \
#                 data.groupby(["Operator", "Part"]).min()[["Value"]].reset_index()[["Part", "Value"]].set_index("Part")[
#                     "Value"]
#
#             # Get data frame by operator and part
#             data_grouped_by_operator_and_part_stats = pd.DataFrame({
#                 "Operator": data_grouped_by_operator_and_part.set_index("Part")["Operator"],
#                 "Part": data_grouped_by_operator_and_part.set_index("Part").index,
#                 "Mean": mean_value,
#                 "Max": max_value,
#                 "Min": min_value
#             })
#
#             # Calculate "Range" column
#             data_grouped_by_operator_and_part_stats["Range"] = abs(
#                 data_grouped_by_operator_and_part_stats["Max"] - data_grouped_by_operator_and_part_stats["Min"])
#
#             # Drop "Part" column
#             data_grouped_by_operator_and_part_stats = data_grouped_by_operator_and_part_stats.drop(columns=["Part"])
#
#             # Reindex based on Part values
#             data_grouped_by_operator_and_part_stats = data_grouped_by_operator_and_part_stats.reindex(
#                 list(dict.fromkeys(data["Part"]))).reset_index()
#
#             # Plot X-bar and R charts by Operator
#             operators = data_grouped_by_operator_and_part_stats["Operator"].unique()
#             for operator in operators:
#                 # X-bar chart
#                 fig, ax = plt.subplots(figsize=(8, 3))
#                 self._plot_xbar_chart_by_operator(operator, data_grouped_by_operator_and_part_stats, ax)
#                 pdf.savefig(fig)
#                 plt.close(fig)
#
#                 # R chart
#                 fig, ax = plt.subplots(figsize=(8, 3))
#                 self._plot_r_chart_by_operator(operator, data_grouped_by_operator_and_part_stats, ax)
#                 pdf.savefig(fig)
#                 plt.close(fig)
#
#         pdf_io.seek(0)
#         return pdf_io
#
#
#     def _perform_two_way_anova(self, data):
#         # Performing nested ANOVA
#         model_nested = ols('Value ~ C(Part) + C(Operator) + C(Part):C(Operator)', data=data).fit()
#         model_nested_results = sm.stats.anova_lm(model_nested, typ=2)
#         model_nested_results.rename(columns={"df": "DF", "sum_sq": "SS", "mean_sq": "MS", "PR(>F)": "P"}, inplace=True)
#
#         # Calculate the variance components
#         MS_repeatability = model_nested_results.loc["Residual", "MS"]
#         MS_part_operator = model_nested_results.loc["C(Operator):C(Part)", "MS"]
#         MS_operator = model_nested_results.loc["C(Operator)", "MS"]
#
#         var_comp_repeatability = MS_repeatability
#         var_comp_part_operator = (MS_part_operator - MS_repeatability) / data["Operator"].nunique()
#         var_comp_operator = (MS_operator - MS_part_operator) / data["Part"].nunique()
#         var_comp_total_gage_rr = var_comp_repeatability + var_comp_part_operator
#
#         var_comp_total_variation = var_comp_total_gage_rr + var_comp_operator
#
#         gage_rr_var_comp_df = pd.DataFrame({
#             "Source": ["Total Gage R&R", "Repeatability", "Reproducibility", "Part-To-Part", "Total Variation"],
#             "VarComp": [var_comp_total_gage_rr, var_comp_repeatability, var_comp_part_operator, var_comp_operator, var_comp_total_variation]
#         })
#         gage_rr_var_comp_df["%Contribution (of VarComp)"] = gage_rr_var_comp_df["VarComp"] / gage_rr_var_comp_df["VarComp"].iloc[-1] * 100
#         gage_rr_var_comp_df.set_index("Source", inplace=True)
#
#         # Gage Evaluation
#         gage_evaluation_df = gage_rr_var_comp_df.copy()
#         gage_evaluation_df["StdDev (SD)"] = np.sqrt(gage_evaluation_df["VarComp"])
#         gage_evaluation_df["Study Var (6 x SD)"] = gage_evaluation_df["StdDev (SD)"] * 6
#         gage_evaluation_df["%Study Var (%SV)"] = gage_evaluation_df["Study Var (6 x SD)"] / gage_evaluation_df["Study Var (6 x SD)"].iloc[-1] * 100
#
#         return model_nested_results, gage_rr_var_comp_df, gage_evaluation_df
#
#     def _plot_value_by_part(self, data, data_grouped_by_part, ax):
#         ax.scatter(x=data["Part"], y=data["Value"], color="grey")
#         ax.scatter(x=data_grouped_by_part["Part"], y=data_grouped_by_part["Value"], color="#7DA7D9", facecolors="none")
#         ax.plot(data_grouped_by_part["Part"], data_grouped_by_part["Value"], color="#7DA7D9")
#         ax.set_xticks(list(data_grouped_by_part["Part"]))
#         ax.set_title("Value by Part")
#         ax.set_xlabel("Part")
#         ax.grid(color="lightgrey")
#
#     def _plot_value_by_operator(self, data, data_grouped_by_operator, ax):
#         sns.boxplot(x="Operator", y="Value", data=data, color="#7DA7D9", width=0.4, ax=ax)
#         ax.plot(data_grouped_by_operator["Operator"], data_grouped_by_operator["Value"], color="grey")
#         ax.scatter(x=data_grouped_by_operator["Operator"], y=data_grouped_by_operator["Value"], facecolors="none",
#                    edgecolors="grey")
#         ax.set_title("Value by Operator")
#         ax.grid(color="lightgrey")
#
#     def _plot_xbar_chart_by_operator(self, operator, data_grouped_by_operator_and_part_stats, ax):
#         ax.scatter(
#             x=data_grouped_by_operator_and_part_stats[data_grouped_by_operator_and_part_stats["Operator"] == operator][
#                 "Part"],
#             y=data_grouped_by_operator_and_part_stats[data_grouped_by_operator_and_part_stats["Operator"] == operator][
#                 "Mean"])
#         ax.plot(
#             data_grouped_by_operator_and_part_stats[data_grouped_by_operator_and_part_stats["Operator"] == operator][
#                 "Part"],
#             data_grouped_by_operator_and_part_stats[data_grouped_by_operator_and_part_stats["Operator"] == operator][
#                 "Mean"])
#         ax.axhline(data_grouped_by_operator_and_part_stats["Mean"].mean(), color="green", label="X-bar")
#         ax.axhline(data_grouped_by_operator_and_part_stats["Mean"].mean() + (
#                 1.023 * data_grouped_by_operator_and_part_stats["Range"].mean()), color="red", label="UCL")
#         ax.axhline(data_grouped_by_operator_and_part_stats["Mean"].mean() - (
#                 1.023 * data_grouped_by_operator_and_part_stats["Range"].mean()), color="red", label="LCL")
#         ax.set_title(f"Xbar Chart by Operator - {operator}")
#         ax.set_xlabel("Part")
#         ax.set_ylabel("Sample Mean")
#         ax.set_ylim(data_grouped_by_operator_and_part_stats["Mean"].min() - 1,
#                     data_grouped_by_operator_and_part_stats["Mean"].max() + 1)
#         ax.legend()
#
#     def _plot_r_chart_by_operator(self, operator, data_grouped_by_operator_and_part_stats, ax):
#         ax.scatter(
#             x=data_grouped_by_operator_and_part_stats[data_grouped_by_operator_and_part_stats["Operator"] == operator][
#                 "Part"],
#             y=data_grouped_by_operator_and_part_stats[data_grouped_by_operator_and_part_stats["Operator"] == operator][
#                 "Range"])
#         ax.plot(
#             data_grouped_by_operator_and_part_stats[data_grouped_by_operator_and_part_stats["Operator"] == operator][
#                 "Part"],
#             data_grouped_by_operator_and_part_stats[data_grouped_by_operator_and_part_stats["Operator"] == operator][
#                 "Range"])
#         ax.axhline(data_grouped_by_operator_and_part_stats["Range"].mean(), color="green", label="R-bar")
#         ax.axhline(2.574 * data_grouped_by_operator_and_part_stats["Range"].mean(), color="red", label="UCL")
#         ax.axhline(0 * data_grouped_by_operator_and_part_stats["Range"].mean(), color="red", label="LCL")
#         ax.set_title(f"R Chart by Operator - {operator}")
#         ax.set_xlabel("Part")
#         ax.set_ylabel("Sample Range")
#         ax.set_ylim(max(0, data_grouped_by_operator_and_part_stats["Range"].min() - 1),
#                     data_grouped_by_operator_and_part_stats["Range"].max() + 1)
#         ax.legend()
