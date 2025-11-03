from .validators.define_validators import DEFINE_VALIDATORS
from .validators.measure_validators import MEASURE_VALIDATORS
from .validators.analysis_validators import ANALYSIS_VALIDATORS
from .validators.improve_validators import IMPROVE_VALIDATORS
from .validators.control_validators import CONTROL_VALIDATORS

def validate_json(sheet_name: str, data: dict) -> bool:
    """Route to appropriate validator based on sheet category."""
    
    # Route to category
    if sheet_name.startswith("D-") or sheet_name == "Info-Sammlung":
        validators = DEFINE_VALIDATORS
    elif sheet_name.startswith("M-"):
        validators = MEASURE_VALIDATORS
    elif sheet_name.startswith("A-"):
        validators = ANALYSIS_VALIDATORS
    elif sheet_name.startswith("I-"):
        validators = IMPROVE_VALIDATORS
    elif sheet_name.startswith("C-"):
        validators = CONTROL_VALIDATORS
    else:
        raise ValueError(f"Unknown sheet category for: {sheet_name}")
    
    if sheet_name not in validators:
        raise ValueError(f"No validator defined for sheet: {sheet_name}")
    
    return validators[sheet_name](data)
