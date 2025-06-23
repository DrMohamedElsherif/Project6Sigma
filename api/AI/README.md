# AI Features Module

This module contains all AI-related features for the SixAPI project, following the same pattern as other chart modules.

## Structure

```
api/AI/
├── __init__.py
├── ai_router.py          # Router with endpoints (like hypothesistest_router.py)
├── analysis.py           # Business logic functions (like ttest.py)
└── README.md            # This file
```

## Pattern

This follows the same pattern as `api/charts/hypothesistest/`:
- **Router file** (`ai_router.py`): Contains FastAPI endpoints that import and call business logic
- **Logic file** (`analysis.py`): Contains the actual processing functions and utilities
- **Import pattern**: `from .analysis import process_ai_analysis` (similar to `from .ttest import Ttest`)

## Migration from charts/ai_analysis_router.py

The AI analysis functionality has been migrated from `api/charts/ai_analysis_router.py` to this module:

- **Endpoint URL changed**: `/api/v1/charts/ai-analysis/ai-analysis` → `/api/v1/ai/ai-analysis`
- **Business logic moved**: Analysis-specific code moved to `analysis.py`
- **Generic utilities kept**: Common AI utilities remain in `api/utils/ai_utils.py`

## Usage

The AI analysis endpoint is now available at:
```
POST /api/v1/ai/ai-analysis
```

With the same request format:
```json
{
    "project": "project_name",
    "step": "analysis",
    "chart_url": "URL_to_PDF_or_PNG", 
    "raw_data": "optional raw data string"
}
```

## Adding New AI Features

To add a new AI feature (e.g., summarization):

1. Add the business logic function to a new file (e.g., `summarization.py`)
2. Add an endpoint in `ai_router.py`:
```python
@router.post("/summarization")
async def ai_summarization_endpoint(request: dict):
    from .summarization import process_summarization
    # Process request and call business logic
    return result
```

This follows the exact same pattern as the existing chart modules.

## Dependencies

- Azure OpenAI (via `api.utils.ai_utils`)
- FastAPI
- PDF/Image processing utilities
