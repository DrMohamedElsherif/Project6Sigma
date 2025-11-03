from .prompts.define_prompts import DEFINE_PROMPTS
from .prompts.measure_prompts import MEASURE_PROMPTS
from .prompts.analysis_prompts import ANALYSIS_PROMPTS
from .prompts.improve_prompts import IMPROVE_PROMPTS
from .prompts.control_prompts import CONTROL_PROMPTS

def get_prompt(sheet_name: str, data: str) -> str:
    """Route to appropriate prompt based on sheet category."""
    
    # Route to category
    if sheet_name.startswith("D-") or sheet_name == "Info-Sammlung":
        prompts = DEFINE_PROMPTS
    elif sheet_name.startswith("M-"):
        prompts = MEASURE_PROMPTS
    elif sheet_name.startswith("A-"):
        prompts = ANALYSIS_PROMPTS
    elif sheet_name.startswith("I-"):
        prompts = IMPROVE_PROMPTS
    elif sheet_name.startswith("C-"):
        prompts = CONTROL_PROMPTS
    else:
        raise ValueError(f"Unknown sheet category for: {sheet_name}")
    
    if sheet_name not in prompts:
        raise ValueError(f"No prompt defined for sheet: {sheet_name}")
    
    prompt_template = prompts[sheet_name]
    return prompt_template.replace("{data}", data)

