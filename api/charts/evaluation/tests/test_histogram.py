import pytest
import math
import os

from api.charts.evaluation.histogram_v2 import HistogramV2
from api.charts.evaluation.tests.test_utils import SCENARIOS, apply_scenario_to_dataset
from api.schemas import BusinessLogicException

# ----------------------------
# OUTPUT DIRECTORY
# ----------------------------
OUTPUT_DIR = "static/api_test/eval_charts"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ----------------------------
# BASE DATASET FOR HISTOGRAM
# ----------------------------
BASE_VALUES = {
    #"A": [23.5, 25.2, 24.7, 24.1, 25.4, 23.9, 24.8, 25.1, 24.3, 24.9],
    #"B": [21.1, 20.8, 21.3, 20.9, 21.2, 21.0, 20.7, 21.4, 21.1, 20.6],
    "A": [23.9, 24.1, 24.0, 24.3, 23.8, 24.2, 24.4, 23.7, 24.5, 24.0],
    "B": [23.8, 24.0, 24.2, 23.9, 24.1, 24.3, 23.7, 24.4, 23.6, 24.0],
    "C": [18.5, 19.2, 18.7, 19.1, 18.4, 18.9, 19.3, 18.8, 19.0, 18.6],
    "D": [15.5, 16.2, 15.7, 16.1, 15.4, 15.9, 16.3, 15.8, 16.0, 15.6]
}

MODES = ["single", "stacked", "subplots"]

# ----------------------------
# HELPERS
# ----------------------------

def build_histogram_dataset(mode, scenario):
    """
    Build Histogram datasets per mode and apply shared scenario logic
    """
    cols = {
        "single": ["A"],
        "stacked": ["A", "B"],
        "subplots": ["A", "B", "C", "D"]
    }[mode]

    dataset = {"values": {col: BASE_VALUES[col].copy() for col in cols}}
    return apply_scenario_to_dataset(dataset, scenario)

# ----------------------------
# INVALID DATA TESTS
# ----------------------------

@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("scenario", ["n_less_than_2", "all_nans"])
def test_invalid_datasets_raise_error(mode, scenario):
    data = {
        "project": "api_test",
        "step": "eval_charts",
        "config": {"title": f"{mode}_{scenario}", "mode": mode},
        "data": build_histogram_dataset(mode, scenario)
    }

    with pytest.raises(BusinessLogicException):
        HistogramV2(data).process()

# ----------------------------
# VALID DATA TESTS
# ----------------------------

@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("scenario", ["normal", "large", "some_nans"])
def test_valid_datasets(mode, scenario):

    data = {
        "project": "api_test",
        "step": "eval_charts",
        "config": {
            "title": f"{mode}_{scenario}",
            "mode": mode,
            "bins": 10,
            "show_stats": True
        },
        "data": build_histogram_dataset(mode, scenario)
    }

    hist = HistogramV2(data)
    fig = hist.process()
    stats = hist.statistics

    # ----------------------------
    # FIGURE VALIDATION
    # ----------------------------
    assert fig is not None

    fig_path = os.path.join(OUTPUT_DIR, f"{mode}_{scenario}.png")
    fig.savefig(fig_path, dpi=120)

    # ----------------------------
    # STATISTICS VALIDATION
    # ----------------------------
    assert stats is not None
    assert isinstance(stats, dict)

    for col, values in data["data"]["values"].items():
        assert col in stats
        clean = [v for v in values if v is not None and not math.isnan(v)]
        stat = stats[col]

        # --- REQUIRED FIELDS ---
        required_keys = [
            "column_name", "n", "average", "median",
            "min", "max", "range", "standard_deviation",
            "ci_95_lower", "ci_95_upper", 
            "q1", "q3", "iqr"
        ]
        for key in required_keys:
            assert key in stat

        # --- BASIC CHECKS ---
        assert stat["n"] == len(clean)
        if len(clean) > 1:
            assert stat["min"] <= stat["q1"] <= stat["median"] <= stat["q3"] <= stat["max"]
            assert stat["iqr"] == pytest.approx(stat["q3"] - stat["q1"])
            assert stat["ci_95_lower"] <= stat["average"] <= stat["ci_95_upper"]

# ----------------------------
# MODE-SPECIFIC TESTS
# ----------------------------

@pytest.mark.parametrize("mode", ["single", "stacked", "subplots"])
def test_mode_statistics_count(mode):
    data = {
        "project": "api_test",
        "step": "eval_charts",
        "config": {"title": f"{mode}_test", "mode": mode},
        "data": build_histogram_dataset(mode, "normal")
    }

    hist = HistogramV2(data)
    hist.process()

    expected_count = {"single": 1, "stacked": 2, "subplots": 4}[mode]
    assert len(hist.statistics) == expected_count

# ----------------------------
# INVALID MODE TEST
# ----------------------------

def test_invalid_mode():
    data = {
        "project": "api_test",
        "step": "eval_charts",
        "config": {"title": "bad_mode", "mode": "invalid"},
        "data": build_histogram_dataset("single", "normal")
    }

    # Histogram now raises BusinessLogicException on invalid mode
    with pytest.raises(BusinessLogicException) as exc_info:
        HistogramV2(data).process()

    exc = exc_info.value
    assert exc.error_code == "error_validation"
    assert "invalid" in exc.details["message"].lower()



