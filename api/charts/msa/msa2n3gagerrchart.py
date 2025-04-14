from typing import List, Optional

import io
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from pydantic import BaseModel, Field
from matplotlib.backends.backend_pdf import PdfPages
from ..constants import FIGURE_SIZE_A4_PORTRAIT, COLOR_PALETTE
from ...utils.pdf_utils import add_header_or_footer_to_a4_portrait

header_image_path = 'assets/img/Header.png'
footer_image_path = 'assets/img/Footer.png'

from api.schemas import BusinessLogicException


class MSA2GagerrConfig(BaseModel):
    title: str
    labelx: str = Field(..., description="Label for x-axis (Operator or Device)")


class MSA2GagerrData(BaseModel):
    parts: List[int] = Field(..., min_length=1)
    operators: Optional[List[str]] = None
    devices: Optional[List[str]] = None
    values: List[float] = Field(..., min_length=1)


class MSA2GagerrRequest(BaseModel):
    project: str
    step: str
    config: MSA2GagerrConfig
    data: MSA2GagerrData


class MSA2n3GagerrChart:
    def __init__(self, data: dict):
        try:
            if not isinstance(data, dict):
                raise ValueError("Request must be a JSON object")
            for field in ['project', 'step', 'config', 'data']:
                if field not in data:
                    raise ValueError(field)

            # Validate config fields
            if 'config' in data and isinstance(data['config'], dict):
                if 'labelx' not in data['config']:
                    raise ValueError("config.labelx")
                if not data['config']['labelx']:
                    raise ValueError("config.labelx")

            # Check operators/devices data types before pydantic validation
            if 'data' in data and isinstance(data['data'], dict):
                if 'operators' in data['data'] and data['data']['operators'] is not None:
                    if not all(isinstance(x, str) for x in data['data']['operators']):
                        raise ValueError("data.operators.type")
                if 'devices' in data['data'] and data['data']['devices'] is not None:
                    if not all(isinstance(x, str) for x in data['data']['devices']):
                        raise ValueError("data.devices.type")

            validated_data = MSA2GagerrRequest(**data)
            self.project = validated_data.project
            self.step = validated_data.step
            self.config = validated_data.config
            self.data = validated_data.data
            self.message = ""
            self.figure = None

        except ValueError as e:
            error_msg = str(e)

            if "int_from_float" in error_msg:
                error_code = "error_must_be_integer"
            else:
                error_code = "error_validation"

            # Map error message to correct field
            if "config.labelx" in error_msg:
                field = "labelx"
            elif "data.parts" in error_msg:
                field = "parts"
            elif "data.values" in error_msg:
                field = "values"
            elif "data.operators" in error_msg or "data.operators.type" in error_msg:
                field = "operators"
            elif "data.devices" in error_msg or "data.devices.type" in error_msg:
                field = "devices"
            else:
                field = error_msg.split("\n")[1].split(".")[0] if "\n" in error_msg else "data"

            raise BusinessLogicException(
                error_code=error_code,
                field=field,
                details={"message": "Invalid or missing field."}
            )

    def process(self):
        title = self.config.title
        values = self.data.values
        parts = self.data.parts

        if self.data.operators:
            operators = self.data.operators
        elif self.data.devices:
            operators = self.data.devices
        else:
            raise BusinessLogicException(
                error_code="error_no_operators_devices",
                field="operators" if self.data.operators else "devices",
                details={"message": "Either operators or devices must be provided."}
            )

        label = self.config.labelx

        if not (len(parts) == len(operators) == len(values)):
            raise BusinessLogicException(
                error_code="error_data_length_mismatch",
                field="values",
                details={"message": "Data length mismatch"}
            )

        # Create DataFrame
        data = pd.DataFrame({
            "Part": parts,
            "Operator": operators,
            "Value": values
        })


        # Basic data structure validations
        operators_count = data["Operator"].nunique()
        parts_count = data["Part"].nunique()

        if operators_count < 2:
            raise BusinessLogicException(
                error_code="error_insufficient_operators_devices",
                field="operators",
                details={"message": "At least 2 operators/devices are required for Gage R&R"}
            )

        if parts_count < 2:
            raise BusinessLogicException(
                error_code="error_insufficient_parts_gage_rr",
                field="parts",
                details={"message": "At least 2 parts are required for Gage R&R"}
            )

        # Validate measurements per part/operator
        measurements_per_part = data.groupby(['Part', 'Operator']).size()
        if not measurements_per_part.nunique() == 1:
            raise BusinessLogicException(
                error_code="error_uneven_measurements",
                field="values",
                details={"message": "Each operator must measure each part the same number of times"}
            )

        num_measurements = measurements_per_part.iloc[0]
        if num_measurements < 2:
            raise BusinessLogicException(
                error_code="error_insufficient_measurements",
                field="values",
                details={"message": "At least 2 measurements per part per operator are required"}
            )

        # # Validate data completeness
        # expected_total = parts_count * operators_count * num_measurements
        # if len(data) != expected_total:
        #     raise BusinessLogicException(
        #         error_code="error_data_length_mismatch",
        #         field="values",
        #         details={"message": "Data length does not match the expected number of measurements"}
        #     )

        # Check for missing or invalid values
        if data['Value'].isna().any():
            raise BusinessLogicException(
                error_code="error_missing_values",
                field="values",
                details={"message": "Dataset contains missing values"}
            )

        # Sort and reset index
        data = data.sort_values(["Part", "Operator"])
        data.reset_index(inplace=True, drop=True)

        # Assign "Measurement" column
        num_measurements = data["Part"].value_counts().iloc[0]
        data["Measurement"] = list(np.arange(1, num_measurements + 1)) * (len(data) // num_measurements)

        # # Plot Gage Run Chart
        # g = sns.relplot(
        #     data=data,
        #     x="Measurement",
        #     y="Value",
        #     hue="Operator",
        #     style="Operator",
        #     col="Part",
        #     col_wrap=5,
        #     aspect=0.7,
        #     kind='line',
        #     palette=COLOR_PALETTE,
        #     markers=True,
        #     dashes=False
        # )
        # g.figure.set_size_inches(FIGURE_SIZE_A4_PORTRAIT)
        # #g.figure.suptitle(title, fontsize=16)
        # header_ax = add_header_or_footer_to_a4_portrait(g.figure, header_image_path, position='header')
        # footer_ax = add_header_or_footer_to_a4_portrait(g.figure, footer_image_path, position='footer', page_number=1, total_pages=1)
        # g.map(plt.axhline, y=data["Value"].mean(), color=".7", dashes=(2, 1), zorder=0)
        # g.set_axis_labels("Measurement", "Value")

        # g.legend.set_title(f"{label}")
        # legend = g._legend

        # # Adjust legend position
        # legend.set_bbox_to_anchor((0.5, 0.06))
        # legend.set_loc('lower center')
        # plt.setp(legend.get_texts(), fontsize=12)
        # plt.setp(legend.get_title(), fontsize=14)

        # plt.subplots_adjust(top=0.85, bottom=0.2)

        # self.figure = g.figure  # Save the matplotlib figure instead of the FacetGrid
        # plt.close('all')
        # return self.figure

        pdf_io = io.BytesIO()

        with PdfPages(pdf_io) as pdf:
            # Calculate number of parts to determine layout
            parts_list = sorted(data['Part'].unique())
            n_parts = len(parts_list)
            
            # Determine grid dimensions (try to make it somewhat square)
            n_cols = min(4, n_parts)  # Maximum 5 columns
            n_rows = int(np.ceil(n_parts / n_cols))
            
            # Create a single figure with subplots grid and high DPI
            fig, axes = plt.subplots(n_rows, n_cols, figsize=FIGURE_SIZE_A4_PORTRAIT, dpi=300, sharey=True)
            fig.subplots_adjust(top=0.85, bottom=0.2, hspace=0.4, wspace=0.3)
            fig.suptitle(title, fontsize=14, y=0.92, ha='left', x=0.1)
            
            # Add header and footer to this figure
            add_header_or_footer_to_a4_portrait(fig, header_image_path, position='header')
            add_header_or_footer_to_a4_portrait(fig, footer_image_path, position='footer', page_number=1, total_pages=1)
            
            
            # Flatten axes array for easier iteration
            if n_rows > 1 or n_cols > 1:
                axes = axes.flatten()
            else:
                axes = [axes]
            
            # Draw a line plot in each subplot
            for i, part in enumerate(parts_list):
                if i < len(axes):
                    part_data = data[data['Part'] == part]
                    
                    # Create the line plot in this axis
                    sns.lineplot(
                        data=part_data,
                        x="Measurement",
                        y="Value",
                        hue="Operator",
                        style="Operator",
                        markers=True,
                        palette=COLOR_PALETTE,
                        ax=axes[i]
                    )
                    
                    # Add horizontal line at mean
                    axes[i].axhline(data["Value"].mean(), color=".7", dashes=(2, 1), zorder=0)
                    
                    # Set subplot title
                    axes[i].set_title(f'Part = {part}')
                    
                    # Only show y-label for leftmost plots
                    if i % n_cols != 0:
                        axes[i].set_ylabel('')
                    else:
                        axes[i].set_ylabel('Value')
                    
                    # Only show x-label for bottom plots
                    if i < (n_rows - 1) * n_cols:
                        axes[i].set_xlabel('')
                    else:
                        axes[i].set_xlabel('Measurement')
                        
                    # Remove legend from individual plots
                    axes[i].get_legend().remove()

                    # Remove right and top spines
                    axes[i].spines[['right', 'top']].set_visible(False)
            
            # Turn off any unused axes
            for j in range(i + 1, len(axes)):
                axes[j].axis('off')
            
            # Create a single legend for the entire figure
            handles, labels = axes[0].get_legend_handles_labels()
            legend = fig.legend(
                handles, labels, 
                title=label,
                loc='lower center', 
                bbox_to_anchor=(0.5, 0.1), 
                ncol=min(operators_count, 4)
            )
            legend.get_frame().set_linewidth(0)  # Remove the outline around the legend
            
            pdf.savefig(fig)
            plt.close(fig)

        pdf_io.seek(0)
        plt.close('all')
        return pdf_io

    def getProcessMessage(self):
        return self.message or "MSA2 Gage R&R chart generated successfully"
