import pytest
import math
import os

from api.charts.evaluation.histogram import Histogram
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
        Histogram(data).process()

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

    hist = Histogram(data)
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
            "ci_95_lower", "ci_95_upper", "ci_95",
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

    hist = Histogram(data)
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
        Histogram(data).process()

    exc = exc_info.value
    assert exc.error_code == "error_validation"
    assert "invalid" in exc.details["message"].lower()



####################### BELOW OS THE OLD UNREFACTORED CODE, IGNORE ######################

# import pytest
# import math
# import os

# from api.charts.evaluation.histogram import Histogram
# from api.charts.evaluation.tests.test_utils import SCENARIOS, apply_scenario_to_dataset
# from api.schemas import BusinessLogicException

# # ----------------------------
# # OUTPUT DIRECTORY
# # ----------------------------
# OUTPUT_DIR = "static/api_test/eval_charts"
# os.makedirs(OUTPUT_DIR, exist_ok=True)

# # ----------------------------
# # BASE DATASET
# # ----------------------------
# BASE_VALUES = {
#     "A": [23.5, 25.2, 24.7, 24.1, 25.4, 23.9, 24.8, 25.1, 24.3, 24.9],
#     "B": [21.1, 20.8, 21.3, 20.9, 21.2, 21.0, 20.7, 21.4, 21.1, 20.6],
#     "C": [18.5, 19.2, 18.7, 19.1, 18.4, 18.9, 19.3, 18.8, 19.0, 18.6],
#     "D": [15.5, 16.2, 15.7, 16.1, 15.4, 15.9, 16.3, 15.8, 16.0, 15.6]
# }

# MODES = ["single", "stacked", "subplots"]
# SCENARIOS = ["normal", "large", "some_nans", "n_less_than_2", "all_nans"]

# # ----------------------------
# # HELPERS
# # ----------------------------

# # def apply_scenario(values, scenario):
# #     if scenario == "normal":
# #         return values

# #     if scenario == "some_nans":
# #         vals = [v if i % 2 == 0 else float("nan") for i, v in enumerate(values)]
# #         # ensure at least 2 valid
# #         if sum(not math.isnan(v) for v in vals) < 2:
# #             return values[:2]
# #         return vals

# #     if scenario == "n_less_than_2":
# #         return values[:1]

# #     if scenario == "all_nans":
# #         return [float("nan")] * len(values)

# #     if scenario == "large":
# #         return values * 500

# #     return values

# def apply_scenario(values, scenario):
#     """
#     Modify a list of values according to the scenario:
#     - some_nans: every other value becomes NaN, but ensure at least 2 valid
#     - n_less_than_2: only keep 1 value
#     - all_nans: all values become NaN
#     - large: repeat the values 500 times
#     """
#     if scenario == "normal":
#         return values

#     if scenario == "some_nans":
#         vals = [v if i % 2 == 0 else float("nan") for i, v in enumerate(values)]
#         # ensure at least 2 valid
#         valid_count = sum(not math.isnan(v) for v in vals)
#         if valid_count < 2:
#             # restore first 2 values to be valid
#             for i, v in enumerate(vals):
#                 if math.isnan(v) and valid_count < 2:
#                     vals[i] = values[i]
#                     valid_count += 1
#         return vals

#     if scenario == "n_less_than_2":
#         return values[:1]

#     if scenario == "all_nans":
#         return [float("nan")] * len(values)

#     if scenario == "large":
#         return values * 500

#     return values


# def build_dataset(mode, scenario):
#     cols = ["A"] if mode == "single" else ["A", "B"] if mode == "stacked" else ["A", "B", "C", "D"]

#     return {
#         "values": {
#             col: apply_scenario(BASE_VALUES[col], scenario)
#             for col in cols
#         }
#     }

# # ----------------------------
# # INVALID DATA TESTS
# # ----------------------------

