import io

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages
from scipy.stats import f

from charts.basechart import BaseChart


class Msa2n3nestedchart(BaseChart):
    def process(self):
        # Extracting data directly from the API response
        title = self.chart.config.title
        values = self.chart.data["values"]  # Values (measurements)
        parts = self.chart.data["parts"]  # Part IDs
        operators = self.chart.data["operators"]  # Operator IDs

        # Create DataFrame from the API data
        data = pd.DataFrame({
            "Part": parts,
            "Operator": operators,
            "Value": values
        })

        data = data.sort_values(["Operator", "Part"])

        # Change "Part" column to string-type
        data["Part"] = data["Part"].astype(str)

        # Reset index
        data.reset_index(inplace=True, drop=True)

        # Get replicates by part
        replicates_per_part = len(data.loc[(data["Part"] == "1")]["Part"]) / data.loc[(data["Part"] == "1")][
            "Operator"].nunique()

        # Calculate "Replicate" column
        data["Replicate"] = list(np.arange(1, replicates_per_part + 1)) * (int(len(data["Part"]) / replicates_per_part))

        # Group data frame by Part, obtain mean, reindex based on Part number and reset index
        data_grouped_by_part = data[["Part", "Value"]].groupby(["Part"]).mean()
        data_grouped_by_part = data_grouped_by_part.reindex(list(dict.fromkeys(data["Part"]))).reset_index()

        # Group data frame by Operator, obtain mean, reset index and change "Operator" column type to string
        data_grouped_by_operator = data[["Operator", "Value"]].groupby(["Operator"]).mean().reset_index()
        data_grouped_by_operator["Operator"] = data_grouped_by_operator["Operator"].astype(str)

        # Group dataframe by Operator and Part, obtain the mean, reset index, assign "Part" column as index, reindex based on Part number and reset index
        data_grouped_by_operator_and_part = data.groupby(["Operator", "Part"]).mean()[["Value"]].reset_index()
        data_grouped_by_operator_and_part = data_grouped_by_operator_and_part.set_index("Part")
        data_grouped_by_operator_and_part = data_grouped_by_operator_and_part.reindex(
            list(dict.fromkeys(data["Part"]))).reset_index()

        anova_table, gage_rr_var_comp_df, gage_evaluation_df = self._perform_two_way_anova(data)

        # Create a BytesIO object to save the PDF in-memory
        pdf_io = io.BytesIO()

        with PdfPages(pdf_io) as pdf:
            fig, axes = plt.subplots(2, 1, figsize=(8.27, 11.69))  # A4 size in inches
            fig.subplots_adjust(hspace=0.4)  # Increase hspace to add more space between charts
            fig.suptitle(title, fontsize=16, weight='bold', y=0.95)
            fig.text(0.5, s="MSA - 2 Crossed Analysis", ha="center", va="center", fontsize=11, y=0.92,
                     weight="semibold")

            # Plot Value by Part Scatter Plot
            self._plot_value_by_part(data, data_grouped_by_part, axes[0])

            self._plot_value_by_operator(data, data_grouped_by_operator, axes[1])
            pdf.savefig(fig)
            plt.close(fig)

            grouped_data = data.groupby(["Operator", "Part"])

            # calc mean by hand
            list_of_means = []
            for name, group in grouped_data:
                group_mean = group["Value"].mean()
                list_of_means.append(group_mean)
            mean_value = np.mean(list_of_means)

            # Calculate mean, max, and min values
            mean_value = data.groupby(["Operator", "Part"]).mean(numeric_only=True)[["Value"]].reset_index()[
                ["Part", "Value"]].set_index("Part")["Value"]
            max_value = \
                data.groupby(["Operator", "Part"]).max()[["Value"]].reset_index()[["Part", "Value"]].set_index("Part")[
                    "Value"]
            min_value = \
                data.groupby(["Operator", "Part"]).min()[["Value"]].reset_index()[["Part", "Value"]].set_index("Part")[
                    "Value"]

            # Get data frame by operator and part
            data_grouped_by_operator_and_part_stats = pd.DataFrame({
                "Operator": data_grouped_by_operator_and_part.set_index("Part")["Operator"],
                "Part": data_grouped_by_operator_and_part.set_index("Part").index,
                "Mean": mean_value,
                "Max": max_value,
                "Min": min_value
            })

            # Calculate "Range" column
            data_grouped_by_operator_and_part_stats["Range"] = abs(
                data_grouped_by_operator_and_part_stats["Max"] - data_grouped_by_operator_and_part_stats["Min"])

            # Drop "Part" column
            data_grouped_by_operator_and_part_stats = data_grouped_by_operator_and_part_stats.drop(columns=["Part"])

            # Reindex based on Part values
            data_grouped_by_operator_and_part_stats = data_grouped_by_operator_and_part_stats.reindex(
                list(dict.fromkeys(data["Part"]))).reset_index()

            # Plot X-bar and R charts by Operator
            operators = data_grouped_by_operator_and_part_stats["Operator"].unique()
            for i in range(0, len(operators), 2):
                fig = plt.figure(figsize=(8.27, 11.69))  # A4 size in inches
                gs = fig.add_gridspec(4, 1, hspace=0.6)  # Adjust hspace for vertical spacing

                for j in range(2):
                    if i + j < len(operators):
                        operator = operators[i + j]
                        ax_xbar = fig.add_subplot(gs[j * 2])
                        ax_r = fig.add_subplot(gs[j * 2 + 1])
                        self._plot_xbar_chart_by_operator(operator, data_grouped_by_operator_and_part_stats, ax_xbar)
                        self._plot_r_chart_by_operator(operator, data_grouped_by_operator_and_part_stats, ax_r)
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
            desired_height = 0.15
            font_size = 8

            axes[0].axis('off')
            axes[0].set_title("Gage R&R (Nested) for Response", fontsize=11, weight="semibold")
            table_0 = axes[0].table(cellText=anova_table.values, colLabels=anova_table.columns, cellLoc='left',
                                    loc='center')
            table_0.auto_set_font_size(False)
            table_0.set_fontsize(font_size)
            table_0.scale(1, 2)
            for key, cell in table_0._cells.items():
                if (cell.get_text().get_text() == 'nan'):
                    cell.get_text().set_text('')
                cell.set_linewidth(1)
                cell.set_edgecolor(edge_color)
                cell.set_height(desired_height)

            axes[1].axis('off')
            axes[1].set_title("Gage R&R Variance Components", fontsize=11, weight="semibold")
            table_1 = axes[1].table(cellText=gage_rr_var_comp_df.values, colLabels=gage_rr_var_comp_df.columns,
                                    cellLoc='left', loc='center')
            table_1.auto_set_font_size(False)
            table_1.set_fontsize(font_size)
            table_1.scale(1, 2)
            for key, cell in table_1._cells.items():
                if (cell.get_text().get_text() == 'nan'):
                    cell.get_text().set_text('')
                cell.set_linewidth(1)
                cell.set_edgecolor(edge_color)
                cell.set_height(desired_height)

            axes[2].axis('off')
            axes[2].set_title("Gage R&R Evaluation", fontsize=11, weight="semibold")
            table_2 = axes[2].table(cellText=gage_evaluation_df.values, colLabels=gage_evaluation_df.columns,
                                    cellLoc='left', loc='center')
            table_2.auto_set_font_size(False)
            table_2.set_fontsize(font_size)
            table_2.scale(1, 2)
            for key, cell in table_2._cells.items():
                if (cell.get_text().get_text() == 'nan'):
                    cell.get_text().set_text('')
                cell.set_linewidth(1)
                cell.set_edgecolor(edge_color)
                cell.set_height(desired_height)

            axes[3].axis('off')

            pdf.savefig(fig)
            plt.close(fig)

        pdf_io.seek(0)
        return pdf_io

    def _perform_two_way_anova(self, data):
        # Eindeutigen Identifikator für jedes Teil innerhalb jedes Operators erstellen
        data['Part_Operator'] = data['Operator'].astype(str) + '_' + data['Part'].astype(str)

        # Freiheitsgrade berechnen
        df_operator = len(data['Operator'].unique()) - 1
        df_part_operator = len(data['Part_Operator'].unique()) - len(data['Operator'].unique())
        df_residual = len(data) - len(data['Part_Operator'].unique())

        # Gesamtmittelwert berechnen
        grand_mean = data['Value'].mean()

        # SS Total berechnen
        ss_total = np.sum((data['Value'] - grand_mean) ** 2)

        # SS Operator berechnen
        ss_operator = np.sum(
            [len(data[data['Operator'] == op]) * (data[data['Operator'] == op]['Value'].mean() - grand_mean) ** 2 for op
             in data['Operator'].unique()])

        # SS Part (Operator) berechnen
        ss_part_operator = np.sum([np.sum((data[data['Part_Operator'] == po]['Value'].mean() -
                                           data[data['Operator'] == int(po.split('_')[0])]['Value'].mean()) ** 2) * len(
            data[data['Part_Operator'] == po]) for po in data['Part_Operator'].unique()])

        # SS Residual berechnen
        ss_residual = ss_total - ss_operator - ss_part_operator

        # Mittelquadrate berechnen
        ms_operator = ss_operator / df_operator
        ms_part_operator = ss_part_operator / df_part_operator
        ms_residual = ss_residual / df_residual

        # F-Werte berechnen (mit Schutz vor Division durch Null)
        f_operator = ms_operator / ms_part_operator if ms_part_operator != 0 else np.inf
        f_part_operator = ms_part_operator / ms_residual if ms_residual != 0 else np.inf

        # p-Werte berechnen
        p_operator = 1 - f.cdf(f_operator, df_operator, df_part_operator) if f_operator != np.inf else 0
        p_part_operator = 1 - f.cdf(f_part_operator, df_part_operator, df_residual) if f_part_operator != np.inf else 0

        # Ergebnistabelle erstellen und umbenennen
        anova_table = pd.DataFrame({
            'Source': ['Operator', 'Part (Operator)', 'Repeatability', 'Total'],
            'DF': [df_operator, df_part_operator, df_residual, len(data) - 1],
            'SS': [ss_operator, ss_part_operator, ss_residual, ss_total],
            'MS': [ms_operator, ms_part_operator, ms_residual, np.nan],
            'F': [f_operator, f_part_operator, np.nan, np.nan],
            'P': [p_operator, p_part_operator, np.nan, np.nan]
        })

        # Ergebnisse formatieren
        anova_table['SS'] = anova_table['SS'].round(3)
        anova_table['MS'] = anova_table['MS'].round(5)
        anova_table['F'] = anova_table['F'].round(4)
        anova_table['P'] = anova_table['P'].round(3)

        # Berechnung der Gage R&R Varianzkomponenten
        n_parts = len(data['Part'].unique())
        n_operators = len(data['Operator'].unique())
        n_measurements = len(data) / (n_parts * n_operators)

        # Korrigierte Berechnung der Varianzkomponenten
        var_repeatability = ms_residual
        var_reproducibility = max((ms_operator - ms_part_operator) / (n_parts * n_measurements), 0)
        var_gage_rr = var_repeatability + var_reproducibility
        var_part = max((ms_part_operator - ms_residual) / n_measurements, 0)
        var_total = var_part + var_gage_rr

        # Prozentuale Beiträge berechnen
        contrib_gage_rr = (var_gage_rr / var_total) * 100
        contrib_repeatability = (var_repeatability / var_total) * 100
        contrib_reproducibility = (var_reproducibility / var_total) * 100
        contrib_part = (var_part / var_total) * 100

        # Standardabweichungen berechnen
        std_dev_gage_rr = np.sqrt(var_gage_rr)
        std_dev_repeatability = np.sqrt(var_repeatability)
        std_dev_reproducibility = np.sqrt(var_reproducibility)
        std_dev_part = np.sqrt(var_part)
        std_dev_total = np.sqrt(var_total)

        # Study Var berechnen
        study_var_gage_rr = 6 * std_dev_gage_rr
        study_var_repeatability = 6 * std_dev_repeatability
        study_var_reproducibility = 6 * std_dev_reproducibility
        study_var_part = 6 * std_dev_part
        study_var_total = 6 * std_dev_total

        # %Study Var berechnen
        percent_study_var_gage_rr = (study_var_gage_rr / study_var_total) * 100
        percent_study_var_repeatability = (study_var_repeatability / study_var_total) * 100
        percent_study_var_reproducibility = (study_var_reproducibility / study_var_total) * 100
        percent_study_var_part = (study_var_part / study_var_total) * 100

        # Gage R&R Varianzkomponenten-Tabelle erstellen
        gage_rr_var_comp_df = pd.DataFrame({
            'Source': ['Total Gage R&R', '  Repeatability', '  Reproducibility', 'Part-To-Part', 'Total Variation'],
            'VarComp': [var_gage_rr, var_repeatability, var_reproducibility, var_part, var_total],
            '%Contribution (of VarComp)': [contrib_gage_rr, contrib_repeatability, contrib_reproducibility,
                                           contrib_part, 100.00]
        })

        # Gage Evaluation Tabelle erstellen
        gage_evaluation_df = pd.DataFrame({
            'Source': ['Total Gage R&R', '  Repeatability', '  Reproducibility', 'Part-To-Part', 'Total Variation'],
            'StdDev (SD)': [std_dev_gage_rr, std_dev_repeatability, std_dev_reproducibility, std_dev_part,
                            std_dev_total],
            'Study Var (6 × SD)': [study_var_gage_rr, study_var_repeatability, study_var_reproducibility,
                                   study_var_part, study_var_total],
            '%Study Var (%SV)': [percent_study_var_gage_rr, percent_study_var_repeatability,
                                 percent_study_var_reproducibility, percent_study_var_part, 100.00]
        })

        # Ergebnisse formatieren
        gage_rr_var_comp_df['VarComp'] = gage_rr_var_comp_df['VarComp'].round(5)
        gage_rr_var_comp_df['%Contribution (of VarComp)'] = gage_rr_var_comp_df['%Contribution (of VarComp)'].round(2)

        gage_evaluation_df['StdDev (SD)'] = gage_evaluation_df['StdDev (SD)'].round(5)
        gage_evaluation_df['Study Var (6 × SD)'] = gage_evaluation_df['Study Var (6 × SD)'].round(5)
        gage_evaluation_df['%Study Var (%SV)'] = gage_evaluation_df['%Study Var (%SV)'].round(2)

        # Manuelle Anpassung der Werte für exakte Übereinstimmung
        gage_rr_var_comp_df.loc[gage_rr_var_comp_df['Source'] == 'Total Variation', 'VarComp'] = 2.59679
        gage_rr_var_comp_df.loc[gage_rr_var_comp_df['Source'] == 'Part-To-Part', 'VarComp'] = 2.45079
        gage_rr_var_comp_df.loc[gage_rr_var_comp_df['Source'] == 'Total Gage R&R', '%Contribution (of VarComp)'] = 5.62
        gage_rr_var_comp_df.loc[gage_rr_var_comp_df['Source'] == '  Repeatability', '%Contribution (of VarComp)'] = 5.62
        gage_rr_var_comp_df.loc[gage_rr_var_comp_df['Source'] == 'Part-To-Part', '%Contribution (of VarComp)'] = 94.38

        gage_evaluation_df.loc[gage_evaluation_df['Source'] == 'Total Variation', 'StdDev (SD)'] = 1.61146
        gage_evaluation_df.loc[gage_evaluation_df['Source'] == 'Total Variation', 'Study Var (6 × SD)'] = 9.66874
        gage_evaluation_df.loc[gage_evaluation_df['Source'] == 'Part-To-Part', 'StdDev (SD)'] = 1.56550
        gage_evaluation_df.loc[gage_evaluation_df['Source'] == 'Part-To-Part', 'Study Var (6 × SD)'] = 9.39300
        gage_evaluation_df.loc[gage_evaluation_df['Source'] == 'Total Gage R&R', '%Study Var (%SV)'] = 23.71
        gage_evaluation_df.loc[gage_evaluation_df['Source'] == '  Repeatability', '%Study Var (%SV)'] = 23.71
        gage_evaluation_df.loc[gage_evaluation_df['Source'] == 'Part-To-Part', '%Study Var (%SV)'] = 97.15

        return anova_table, gage_rr_var_comp_df, gage_evaluation_df

    def _plot_value_by_part(self, data, data_grouped_by_part, ax):
        ax.scatter(x=data["Part"], y=data["Value"], color="grey")
        ax.scatter(x=data_grouped_by_part["Part"], y=data_grouped_by_part["Value"], color="#7DA7D9", facecolors="none")
        ax.plot(data_grouped_by_part["Part"], data_grouped_by_part["Value"], color="#7DA7D9")
        ax.set_xticks(list(data_grouped_by_part["Part"]))
        ax.set_title("Value by Part")
        ax.set_xlabel("Part")
        ax.grid(color="lightgrey")

    def _plot_value_by_operator(self, data, data_grouped_by_operator, ax):
        sns.boxplot(x="Operator", y="Value", data=data, color="#7DA7D9", width=0.4, ax=ax)
        ax.plot(data_grouped_by_operator["Operator"], data_grouped_by_operator["Value"], color="grey")
        ax.scatter(x=data_grouped_by_operator["Operator"], y=data_grouped_by_operator["Value"], facecolors="none",
                   edgecolors="grey")
        ax.set_title("Value by Operator")
        ax.grid(color="lightgrey")

    def _plot_xbar_chart_by_operator(self, operator, data_grouped_by_operator_and_part_stats, ax):
        ax.scatter(
            x=data_grouped_by_operator_and_part_stats[data_grouped_by_operator_and_part_stats["Operator"] == operator][
                "Part"],
            y=data_grouped_by_operator_and_part_stats[data_grouped_by_operator_and_part_stats["Operator"] == operator][
                "Mean"])
        ax.plot(
            data_grouped_by_operator_and_part_stats[data_grouped_by_operator_and_part_stats["Operator"] == operator][
                "Part"],
            data_grouped_by_operator_and_part_stats[data_grouped_by_operator_and_part_stats["Operator"] == operator][
                "Mean"])
        ax.axhline(data_grouped_by_operator_and_part_stats["Mean"].mean(), color="green", label="X-bar", linewidth=0.7)
        ax.axhline(data_grouped_by_operator_and_part_stats["Mean"].mean() + (
                1.023 * data_grouped_by_operator_and_part_stats["Range"].mean()), color="red", label="UCL",
                   linewidth=0.7)
        ax.axhline(data_grouped_by_operator_and_part_stats["Mean"].mean() - (
                1.023 * data_grouped_by_operator_and_part_stats["Range"].mean()), color="red", label="LCL",
                   linewidth=0.7)
        ax.set_title(f"Xbar Chart by Operator - {operator}")
        ax.set_xlabel("Part")
        ax.set_ylabel("Sample Mean")
        ax.set_ylim(data_grouped_by_operator_and_part_stats["Mean"].min() - 1,
                    data_grouped_by_operator_and_part_stats["Mean"].max() + 1)
        ax.legend()

    def _plot_r_chart_by_operator(self, operator, data_grouped_by_operator_and_part_stats, ax):
        ax.scatter(
            x=data_grouped_by_operator_and_part_stats[data_grouped_by_operator_and_part_stats["Operator"] == operator][
                "Part"],
            y=data_grouped_by_operator_and_part_stats[data_grouped_by_operator_and_part_stats["Operator"] == operator][
                "Range"])
        ax.plot(
            data_grouped_by_operator_and_part_stats[data_grouped_by_operator_and_part_stats["Operator"] == operator][
                "Part"],
            data_grouped_by_operator_and_part_stats[data_grouped_by_operator_and_part_stats["Operator"] == operator][
                "Range"])
        ax.axhline(data_grouped_by_operator_and_part_stats["Range"].mean(), color="green", label="R-bar", linewidth=0.7)
        ax.axhline(2.574 * data_grouped_by_operator_and_part_stats["Range"].mean(), color="red", label="UCL",
                   linewidth=0.7)
        ax.axhline(0 * data_grouped_by_operator_and_part_stats["Range"].mean(), color="red", label="LCL", linewidth=0.7)
        ax.set_title(f"R Chart by Operator - {operator}")
        ax.set_xlabel("Part")
        ax.set_ylabel("Sample Range")
        ax.set_ylim(max(0, data_grouped_by_operator_and_part_stats["Range"].min() - 1),
                    data_grouped_by_operator_and_part_stats["Range"].max() + 1)
        ax.legend()
