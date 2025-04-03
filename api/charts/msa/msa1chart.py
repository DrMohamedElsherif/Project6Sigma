import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.stats
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional, Dict, Any
from api.schemas import BusinessLogicException
from ..constants import FIGURE_SIZE_A4_PORTRAIT, TABLE_EDGE_COLOR
from ...utils.pdf_utils import add_header_or_footer_to_a4_portrait

header_image_path = 'assets/img/Header.png'
footer_image_path = 'assets/img/Footer.png'


class MSA1Config(BaseModel):
    title: Optional[str] = "MSA 1"
    reference: float
    tolerance: float = Field(gt=0)
    percentage_of_tolerance: float = Field(gt=0, le=1)


class MSA1Data(BaseModel):
    values: List[float] = Field(min_length=2)


class MSA1Request(BaseModel):
    project: str
    step: str
    config: MSA1Config
    data: MSA1Data


class MSA1Chart:
    def __init__(self, data: dict):
        try:
            # First validate core request structure
            if not isinstance(data, dict):
                raise ValueError("Request must be a JSON object")
            for field in ['project', 'step', 'config', 'data']:
                if field not in data:
                    raise ValueError(field)

            # Then validate config
            if not isinstance(data['config'], dict):
                raise ValueError("config")
            for field in ['reference', 'tolerance', 'percentage_of_tolerance']:
                if field not in data['config']:
                    raise ValueError(field)

            try:
                validated_data = MSA1Request(**data)
                self.project = validated_data.project
                self.step = validated_data.step
                self.config = validated_data.config
                self.data = validated_data.data
                self.message = ""
                self.figure = None
            except ValidationError as e:
                # Extract the field name from the error
                error_loc = e.errors()[0]['loc']
                field = error_loc[-1] if error_loc else "unknown"
                raise ValueError(field)

        except ValueError as e:
            raise BusinessLogicException(
                error_code="error_validation",
                field=str(e),
                details={"message": f"Invalid or missing field: {str(e)}"}
            )

    def process(self):
        title = self.config.title
        data = self.data.values
        reference = self.config.reference
        tolerance = self.config.tolerance
        percentage_of_tolerance = self.config.percentage_of_tolerance

        # Define Upper and Lower Control Limits
        UCL = reference + (0.1 * tolerance)
        LCL = reference - (0.1 * tolerance)

        if LCL >= UCL:
            raise BusinessLogicException(
                error_code="error_invalid_control_limits",
                field="tolerance",
                details={"message": "Invalid control limits: LCL must be less than UCL"}
            )

        below_LCL = [i for i in range(len(data)) if data[i] < LCL]
        above_UCL = [i for i in range(len(data)) if data[i] > UCL]

        # Plot Run chart
        self.figure, axs = plt.subplots(2, 1, figsize=(FIGURE_SIZE_A4_PORTRAIT), dpi=300)

        header_ax = add_header_or_footer_to_a4_portrait(self.figure, header_image_path, position='header')
        footer_ax = add_header_or_footer_to_a4_portrait(self.figure, footer_image_path, position='footer', page_number=1, total_pages=1)
            

        # Plot in the first row
        axs[0].plot(data, color='black', marker="o", lw=0.5, zorder=3)
        axs[0].plot(below_LCL, [data[i] for i in below_LCL], linestyle="", marker="s", color="red", zorder=5)
        axs[0].plot(above_UCL, [data[i] for i in above_UCL], linestyle="", marker="s", color="red", zorder=5)
        axs[0].axhline(reference, color="grey", label="Reference", linestyle="dashed")
        axs[0].axhline(UCL, color="#a03130", label="UCL")
        axs[0].axhline(LCL, color="#a03130", label="LCL")
        axs[0].axhline(np.median(data), color="#95b92a", linestyle="--", label="Median")
        axs[0].set_xlabel("Observation")
        axs[0].set_ylabel("Individual Value")
        axs[0].grid(True, alpha=0.3, zorder=0)
        axs[0].legend(loc='upper right', framealpha=1)

        # Calculate statistics
        mean_X = np.mean(data)
        std_dev = np.std(data, ddof=1)

        if std_dev == 0:
            raise BusinessLogicException(
                error_code="error_zero_variation",
                field="values",
                details={"message": "Standard deviation is zero. Data shows no variation"}
            )

        basic_statistics_df = pd.DataFrame({
            "Metric": ["Reference", "Mean", "StDev", "6 x StDev (SV)", "Tolerance (Tol)"],
            "Value": [reference, mean_X, std_dev, 6 * std_dev, tolerance]
        })

        # Calculate capability indices
        cg = (percentage_of_tolerance * tolerance) / (3 * std_dev)
        cgk = (percentage_of_tolerance * tolerance - (abs(mean_X - reference))) / (3 * std_dev)

        # Validate capability indices
        if cg <= 0 or cgk <= 0:
            raise BusinessLogicException(
                error_code="error_invalid_capability",
                field="values",
                details={"message": "Invalid capability indices."}
            )

        K = 20  # Constant for variance calculation
        bias = mean_X - reference
        t_statistic = abs(bias) / (std_dev / np.sqrt(len(data)))
        p_value = scipy.stats.t.sf(np.abs(t_statistic), len(data) - 1) * 2

        var_repeatability = round(K / cg, 2)
        var_repeatability_and_bias = round(K / cgk, 2)

        capability_df = pd.DataFrame({
            "Metric": ["Cg", "Cgk", "%Var(Repeatability)", "%Var(Rep. and Bias)"],
            "Value": [cg, cgk, var_repeatability, var_repeatability_and_bias]
        })

        bias_df = pd.DataFrame({
            "Metric": ["Bias", "T", "PValue"],
            "Value": [bias, t_statistic, p_value]
        })

        # Turn off axes for the tables
        axs[1].axis("off")

        # Create a new gridspec for two rows and two columns for the tables
        gs = axs[1].get_gridspec()
        subgs = gs[1].subgridspec(2, 2)  # 2 rows, 2 columns

        # Add subplots for the tables
        ax_tables = [
            self.figure.add_subplot(subgs[0, 0]),  # Top-left
            self.figure.add_subplot(subgs[0, 1]),  # Top-right
            self.figure.add_subplot(subgs[1, 0])   # Bottom-left
        ]

        # Turn off axes for all table subplots
        for ax in ax_tables:
            ax.axis("off")

        # Add titles above the tables
        ax_tables[0].set_title('Basic Statistics', fontsize=12, weight='bold')
        ax_tables[1].set_title('Bias Analysis', fontsize=12, weight='bold')
        ax_tables[2].set_title('Capability', fontsize=12, weight='bold')

        # Determine the maximum number of rows
        max_rows = max(len(basic_statistics_df), len(capability_df), len(bias_df))

        # Format and pad tables
        def add_empty_rows_and_format(df, max_rows):
            def format_value(metric, value):
                if metric in ["%Var(Repeatability)", "%Var(Rep. and Bias)"]:
                    return f"{value:.2f}"
                elif isinstance(value, (int, float)):
                    return f"{value:.8f}"
                return value

            df['Value'] = df.apply(lambda row: format_value(row['Metric'], row['Value']), axis=1)
            additional_rows = max_rows - len(df)
            empty_rows = pd.DataFrame({col: [''] * additional_rows for col in df.columns})
            return pd.concat([df, empty_rows], ignore_index=True)

        # Format tables
        tables_data = [
            add_empty_rows_and_format(basic_statistics_df, max_rows),
            add_empty_rows_and_format(bias_df, max_rows),
            add_empty_rows_and_format(capability_df, max_rows)
        ]

        # Add tables
        tables = []
        for idx, df in enumerate(tables_data):
            table = ax_tables[idx].table(cellText=df.values, colLabels=None,
                         cellLoc="left", loc="center", edges="closed", bbox=[0, 0, 1, 1])
            table.auto_set_font_size(False)
            table.set_fontsize(8)
            table.scale(1, 1.5)

            # Set edge color for the table
            for key, cell in table.get_celld().items():
                cell.set_edgecolor(TABLE_EDGE_COLOR)

            tables.append(table)

        plt.subplots_adjust(hspace=0.3, top=0.9, bottom=0.1, left=0.15, right=0.85)
        plt.close('all')

        return self.figure
