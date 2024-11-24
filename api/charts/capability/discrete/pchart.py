from io import BytesIO
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from api.schemas import BusinessLogicException


def P_chart(data, title, acceptable_percent=0, subgroup_size=1):

    """
    data: 'pandas DataFrame'
    target: 'int' = 0
    subgroup_size: 'int' = 1

    Parameters
    ----------
    data : pandas DataFrame  object
        DataFrame containing continuous values in a single column.
        All values must be non-negative.
    acceptable_percent : int
        Target value. Value must be greater or equal to zero.
    subgroup_size : int
        Amount of units per sampled group.
    """

    if acceptable_percent < 0:
        raise BusinessLogicException(
            error_code="error_must_be_positive",
            field="acceptable_percent",
            details={"message": "A non-negative target value must be specified"}
        )
    if acceptable_percent % 1 != 0:
        raise BusinessLogicException(
            error_code="error_must_be_integer",
            field="acceptable_percent",
            details={"message": "A discrete value for acceptable_percent must be specified"}
        )

    # Validate subgroup_size
    if subgroup_size <= 0:
        raise BusinessLogicException(
            error_code="error_must_be_positive",
            field="subgroup_size",
            details={"message": "The subgroup size must be a positive value greater than zero"}
        )
    if subgroup_size % 1 != 0:
        raise BusinessLogicException(
            error_code="error_must_be_integer",
            field="subgroup_size",
            details={"message": "A discrete value for subgroup_size must be specified"}
        )

    # Update dataframe
    data.rename(columns={"value": "defects"}, inplace=True)

    # Validate that there are no negative values
    if min(data["defects"]) < 0:
        raise BusinessLogicException(
            error_code="error_negative_values_in_dataset",
            field="data",
            details={"message": "The data set contains at least one negative value. All values must be non-negative."}
        )

    # Calculate proportion of defective units per sample group
    data["p"] = round(data["defects"] / subgroup_size, 2)

    # Calculate P-bar, n-bar, Upper Control Limit (UCL) and Lower Control Limit (LCL)
    p_bar = np.sum(data["defects"]) / (len(data["defects"]) * subgroup_size)
    n_bar = (len(data["defects"]) * subgroup_size) / len(data["defects"])
    UCL = p_bar + (3 * np.sqrt((p_bar * (1 - p_bar)) / n_bar))
    LCL = max(0, p_bar - (3 * np.sqrt((p_bar * (1 - p_bar)) / n_bar)))

    # Create PDF report
    pdf_io = BytesIO()
    with PdfPages(pdf_io) as pdf:
        # First page (A4 landscape): P chart, Cumulative % Defective chart
        fig, axs = plt.subplot_mosaic([
            ["P", "P"],
            ["Cumulative % Defective", "Cumulative % Defective"]],
            figsize=(11.69, 8.27))  # A4 size in inches for landscape

        plt.tight_layout()
        plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1, hspace=0.8, wspace=0.5)
        plt.suptitle(f"{title}", fontsize=16, y=0.96)

        # Plot P chart
        axs["P"].plot(data["p"], linestyle="-", marker="o", color="black")
        axs["P"].plot(data[data["p"] > UCL]["p"], linestyle="", marker="s", color="red")
        axs["P"].plot(data[data["p"] < LCL]["p"], linestyle="", marker="s", color="red")
        axs["P"].axhline(np.mean(data["p"]), color="green", label="Target")
        axs["P"].axhline(UCL, color="red", label="UCL")
        axs["P"].axhline(LCL, color="red", label="LCL")
        axs["P"].set_title("P Chart")
        axs["P"].set_ylabel("Proportion")
        axs["P"].grid(True)

        # Plot Cumulative % Defective chart
        axs["Cumulative % Defective"].plot(data["p"].expanding().mean(), linestyle="-", marker="o", color="black")
        axs["Cumulative % Defective"].axhline(data["p"].mean(), linestyle="--", color="grey")
        axs["Cumulative % Defective"].set_title("% Cumulative Defective")
        axs["Cumulative % Defective"].set_xlabel("Subgroup")
        axs["Cumulative % Defective"].set_ylabel("% Defective")
        axs["Cumulative % Defective"].grid(color="gray", linewidth=0.5)

        pdf.savefig(fig)
        plt.close(fig)

        # Second page: Process Characterization and Capability Tables
        fig, axs = plt.subplot_mosaic([
            ["Histogram", "Probability Plot"],
            ["Process Characterization", "Process Capability"]],
            figsize=(11.69, 8.27))  # A4 size in inches for landscape
        plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1, hspace=0.6, wspace=0.1)

        # Plot histogram of observed % defective per subgroup
        axs["Histogram"].hist(data["p"] * 100, color="#7DA7D9", edgecolor="black", bins=12)
        axs["Histogram"].axvline(acceptable_percent, linestyle="--", color="green", label="Target")
        axs["Histogram"].annotate(f"{acceptable_percent}%", xy=(acceptable_percent, 0), color="green")
        axs["Histogram"].set_title("Observed % Defective per Subgroup")
        axs["Histogram"].grid(color="lightgray", linestyle="--", linewidth=0.5)

        # Generate Process Characterization dataframe
        process_characterization_df = pd.DataFrame({
            "Number of subgroups": [len(data["p"])],
            "Subgroup size": subgroup_size,
            "Total items tested": subgroup_size * len(data["p"]),
            "Number of defectives": sum(data["defects"])
        }).T

        process_characterization_df.rename(columns={0: "Value"}, inplace=True)

        # Generate Process Capability Overall dataframe
        process_capability_overall_df = pd.DataFrame({
            "% Defective": [round(np.mean(data['p']) * 100, 2)],
            "95% CI": f"({round(np.mean(data['p']) - (1.815 * (np.std(data['p'], ddof=1) / np.sqrt(len(data['defects'])))), 4) * 100}; "
                      f"{round(np.mean(data['p']) + (1.815 * (np.std(data['p'], ddof=1) / np.sqrt(len(data['defects'])))), 4) * 100})",
            "PPM (DPMO)": round(np.mean(data['p']) * 1000000, 0)
        }).T

        process_capability_overall_df.rename(columns={0: "Value"}, inplace=True)

        # Plot Process Characterization Table
        process_characterization_table = axs["Process Characterization"].table(
            cellText=process_characterization_df.values,
            rowLabels=process_characterization_df.index,
            colLabels=process_characterization_df.columns,
            cellLoc='left',
            loc='center',
            colWidths=[0.3, 0.25],
            bbox=[0.4, 0.38, 0.425, 0.6]
        )
        axs["Process Characterization"].axis('off')
        process_characterization_table.scale(1, 1)
        axs["Process Characterization"].set_title("Process Characterization", pad=20)

        # Plot Process Capability Table
        process_capability_table = axs["Process Capability"].table(
            cellText=process_capability_overall_df.values,
            rowLabels=process_capability_overall_df.index,
            colLabels=process_capability_overall_df.columns,
            cellLoc='left',
            loc='center',
            colWidths=[0.3, 0.25],
            bbox=[0.35, 0.5, 0.5, 0.5]
        )
        axs["Process Capability"].axis('off')
        axs["Process Capability"].set_title("Process Capability", pad=20)

        # Hide the Probability Plot section for now
        axs["Probability Plot"].axis('off')

        pdf.savefig(fig)
        plt.close(fig)

    pdf_io.seek(0)
    return pdf_io
