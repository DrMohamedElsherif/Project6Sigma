from typing import List, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from pydantic import BaseModel, Field

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

            validated_data = MSA2GagerrRequest(**data)
            self.project = validated_data.project
            self.step = validated_data.step
            self.config = validated_data.config
            self.data = validated_data.data
            self.message = ""
            self.figure = None

        except ValueError as e:
            raise BusinessLogicException(
                error_code="error_validation",
                field=str(e),
                details={"message": f"Invalid or missing field: {str(e)}"}
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

        # Plot Gage Run Chart
        g = sns.relplot(
            data=data,
            x="Measurement",
            y="Value",
            hue="Operator",
            style="Operator",
            col="Part",
            col_wrap=5,
            aspect=0.7,
            kind='line',
            markers=True,
            dashes=False
        )
        g.fig.suptitle(title, fontsize=16)
        g.map(plt.axhline, y=data["Value"].mean(), color=".7", dashes=(2, 1), zorder=0)
        g.set_axis_labels("Measurement", "Value")

        g.legend.set_title(f"{label}")
        legend = g._legend
        plt.setp(legend.get_texts(), fontsize=12)
        plt.setp(legend.get_title(), fontsize=14)

        plt.tight_layout()

        plt.tight_layout()
        self.figure = g.figure  # Save the matplotlib figure instead of the FacetGrid
        plt.close('all')
        return self.figure

    def getProcessMessage(self):
        return self.message or "MSA2 Gage R&R chart generated successfully"
