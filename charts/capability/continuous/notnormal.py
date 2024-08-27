from io import BytesIO
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from scipy import stats
from scipy.stats import normaltest, probplot
from statsmodels.graphics.gofplots import qqplot


def I_MR_chart_transformed(data, title, target=0, subgroup_size=1, LSL=0, USL=0):
    # (Die Validierungen bleiben unverändert)
    if target < 0:
        return print("Error. A non-negative target value must be specified.")
    if subgroup_size <= 0:
        return print("Error. The subgroup size must be a positive value greater than zero.")
    if LSL < 0:
        return print("Error. A non-negative Lower Specification Limit (LSL) must be specified.")
    if USL < 0:
        return print("Error. A non-negative Upper Specification Limit (USL) must be specified.")
    if LSL >= 0 and target > 0:
        if target < LSL:
            return print(f"Error. Target value ({target}) is lower than Lower Specification Limit ({LSL}).")
    if USL >= 0 and target > 0:
        if target > USL:
            return print(f"Error. Target value ({target}) is greater than Upper Specification Limit ({USL}).")
    if LSL > 0 and USL > 0:
        if USL < LSL:
            return print(f"Error. Upper Specification Limit ({USL}) is lower than Lower Specification Limit ({LSL}).")
        if USL == LSL:
            return print(f"Error. Upper Specification Limit ({USL}) is equal to Lower Specification Limit ({LSL}).")

    # Update dataframe
    data.rename(columns={0: "value"}, inplace=True)

    # Validate that there are no negative values
    if min(data["value"]) < 0:
        return print("Error. The data set contains at least one negative value. All values must be non-negative.")

    # Transform data using Box-Cox
    data["value_transformed"], lambda_value = stats.boxcox(data["value"])

    # Calculate Moving Range
    data["MR"] = abs(data["value_transformed"].diff())

    # Calculate CL-bar and MR-bar
    CL_bar = data["value_transformed"].mean()
    MR_bar = data["MR"].mean()

    # I-MR chart (logic applicable when subgroup size is equal to 1)
    if subgroup_size == 1:
        # Calculate Upper Control Limit (UCL) and Lower Control Limit (LCL)
        I_UCL = CL_bar + (2.66 * MR_bar)
        I_LCL = CL_bar - (2.66 * MR_bar)
        MR_UCL = 3.267 * MR_bar
        MR_LCL = 0 * MR_bar

        pdf_io = BytesIO()
        with PdfPages(pdf_io) as pdf:
            # Single page (A4 landscape): I chart, MR chart, Normality plot + table
            fig, axs = plt.subplot_mosaic([
                ["I", "I"],
                ["MR", "MR"],
                ["Normality", "Normality Test"]],
                figsize=(11.69, 8.27))  # A4 size in inches for landscape

            # Increase the space between the plots
            plt.tight_layout()
            plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1, hspace=0.8, wspace=0.5)
            plt.suptitle(f"{title}", fontsize=16, y=0.96)

            # Plot I chart
            axs["I"].plot(data["value_transformed"], linestyle="-", marker="o", color="black")
            axs["I"].axhline(CL_bar, color="green", label="Mean")
            axs["I"].axhline(I_UCL, color="#A50021", label="UCL")
            axs["I"].axhline(I_LCL, color="#A50021", label="LCL")
            axs["I"].set_title("I Chart (Transformed)")
            axs["I"].set_ylabel("Individual Value")
            axs["I"].grid(True)

            # Plot MR chart
            axs["MR"].plot(data["MR"], linestyle="-", marker="o", color="black")
            axs["MR"].axhline(MR_bar, color="green", label="Mean")
            axs["MR"].axhline(MR_UCL, color="#A50021", label="UCL")
            axs["MR"].axhline(MR_LCL, color="#A50021", label="LCL")
            axs["MR"].set_title("MR Chart (Transformed)")
            axs["MR"].set_ylabel("Moving Range")
            axs["MR"].grid(True)

            # Normality Plot
            probplot(data["value_transformed"], dist="norm", plot=axs["Normality"])
            axs["Normality"].set_title(f"Normality Plot (λ = {round(lambda_value, 2)})")

            # Normality Test Table
            _, p_value_normaltest = stats.normaltest(data["value_transformed"])
            normality_pass = "Pass" if p_value_normaltest > 0.05 else "Fail"
            table_data = [["Normality Test Result", normality_pass],
                          ["p-value", f"{p_value_normaltest:.4f}"]]
            table = axs["Normality Test"].table(cellText=table_data, cellLoc='left', loc='center')
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            for key, cell in table.get_celld().items():
                if key[1] == 0:  # key[1] corresponds to the column index
                    cell.set_text_props(fontweight='bold')
                cell.set_height(0.18)
            axs["Normality Test"].set_title("Normality Test (Transformed)")
            axs["Normality Test"].axis('tight')
            axs["Normality Test"].axis('off')

            # Adjust layout to add padding around the content
            plt.tight_layout()
            plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1, hspace=0.6, wspace=0.1)

            pdf.savefig(fig)
            plt.close(fig)

            fig, axs = plt.subplot_mosaic([
                ["Normal", "Process Table"],
                ["Transformed", "Capability Table"]],
                figsize=(11.69, 8.27))  # A4 size in inches for landscape
            plt.tight_layout()
            plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1, hspace=0.6, wspace=0.1)

            # Plot Normality Plot (Q-Q plot) in the "Normal" section of the mosaic
            sns.histplot(data["value"], kde=True, ax=axs["Normal"], bins=30, color="#7DA7D9", edgecolor="black",
                         stat="density")

            # Add vertical lines for target, LSL, and USL
            axs["Normal"].axvline(target, linestyle="--", color="green")
            axs["Normal"].axvline(LSL, linestyle="--", color="#A50021")
            axs["Normal"].axvline(USL, linestyle="--", color="#A50021")

            label_xpad = (USL - LSL) * 0.03
            label_ypad = (axs["Normal"].get_ylim()[1]) * 0.01
            # Add annotations for Target, LSL, and USL
            axs["Normal"].annotate("Target", xy=(target + label_xpad, 0 + label_ypad), color="green")
            axs["Normal"].annotate("LSL", xy=(LSL + label_xpad, 0 + label_ypad), color="#A50021")
            axs["Normal"].annotate("USL", xy=(USL - (label_xpad * 7), 0 + label_ypad), color="#A50021")

            # Set the title and labels for the "Normal" plot
            axs["Normal"].set_title("Capability Histogram", pad=20)
            axs["Normal"].set_xlabel("")
            axs["Normal"].set_ylabel("")
            axs["Normal"].grid(color="lightgray", linestyle="--", linewidth=0.5)

            # Box-Cox transformed LSL and USL
            LSL_transformed = stats.boxcox([LSL, USL])[0][0]
            USL_transformed = stats.boxcox([LSL, USL])[0][1]

            # Plot for Transformed Data
            sns.histplot(data["value_transformed"], kde=True, ax=axs["Transformed"], bins=15, color="#7DA7D9",
                         edgecolor="black", stat="density")
            axs["Transformed"].axvline(LSL_transformed, linestyle="--", color="#A50021")
            axs["Transformed"].axvline(USL_transformed, linestyle="--", color="#A50021")

            # Add annotations for transformed LSL and USL
            axs["Transformed"].annotate("USL", xy=(USL_transformed - 0.5, 0), color="#A50021")
            axs["Transformed"].annotate("LSL", xy=(LSL_transformed - 0.5, 0), color="#A50021")

            # Set the title and labels for the "Transformed" plot
            axs["Transformed"].set_title("Transformed Data", pad=20)
            axs["Transformed"].set_xlabel("")
            axs["Transformed"].set_ylabel("")
            axs["Transformed"].grid(color="lightgray", linestyle="--", linewidth=0.5)

            # Calculate process capability indices Pp and Ppk
            Pp = round((USL_transformed - LSL_transformed) / (6 * np.std(data["value_transformed"], ddof=1)), 2)
            Ppk = round(min((USL_transformed - np.mean(data["value_transformed"])) / (
                        3 * np.std(data["value_transformed"], ddof=1)),
                            (np.mean(data["value_transformed"]) - LSL_transformed) / (
                                        3 * np.std(data["value_transformed"], ddof=1))), 2)

            process_characterization_df = pd.DataFrame({
                "Total N": [len(data["value"])],
                "Subgroup size": subgroup_size,
                "Mean": round(CL_bar, 2),
                "Standard deviation (overall)": round(np.std(data["value_transformed"], ddof=1), 5)
            }).T

            process_characterization_df.rename(columns={0: "Value"}, inplace=True)

            # Generate Process Capability dataframe
            process_capability_df = pd.DataFrame({
                "Pp": [Pp],
                "Ppk": Ppk,
                "% Out of spec (observed)": len(data[data["value"] > USL]["value"]) + len(
                    data[data["value"] < LSL]["value"]),
                "PPM (DPMO) (observed)": (len(data[data["value"] > USL]["value"]) + len(
                    data[data["value"] < LSL]["value"])) * 10000
            }).T

            process_capability_df.rename(columns={0: "Value"}, inplace=True)

            # Convert process_characterization_df to a table and add it to the "Process Table" subplot
            process_characterization_table = axs["Process Table"].table(
                cellText=process_characterization_df.values,
                rowLabels=process_characterization_df.index,
                colLabels=process_characterization_df.columns,
                cellLoc='left',
                loc='center',
                colWidths=[0.2, 0.25],
                bbox=[0.55, 0.5, 0.5, 0.5]
            )
            axs["Process Table"].axis('off')  # Hide the axis for the table
            process_characterization_table.scale(1, 1)  # Scale the table to fit the subplot
            axs["Process Table"].set_title("Process Characterization", pad=20)

            # Add Process Capability table to the "Capability Table" subplot
            process_capability_table = axs["Capability Table"].table(
                cellText=process_capability_df.values,
                rowLabels=process_capability_df.index,
                colLabels=process_capability_df.columns,
                cellLoc='left',
                loc='center',
                colWidths=[0.2, 0.25],
                bbox=[0.55, 0.5, 0.5, 0.5]
            )
            axs["Capability Table"].axis('off')  # Hide the axis for the table
            axs["Capability Table"].set_title("Process Capability", pad=20)

            pdf.savefig(fig)
            plt.close(fig)

        pdf_io.seek(0)
        return pdf_io
    else:
        pass
        # TODO: calculate everything when subgroups are not of equal size
