# api/correlation/schemas.py

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal, Tuple
from enum import Enum

class CorrelationMethod(str, Enum):
    """Available correlation methods"""
    PEARSON = "pearson"
    SPEARMAN = "spearman" 
    KENDALL = "kendall"
    AUTO = "auto"

class CorrelationConfig(BaseModel):
    """Configuration for correlation analysis"""
    title: str = Field(..., description="Plot title")
    method: CorrelationMethod = Field(
        default=CorrelationMethod.AUTO,
        description="Correlation method to use (auto for automatic selection)"
    )
    show_regression: bool = Field(
        default=True,
        description="Show regression line in plot"
    )
    show_confidence_interval: bool = Field(
        default=True,
        description="Show 95% confidence interval"
    )
    alpha: float = Field(
        default=0.05,
        description="Significance level for hypothesis testing"
    )

class CorrelationData(BaseModel):
    """Input data for correlation analysis"""
    dataset_name: Optional[str] = "Dataset"
    x_values: List[float] = Field(..., min_length=2, description="X-axis values")
    y_values: List[float] = Field(..., min_length=2, description="Y-axis values")
    x_label: Optional[str] = "X Variable"
    y_label: Optional[str] = "Y Variable"
    
    @validator('y_values')
    def check_length_match(cls, v, values):
        """Validate that x and y have same length"""
        if 'x_values' in values and len(v) != len(values['x_values']):
            raise ValueError('x_values and y_values must have the same length')
        return v

class CorrelationRequest(BaseModel):
    """Complete request model"""
    project: str
    step: str
    config: CorrelationConfig
    data: CorrelationData

class CorrelationResult(BaseModel):
    """Results of correlation analysis"""
    method_used: CorrelationMethod
    coefficient: float
    p_value: float
    is_significant: bool
    strength_interpretation: str
    sample_size: int
    r_squared: Optional[float] = None
    assumptions_checked: dict