# @pytest.mark.parametrize("mode", MODES)
# @pytest.mark.parametrize("scenario", ["n_less_than_2", "all_nans"])
# def test_invalid_datasets_raise_error(mode, scenario):
#     data = {
#         "project": "api_test",
#         "step": "eval_charts",
#         "config": {"title": f"{mode}_{scenario}", "mode": mode},
#         "data": build_dataset(mode, scenario)
#     }

#     with pytest.raises(BusinessLogicException):
#         Histogram(data).process()

# # ----------------------------
# # VALID DATA TESTS
# # ----------------------------

# @pytest.mark.parametrize("mode", MODES)
# @pytest.mark.parametrize("scenario", ["normal", "large", "some_nans"])
# def test_valid_datasets(mode, scenario):

#     data = {
#         "project": "api_test",
#         "step": "eval_charts",
#         "config": {
#             "title": f"{mode}_{scenario}",
#             "mode": mode,
#             "bins": 10,
#             "show_stats": True
#         },
#         "data": build_dataset(mode, scenario)
#     }

#     hist = Histogram(data)
#     fig = hist.process()
#     stats = hist.statistics

#     # ----------------------------
#     # FIGURE VALIDATION
#     # ----------------------------
#     assert fig is not None

#     fig_path = os.path.join(OUTPUT_DIR, f"{mode}_{scenario}.png")
#     fig.savefig(fig_path, dpi=120)

#     # ----------------------------
#     # STATISTICS VALIDATION
#     # ----------------------------
#     assert stats is not None
#     assert isinstance(stats, dict)

#     for col, values in data["data"]["values"].items():
#         assert col in stats

#         clean = [v for v in values if not (v is None or math.isnan(v))]

#         stat = stats[col]

#         # --- REQUIRED FIELDS ---
#         required_keys = [
#             "column_name", "n", "average", "median",
#             "min", "max", "range", "standard_deviation",
#             "ci_95_lower", "ci_95_upper", "ci_95",
#             "q1", "q3", "iqr"
#         ]

#         for key in required_keys:
#             assert key in stat

#         # --- BASIC CHECKS ---
#         assert stat["n"] == len(clean)

#         if len(clean) > 1:
#             assert stat["min"] <= stat["q1"] <= stat["median"] <= stat["q3"] <= stat["max"]
#             assert stat["iqr"] == pytest.approx(stat["q3"] - stat["q1"])
#             assert stat["ci_95_lower"] <= stat["average"] <= stat["ci_95_upper"]

# # ----------------------------
# # MODE-SPECIFIC TESTS
# # ----------------------------

# def test_single_mode_has_one_dataset():
#     data = {
#         "project": "api_test",
#         "step": "eval_charts",
#         "config": {"title": "single_test", "mode": "single"},
#         "data": build_dataset("single", "normal")
#     }

#     hist = Histogram(data)
#     hist.process()

#     assert len(hist.statistics) == 1


# def test_stacked_mode_multiple_datasets():
#     data = {
#         "project": "api_test",
#         "step": "eval_charts",
#         "config": {"title": "stacked_test", "mode": "stacked"},
#         "data": build_dataset("stacked", "normal")
#     }

#     hist = Histogram(data)
#     hist.process()

#     assert len(hist.statistics) > 1


# def test_subplots_mode_multiple_datasets():
#     data = {
#         "project": "api_test",
#         "step": "eval_charts",
#         "config": {"title": "subplots_test", "mode": "subplots"},
#         "data": build_dataset("subplots", "normal")
#     }

#     hist = Histogram(data)
#     hist.process()

#     assert len(hist.statistics) > 1

# # ----------------------------
# # INVALID MODE TEST
# # ----------------------------

# def test_invalid_mode():
#     data = {
#         "project": "api_test",
#         "step": "eval_charts",
#         "config": {"title": "bad_mode", "mode": "invalid"},
#         "data": build_dataset("single", "normal")
#     }

#     # Histogram now raises BusinessLogicException on invalid mode
#     with pytest.raises(BusinessLogicException) as exc_info:
#         Histogram(data).process()

#     exc = exc_info.value
#     assert exc.error_code == "error_validation"

