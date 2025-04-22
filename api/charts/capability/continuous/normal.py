from io import BytesIO
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from scipy.stats import normaltest, probplot
from statsmodels.graphics.gofplots import qqplot
from ...constants import TABLE_EDGE_COLOR, TABLE_BG_COLOR_GREY
from ....utils.pdf_utils import add_header_or_footer_to_a4_portrait

header_image_path = 'assets/img/Header.png'
footer_image_path = 'assets/img/Footer.png'

def I_MR_chart(data, title, target=0, subgroup_size=1, LSL=None, USL=None):
    """
    data: 'pandas DataFrame'
    target: 'int | float' = 0
    subgroup_size: 'int' = 1
    LSL: 'int | float | None' = None
    USL: 'int | float | None' = None

    Parameters
    ----------
    data : pandas DataFrame object
        DataFrame containing continuous values in a single column.
        All values must be non-negative.
    target : int or float
        Target value. Value must be greater or equal to zero.
    subgroup_size : int
        Amount of units per sampled group.
    LSL : int, float, or None
        Lower Specification Limit.
        If provided, value must be non-negative and lower than target
        and lower than Upper Specification Limit (USL) if USL is also provided.
    USL : int, float, or None
        Upper Specification Limit.
        If provided, value must be non-negative and greater than target
        and greater than Lower Specification Limit (LSL) if LSL is also provided.
    """

    from api.schemas import BusinessLogicException

    # Validate target
    if target < 0:
        raise BusinessLogicException(
            error_code="error_must_be_positive",
            field="target",
            details={"message": "A non-negative target value must be specified"}
        )

    # Validate subgroup_size
    if subgroup_size <= 0:
        raise BusinessLogicException(
            error_code="error_must_be_positive",
            field="subgroup_size",
            details={"message": "The subgroup size must be a positive value greater than zero"}
        )

    # Validate LSL
    if LSL is not None:
        if LSL < 0:
            raise BusinessLogicException(
                error_code="error_must_be_positive",
                field="lower_bound",
                details={"message": "Lower Specification Limit (LSL) must be non-negative"}
            )
        if target < LSL:
            raise BusinessLogicException(
                error_code="error_target_below_lsl",
                field="target",
                details={"message": f"Target value ({target}) is lower than Lower Specification Limit ({LSL})"}
            )

    # Validate USL
    if USL is not None:
        if USL < 0:
            raise BusinessLogicException(
                error_code="error_must_be_positive",
                field="upper_bound",
                details={"message": "Upper Specification Limit (USL) must be non-negative"}
            )
        if target > USL:
            raise BusinessLogicException(
                error_code="error_target_above_usl",
                field="target",
                details={"message": f"Target value ({target}) is greater than Upper Specification Limit ({USL})"}
            )

    # Validate LSL and USL relationship
    if LSL is not None and USL is not None:
        if USL <= LSL:
            raise BusinessLogicException(
                error_code="error_invalid_bounds",
                field="bounds",
                details={"message": f"Upper Specification Limit ({USL}) must be greater than Lower Specification Limit ({LSL})"}
            )

    # Update dataframe
    data.rename(columns={0: "value"}, inplace=True)

    # Validate dataset values
    if min(data["value"]) < 0:
        raise BusinessLogicException(
            error_code="error_negative_values_in_dataset",
            field="values",
            details={"message": "The data set contains at least one negative value. All values must be non-negative"}
        )

    # Rest of the I_MR_chart implementation...

    # Calculate Moving Range
    data["MR"] = abs(data["value"].diff())

    # Calculate CL-bar and MR-bar
    CL_bar = data["value"].mean()
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
                figsize=(8.27, 11.69), dpi=300)  # A4 size in inches for landscape

            # Increase the space between the plots
            plt.tight_layout()
            plt.subplots_adjust(left=0.15, right=0.85, top=0.9, bottom=0.1, hspace=0.8, wspace=0.5)
            fig.suptitle(title, fontsize=14, y=0.92, ha='left', x=0.1)
            
            header_ax = add_header_or_footer_to_a4_portrait(fig, header_image_path, position='header')
            footer_ax = add_header_or_footer_to_a4_portrait(fig, footer_image_path, position='footer', page_number=1, total_pages=2)

            # Plot I chart
            axs["I"].plot(data["value"], color='black', marker="o", lw=0.5)
            axs["I"].axhline(CL_bar, color="grey", label="Mean", linestyle='dashed', alpha=0.7)
            axs["I"].axhline(I_UCL, color="#a03130", label="UCL", lw=0.5)
            axs["I"].axhline(I_LCL, color="#a03130", label="LCL", lw=0.5)
            
            # Mark points outside control limits with a square marker
            out_of_control = (data["value"] > I_UCL) | (data["value"] < I_LCL)
            axs["I"].scatter(data.index[out_of_control], data["value"][out_of_control], 
                             color='red', marker='s', label="Out of Control")

            axs["I"].set_title("I Chart")
            axs["I"].set_ylabel("Individual Value")
            axs["I"].grid(True, alpha=0.3)

            # Plot MR chart
            axs["MR"].plot(data["MR"], color='black', marker="o", lw=0.5)
            axs["MR"].axhline(MR_bar, color="grey", label="Mean", linestyle='dashed', alpha=0.7)
            axs["MR"].axhline(MR_UCL, color="#a03130", label="UCL", lw=0.5)
            axs["MR"].axhline(MR_LCL, color="#a03130", label="LCL", lw=0.5)

            # Mark points outside control limits with a square marker
            out_of_control_mr = (data["MR"] > MR_UCL) | (data["MR"] < MR_LCL)
            axs["MR"].plot(data.index[out_of_control_mr], data["MR"][out_of_control_mr], 
                              color='red', marker='s', label="Out of Control")

            axs["MR"].set_title("MR Chart")
            axs["MR"].set_ylabel("Moving Range")
            axs["MR"].grid(True, alpha=0.3)

            # Normality Plot
            probplot(data["value"], dist="norm", plot=axs["Normality"])
            axs["Normality"].lines[0].set_color('#95b92a')  # Change the color of the data points
            axs["Normality"].lines[1].set_color('black')  # Change the color of the best-fit line
            axs["Normality"].set_title("Normality Plot")
            axs["Normality"].grid(True, alpha=0.3)

            # Normality Test Table
            _, p_value_normaltest = normaltest(data["value"])
            normality_pass = "Pass" if p_value_normaltest > 0.05 else "Fail"
            table_data = [["Normality Test Result", normality_pass],
                          ["p-value", f"{p_value_normaltest:.4f}"]]
            table = axs["Normality Test"].table(cellText=table_data, cellLoc='center', loc='center')
            table.auto_set_font_size(False)
            table.set_fontsize(8)
            for key, cell in table.get_celld().items():
                if key[1] == 0:  # key[1] corresponds to the column index
                    cell.set_text_props(fontweight='bold')
                cell.set_height(0.18)
                if key[0] == 0:
                    cell.set_facecolor(TABLE_BG_COLOR_GREY)
            for cell in table._cells.values():
                cell.set_edgecolor(TABLE_EDGE_COLOR)
                cell.set_linewidth(0.5)
            axs["Normality Test"].set_title("Normality Test")
            axs["Normality Test"].axis('tight')
            axs["Normality Test"].axis('off')

            # Adjust layout to add padding around the content
            plt.tight_layout()
            plt.subplots_adjust(left=0.1, right=0.9, top=0.85, bottom=0.1, hspace=0.6, wspace=0.1)

            pdf.savefig(fig)
            plt.close(fig)

            fig, axs = plt.subplot_mosaic([
                ["Normal", "Normal"],
                ["Process Table", "Capability Table"]],
                figsize=(8.27, 11.69), dpi=300)  # A4 size in inches for landscape
            plt.tight_layout()
            plt.subplots_adjust(left=0.1, right=0.9, top=0.85, bottom=0.1, hspace=0.4, wspace=0.1)

            header_ax = add_header_or_footer_to_a4_portrait(fig, header_image_path, position='header')
            footer_ax = add_header_or_footer_to_a4_portrait(fig, footer_image_path, position='footer', page_number=2, total_pages=2)

            # Plot Normality Plot (Q-Q plot) in the "Normal" section of the mosaic
            sns.histplot(data["value"], ax=axs["Normal"], color="#95b92a", edgecolor="black", stat="density", alpha=1)
            sns.kdeplot(data['value'], ax=axs["Normal"], color="#a03130", lw=1.0)

            # Add vertical lines for target and LSL/USL if provided
            axs["Normal"].axvline(target, linestyle="--", color="grey")
            if LSL is not None:
                axs["Normal"].axvline(LSL, linestyle="--", color="#a03130")
            if USL is not None:
                axs["Normal"].axvline(USL, linestyle="--", color="#a03130")

            label_xpad = (max(data["value"]) - min(data["value"])) * 0.03
            label_ypad = (axs["Normal"].get_ylim()[1]) * 0.04
            # Add annotations for Target and LSL/USL if provided
            axs["Normal"].annotate("Target", xy=(target + label_xpad, axs["Normal"].get_ylim()[1] - label_ypad), color="grey")
            if LSL is not None:
                axs["Normal"].annotate("LSL", xy=(LSL + label_xpad, axs["Normal"].get_ylim()[1] - label_ypad), color="#a03130")
            if USL is not None:
                axs["Normal"].annotate("USL", xy=(USL - (label_xpad * 5), axs["Normal"].get_ylim()[1] - label_ypad), color="#a03130")

            # Set the title and labels for the "Normal" plot
            axs["Normal"].set_title("Capability Histogram", pad=20)
            axs["Normal"].set_xlabel("")
            axs["Normal"].set_ylabel("")
            axs["Normal"].grid(color="lightgray", linestyle="--", linewidth=0.5)

            process_characterization_df = pd.DataFrame({
                "Total N": [len(data["value"])],
                "Subgroup size": subgroup_size,
                "Mean": round(CL_bar, 2),
                "Standard deviation (overall)": round(np.std(data["value"], ddof=1), 5)
            }).T

            process_characterization_df.rename(columns={0: "Value"}, inplace=True)

            # Adjust process capability calculations
            if LSL is None and USL is None:
                Pp = "N/A"
                Ppk = "N/A"
                out_of_spec = 0
                ppm = 0
            elif LSL is None:
                Pp = "N/A"
                Ppk = round((USL - np.mean(data["value"])) / (3 * np.std(data["value"], ddof=1)), 2)
                out_of_spec = len(data[data["value"] > USL])
                ppm = out_of_spec * 1000000 / len(data)
            elif USL is None:
                Pp = "N/A"
                Ppk = round((np.mean(data["value"]) - LSL) / (3 * np.std(data["value"], ddof=1)), 2)
                out_of_spec = len(data[data["value"] < LSL])
                ppm = out_of_spec * 1000000 / len(data)
            else:
                Pp = round((USL - LSL) / (6 * np.std(data["value"], ddof=1)), 2)
                Ppk = round(min((USL - np.mean(data["value"])) / (3 * np.std(data["value"], ddof=1)),
                                (np.mean(data["value"]) - LSL) / (3 * np.std(data["value"], ddof=1))), 2)
                out_of_spec = len(data[data["value"] > USL]) + len(data[data["value"] < LSL])
                ppm = out_of_spec * 1000000 / len(data)

            # Generate Process Capability dataframe
            process_capability_df = pd.DataFrame({
                "Pp": [Pp],
                "Ppk": [Ppk],
                "% Out of spec (observed)": [out_of_spec],
                "PPM (DPMO) (observed)": [ppm]
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
                bbox=[0.55, 0.5, 0.35, 0.4]
            )
            axs["Process Table"].axis('off')  # Hide the axis for the table
            process_characterization_table.scale(1, 1)  # Scale the table to fit the subplot
            axs["Process Table"].set_title("Process Characterization", pad=20)

            # Set edge color for process_characterization_table
            for cell in process_characterization_table.get_celld().values():
                cell.set_edgecolor(TABLE_EDGE_COLOR)
            process_characterization_table.auto_set_font_size(False)
            process_characterization_table.set_fontsize(8)

            # Set the top-left cell background color to TABLE_BG_COLOR_GREY
            process_characterization_table[(0, 0)].set_facecolor(TABLE_BG_COLOR_GREY)

            # Add Process Capability table to the "Capability Table" subplot
            process_capability_table = axs["Capability Table"].table(
                cellText=process_capability_df.values,
                rowLabels=process_capability_df.index,
                colLabels=process_capability_df.columns,
                cellLoc='left',
                loc='center',
                colWidths=[0.2, 0.25],
                bbox=[0.55, 0.5, 0.35, 0.4]
            )
            axs["Capability Table"].axis('off')  # Hide the axis for the table
            axs["Capability Table"].set_title("Process Capability", pad=20)

            # Set edge color for process_capability_table
            for cell in process_capability_table.get_celld().values():
                cell.set_edgecolor(TABLE_EDGE_COLOR)
            process_capability_table.auto_set_font_size(False)
            process_capability_table.set_fontsize(8)

            process_capability_table[(0, 0)].set_facecolor(TABLE_BG_COLOR_GREY)        

            pdf.savefig(fig)
            plt.close(fig)

        pdf_io.seek(0)
        plt.close('all')
        return pdf_io

    else:
        pass
        # TODO: calculate everything when subgroups are not of equal size