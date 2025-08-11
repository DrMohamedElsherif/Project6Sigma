from io import BytesIO
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from ...constants import TABLE_BG_COLOR_GREY, TABLE_EDGE_COLOR
from ....utils.pdf_utils import add_header_or_footer_to_a4_portrait

header_image_path = 'assets/img/Header.png'
footer_image_path = 'assets/img/Footer.png'

from api.schemas import BusinessLogicException


def P_chart(data, title, acceptable_percent=0, subgroup_size=1, projectNumber=None):

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
            figsize=(8.27, 11.69), dpi=300)  # A4 size in inches for landscape

        plt.tight_layout()
        plt.subplots_adjust(left=0.1, right=0.9, top=0.85, bottom=0.15, hspace=0.2, wspace=0.5)
        fig.suptitle(title, fontsize=14, y=0.92, ha='left', x=0.1)
        header_ax = add_header_or_footer_to_a4_portrait(fig, header_image_path, position='header')
        footer_ax = add_header_or_footer_to_a4_portrait(fig, footer_image_path, position='footer', page_number=1, total_pages=2, projectNumber=projectNumber if projectNumber else None)

        # Plot P chart
        axs["P"].plot(data["p"], color='black', marker="o", lw=0.5, zorder=3)
        axs["P"].plot(data[data["p"] > UCL]["p"], linestyle="", marker="s", color="red", zorder=3)
        axs["P"].plot(data[data["p"] < LCL]["p"], linestyle="", marker="s", color="red", zorder=3)
        axs["P"].axhline(np.mean(data["p"]), color="grey", label="Target", linestyle="dashed", zorder=1)
        axs["P"].axhline(UCL, color="#a03130", label="UCL")
        axs["P"].axhline(LCL, color="#a03130", label="LCL")
        axs["P"].set_title("P Chart")
        axs["P"].set_ylabel("Proportion")
        axs["P"].grid(True, alpha=0.3, zorder=0)

        # Plot Cumulative % Defective chart
        axs["Cumulative % Defective"].plot(data["p"].expanding().mean(), color='black', marker="o", lw=0.5, zorder=3)
        axs["Cumulative % Defective"].axhline(data["p"].mean(), linestyle="--", color="grey", zorder=1)
        axs["Cumulative % Defective"].set_title("% Cumulative Defective")
        axs["Cumulative % Defective"].set_xlabel("Subgroup")
        axs["Cumulative % Defective"].set_ylabel("% Defective")
        axs["Cumulative % Defective"].grid(True, alpha=0.3, zorder=0)

        pdf.savefig(fig)
        plt.close(fig)

        # Second page: Process Characterization and Capability Tables
        fig, axs = plt.subplot_mosaic([
            ["Histogram", "Probability Plot"],
            ["Process Characterization", "Process Capability"]],
            figsize=(8.27, 11.69), dpi=300)  # A4 size in inches for landscape
        plt.subplots_adjust(left=0.1, right=0.9, top=0.85, bottom=0.15, hspace=0.6, wspace=0.1)

        header_ax = add_header_or_footer_to_a4_portrait(fig, header_image_path, position='header')
        footer_ax = add_header_or_footer_to_a4_portrait(fig, footer_image_path, position='footer', page_number=2, total_pages=2, projectNumber=projectNumber if projectNumber else None)

        # Plot histogram of observed % defective per subgroup
        axs["Histogram"].hist(data["p"] * 100, color="#95b92a", edgecolor="black", bins=12, zorder=3)
        axs["Histogram"].axvline(acceptable_percent, linestyle="--", color="grey", label="Target", zorder=3)
        axs["Histogram"].annotate(f"{acceptable_percent}%", xy=(acceptable_percent * 1.03, axs['Histogram'].get_ylim()[1] *0.95), color="grey")
        axs["Histogram"].set_title("Observed % Defective per Subgroup")
        axs["Histogram"].grid(True, alpha=0.3, zorder=0)

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

        # Set edge color for process_characterization_table
        for cell in process_characterization_table.get_celld().values():
            cell.set_edgecolor(TABLE_EDGE_COLOR)
        process_characterization_table.auto_set_font_size(False)
        process_characterization_table.set_fontsize(8)

        # Set the top-left cell background color to TABLE_BG_COLOR_GREY
        process_characterization_table[(0, 0)].set_facecolor(TABLE_BG_COLOR_GREY)
        
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

        # Set edge color for process_capability_table
        for cell in process_capability_table.get_celld().values():
            cell.set_edgecolor(TABLE_EDGE_COLOR)
        process_capability_table.auto_set_font_size(False)
        process_capability_table.set_fontsize(8)

        process_capability_table[(0, 0)].set_facecolor(TABLE_BG_COLOR_GREY)  
        
        axs["Process Capability"].axis('off')
        axs["Process Capability"].set_title("Process Capability", pad=20)

        # Hide the Probability Plot section for now
        axs["Probability Plot"].axis('off')

        pdf.savefig(fig)
        plt.close(fig)

    pdf_io.seek(0)
    plt.close('all')
    return pdf_io
