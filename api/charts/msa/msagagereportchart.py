import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import probscale
from scipy.optimize import curve_fit, OptimizeWarning, minimize_scalar
import io
from pydantic import BaseModel, Field
from typing import List, Optional
from api.schemas import BusinessLogicException


class MSAGageReportConfig(BaseModel):
    title: str
    trials: int = Field(..., gt=0)
    ucl: Optional[float] = None
    lcl: Optional[float] = None


class MSAGageReportData(BaseModel):
    parts: List[int] = Field(..., min_length=1)
    values: List[float] = Field(..., min_length=1)
    ok: List[int] = Field(..., min_length=1)


class MSAGageReportRequest(BaseModel):
    project: str
    step: str
    config: MSAGageReportConfig
    data: MSAGageReportData


class MsaGageReportChart:
    def __init__(self, data: dict):
        try:
            if not isinstance(data, dict):
                raise ValueError("Request must be a JSON object")
            for field in ['project', 'step', 'config', 'data']:
                if field not in data:
                    raise ValueError(field)

            validated_data = MSAGageReportRequest(**data)
            self.project = validated_data.project
            self.step = validated_data.step
            self.config = validated_data.config
            self.data = validated_data.data
            self.message = ""
            self.figure = None

        except ValueError as e:
            raise BusinessLogicException(
                error_code="validation_error",
                field=str(e),
                details={"message": f"Invalid or missing field: {str(e)}"}
            )

    def process(self):
        # Define data and parameters
        title = self.config.title
        parts = self.data.parts
        values = self.data.values
        ok = self.data.ok
        num_trials = self.config.trials
        lcl = self.config.lcl
        ucl = self.config.ucl

        # Validate control limits
        if lcl is not None and ucl is not None:
            raise BusinessLogicException(
                error_code="error_invalid_limits",
                field="limits",
                details={"message": "Cannot specify both LCL and UCL. Choose one control limit"}
            )

        if lcl is None and ucl is None:
            raise BusinessLogicException(
                error_code="error_missing_limits",
                field="limits",
                details={"message": "Must specify either LCL or UCL"}
            )

        if lcl is not None:
            control_limit = lcl
            limit_text = "L Limit"
        else:
            control_limit = ucl
            limit_text = "U Limit"

        # Validate data lengths
        if len(parts) != len(values) or len(values) != len(ok):
            raise BusinessLogicException(
                error_code="error_data_length_mismatch",
                field="data",
                details={"message": "Parts, values, and ok lists must have the same length"}
            )

        # Validate ok values against trials
        if any(x > num_trials for x in ok):
            raise BusinessLogicException(
                error_code="error_invalid_ok_values",
                field="ok",
                details={"message": "OK values cannot be greater than number of trials"}
            )

        if any(x < 0 for x in ok):
            raise BusinessLogicException(
                error_code="error_must_be_positive",
                field="ok_values",
                details={"message": "OK values cannot be negative"}
            )

        data = pd.DataFrame({
            "Part": parts,
            "Known-Value": values,
            "Percent Pass": np.array(ok) / num_trials  # Convert OK counts to proportions
        })

        # Check for missing values
        if data.isna().any().any():
            raise BusinessLogicException(
                error_code="error_missing_values",
                field="values",
                details={"message": "Dataset contains missing values"}
            )

        data = data.sort_values(["Known-Value"])

        # Define the sigmoid function
        def fsigmoid(x, a, b):
            return 1.0 / (1.0 + np.exp(-a * (x - b)))

        # Provide initial guesses for parameters
        initial_guess = [10, 0]  # Example initial guess: a=10, b=0

        try:
            # Fit the sigmoid function to the data using more robust methods
            popt, _ = curve_fit(
                fsigmoid,
                data["Known-Value"],
                data["Percent Pass"],
                p0=initial_guess,
                method='trf',  # Using Trust Region Reflective algorithm
                bounds=([-np.inf, -np.inf], [np.inf, np.inf]),  # No bounds, but can be adjusted if needed
                maxfev=10000  # Increase the max number of iterations
            )
        except RuntimeError as e:
            print(f"Curve fitting failed: {e}")
            return None
        except OptimizeWarning as w:
            print(f"Optimization warning: {w}")
            return None

        x = np.linspace(min(data["Known-Value"]), max(data["Known-Value"]), 100)
        y = fsigmoid(x, *popt)

        # Create a BytesIO object
        img_buffer = io.BytesIO()

        # Create the figure and axes with increased spacing
        fig, axs = plt.subplots(2, 1, figsize=(8.27, 11.69))  # A4 size in inches

        # Adjust layout: larger margins and more space between plots
        fig.subplots_adjust(left=0.15, right=0.85, top=0.85, bottom=0.1, hspace=0.4)
        fig.suptitle(title, fontsize=16, weight="bold", y=0.93)

        # First plot
        axs[0].scatter(data["Known-Value"], data["Percent Pass"], label="Data")
        axs[0].plot(x, y, color='red', label='Fitted Sigmoid')
        axs[0].set_title("Probability of Acceptance per Reference Value of Measured Part", pad=5)  # Reduced padding
        axs[0].annotate(f" {limit_text}", xy=(control_limit, 0), color="#A50021")
        axs[0].axvline(x=control_limit, c="#971817", linestyle="--")
        axs[0].set_xlabel("Reference Value of Measured Part")
        axs[0].set_ylabel("Probability of Acceptance")
        axs[0].grid(color="lightgrey")
        axs[0].legend()

        data["Sigmoid Probability Pass"] = fsigmoid(data["Known-Value"], *popt)

        def objective(x, a, b):
            return (0.5 - fsigmoid(x, a, b)) ** 2

        result = minimize_scalar(objective, args=tuple(popt))
        l_limit_estimate = result.x if result.success else None

        # Second plot
        probscale.probplot(data=data["Known-Value"], probax="y", plottype="prob", bestfit=True, ax=axs[1])
        axs[1].set_title("Attribute Gage Report (Analytic) for Acceptances")
        axs[1].set_xlabel("Reference Value of Measured Part")
        axs[1].set_ylabel("Percent of Acceptance")
        axs[1].grid(color="lightgrey")

        # Save the figure to the BytesIO object
        fig.savefig(img_buffer, format='pdf')
        img_buffer.seek(0)  # Rewind the buffer

        # Return the BytesIO object
        return img_buffer
