
import pytest
import math
import os

from api.charts.evaluation.boxplot import Boxplot
from api.charts.evaluation.tests.test_utils import SCENARIOS, apply_scenario_to_dataset
from api.schemas import BusinessLogicException
import matplotlib.pyplot as plt

# ----------------------------
# OUTPUT DIRECTORY FOR FIGURES
# ----------------------------
OUTPUT_DIR = "static/api_test/eval_charts"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ----------------------------
# BASE DATASETS PER VARIANT
# ----------------------------
BASE_DATASETS = {
    "single": [
        {
            "dataset_name": "Machine A",
            "values": {
                "Measurements": [
                    23.5, 25.2, 24.7, 24.1, 25.4, 23.9, 24.8, 25.1, 24.3, 24.9,
                    23.8, 24.6, 25.3, 24.2, 24.5, 25.0, 24.4, 23.7, 24.0, 25.5,
                    24.8, 23.6, 25.2, 24.3, 24.7, 25.1, 24.5, 23.9, 24.2, 25.0
                ]
            }
        },
        {
            "dataset_name": "Machine B",
            "values": {
                "inside_temp": [
                    21.5, 22.2, 21.7, 22.1, 21.4, 21.9, 22.3, 21.8, 22.0, 21.6,
                    21.7, 22.1, 21.5, 21.9, 22.2, 21.8, 22.0, 21.6, 21.9, 22.3
                ],
                "outside_temp": [
                    18.2, 17.8, 18.5, 17.9, 18.3, 18.0, 17.7, 18.4, 18.1, 17.6,
                    18.3, 17.9, 18.2, 18.0, 17.8, 18.5, 17.7, 18.1, 18.4, 17.6
                ],
                "room_temp": [
                    20.1, 19.8, 20.3, 19.9, 20.2, 20.0, 19.7, 20.4, 20.1, 19.6,
                    20.2, 19.9, 20.1, 20.0, 19.8, 20.3, 19.7, 20.2, 20.4, 19.6
                ]
            }
        },
    ],
    "faceted_by_group": [
        {
            "dataset_name": "Machine E",
            "values": {
                "spring": [15.5, 16.2, 15.7, 16.1, 15.4, 15.9, 16.3, 15.8, 16.0, 15.6,
                           15.7, 16.1, 15.5, 15.9, 16.2, 15.8, 16.0, 15.6, 15.9, 16.3],
                "summer": [25.2, 24.8, 25.5, 24.9, 25.3, 25.0, 24.7, 25.4, 25.1, 24.6,
                           25.3, 24.9, 25.2, 25.0, 24.8, 25.5, 24.7, 25.1, 25.4, 24.6],
                "autumn": [18.1, 17.8, 18.3, 17.9, 18.2, 18.0, 17.7, 18.4, 18.1, 17.6,
                           18.2, 17.9, 18.1, 18.0, 17.8, 18.3, 17.7, 18.2, 18.4, 17.6],
                "winter": [5.1, 4.8, 5.3, 4.9, 5.2, 5.0, 4.7, 5.4, 5.1, 4.6,
                           5.2, 5.0, 4.8, 5.3, 4.7, 5.2, 5.4, 4.6, 5.1, 4.9]
            },
            "categories": {"Group": ["X"]*20}  # ensure faceted_by_group has categories
        }
    ],
    "multipanel_columns": [
        {
            "dataset_name": "Machine F",
            "values": {
                "length": [100.2, 99.8, 100.5, 99.9, 100.3, 100.0, 99.7, 100.4, 100.1, 99.6,
                           100.2, 99.9, 100.1, 100.0, 99.8, 100.3, 99.7, 100.2, 100.4, 99.6],
                "width": [50.1, 49.8, 50.3, 49.9, 50.2, 50.0, 49.7, 50.4, 50.1, 49.6,
                          50.2, 49.9, 50.1, 50.0, 49.8, 50.3, 49.7, 50.2, 50.4, 49.6],
                "height": [25.5, 24.8, 25.3, 24.9, 25.2, 25.0, 24.7, 25.4, 25.1, 24.6,
                           25.2, 24.9, 25.1, 25.0, 24.8, 25.3, 24.7, 25.2, 25.4, 24.6],
                "weight": [755.2, 744.8, 753.5, 748.9, 751.3, 750.0, 747.7, 754.4, 751.1, 746.6,
                           752.3, 749.9, 751.2, 750.0, 748.8, 753.5, 747.7, 751.1, 754.4, 746.6]
            }
        }
    ]
}

# ----------------------------
# HELPERS
# ----------------------------

def build_boxplot_dataset(variant, scenario):
    """Apply scenario transformations from shared utils"""
    for ds in BASE_DATASETS[variant]:
        dataset = {
            "dataset_name": ds["dataset_name"],
            "values": {k: v.copy() for k, v in ds["values"].items()}
        }
        if "categories" in ds:
            dataset["categories"] = {k: v.copy() for k, v in ds["categories"].items()}

        dataset = apply_scenario_to_dataset(dataset, scenario)
        yield dataset

# ----------------------------
# INVALID DATASETS TEST
# ----------------------------

@pytest.mark.parametrize("variant", BASE_DATASETS.keys())
@pytest.mark.parametrize("scenario", ["n_less_than_2", "all_nans"])
def test_invalid_datasets_raise_error(variant, scenario):
    for dataset in build_boxplot_dataset(variant, scenario):
        data = {
            "project": "api_test",
            "step": "eval_charts",
            "config": {"title": f"{variant}_{scenario}", "variant": variant},
            "data": dataset
        }
        with pytest.raises(BusinessLogicException):
            Boxplot(data).process()

# ----------------------------
# VALID DATASETS TEST
# ----------------------------

@pytest.mark.parametrize("variant", BASE_DATASETS.keys())
@pytest.mark.parametrize("scenario", ["normal", "large", "some_nans"])
def test_valid_datasets_compute_stats(variant, scenario):
    for dataset in build_boxplot_dataset(variant, scenario):
        # ensure faceted_by_group always has categories
        if variant == "faceted_by_group" and "categories" not in dataset:
            dataset["categories"] = {"Group": ["X"] * len(next(iter(dataset["values"].values())))}

        data = {
            "project": "api_test",
            "step": "eval_charts",
            "config": {"title": f"{variant}_{scenario}", "variant": variant},
            "data": dataset
        }

        boxplot_instance = Boxplot(data)
        fig = boxplot_instance.process()  # generate figure
        stats = boxplot_instance.statistics  # table/statistics

        # ----------------------------
        # SAVE FIGURE
        # ----------------------------
        fig_file = os.path.join(
            OUTPUT_DIR,
            f"{dataset['dataset_name']}_{variant}_{scenario}.png"
        )
        fig.savefig(fig_file, dpi=150)
        # plt.close(fig)  # optionally close figure to free memory

        assert fig is not None
        assert stats is not None

        for col, vals in dataset["values"].items():
            assert col in stats
            valid_vals = [v for v in vals if v is not None and not math.isnan(v)]
            assert stats[col]["n"] == len(valid_vals)
            if valid_vals:
                assert stats[col]["average"] == pytest.approx(sum(valid_vals)/len(valid_vals))
                sorted_vals = sorted(valid_vals)
                mid = len(sorted_vals)//2
                median = (sorted_vals[mid-1] + sorted_vals[mid])/2 if len(sorted_vals) % 2 == 0 else sorted_vals[mid]
                assert stats[col]["median"] == pytest.approx(median)
                assert stats[col]["min"] == min(valid_vals)
                assert stats[col]["max"] == max(valid_vals)

# ----------------------------
# VARIANT-SPECIFIC TESTS
# ----------------------------

def test_faceted_by_group_requires_categories():
    dataset = {
        "dataset_name": "NoCats",
        "values": {"A": [1, 2, 3]}
    }
    data = {
        "project": "api_test",
        "step": "eval_charts",
        "config": {"title": "Missing Categories", "variant": "faceted_by_group"},
        "data": dataset
    }
    with pytest.raises(ValueError):
        Boxplot(data).process()

def test_unknown_variant_raises_error():
    data = {
        "project": "api_test",
        "step": "eval_charts",
        "config": {"title": "Invalid Variant", "variant": "does_not_exist"},
        "data": {"dataset_name": "Dataset", "values": {"A": [1, 2, 3]}}
    }
    with pytest.raises(BusinessLogicException) as exc_info:
        Boxplot(data).process()
    exc = exc_info.value
    assert exc.error_code == "error_validation"
    assert "does_not_exist" in exc.details["message"]
    
    

###################### BELOW OS THE OLD UNREFACTORED CODE, IGNORE ######################
# import pytest
# import math
# import os  
# from api.charts.evaluation.boxplot import Boxplot
# from api.schemas import BusinessLogicException

# # ----------------------------
# # OUTPUT DIRECTORY FOR FIGURES
# # ----------------------------
# OUTPUT_DIR = "static/api_test/eval_charts"  
# os.makedirs(OUTPUT_DIR, exist_ok=True)       

# # ----------------------------
# # HARD-CODED DATASETS PER VARIANT
# # ----------------------------

# SINGLE_DATASETS = [
#     {
#         "dataset_name": "Machine A",
#         "values": {
#             "Measurements": [
#                 23.5, 25.2, 24.7, 24.1, 25.4, 23.9, 24.8, 25.1, 24.3, 24.9,
#                 23.8, 24.6, 25.3, 24.2, 24.5, 25.0, 24.4, 23.7, 24.0, 25.5,
#                 24.8, 23.6, 25.2, 24.3, 24.7, 25.1, 24.5, 23.9, 24.2, 25.0
#             ]
#         }
#     },
#     {
#         "dataset_name": "Machine B",
#         "values": {
#             "inside_temp": [
#                 21.5, 22.2, 21.7, 22.1, 21.4, 21.9, 22.3, 21.8, 22.0, 21.6,
#                 21.7, 22.1, 21.5, 21.9, 22.2, 21.8, 22.0, 21.6, 21.9, 22.3
#             ],
#             "outside_temp": [
#                 18.2, 17.8, 18.5, 17.9, 18.3, 18.0, 17.7, 18.4, 18.1, 17.6,
#                 18.3, 17.9, 18.2, 18.0, 17.8, 18.5, 17.7, 18.1, 18.4, 17.6
#             ],
#             "room_temp": [
#                 20.1, 19.8, 20.3, 19.9, 20.2, 20.0, 19.7, 20.4, 20.1, 19.6,
#                 20.2, 19.9, 20.1, 20.0, 19.8, 20.3, 19.7, 20.2, 20.4, 19.6
#             ]
#         }
#     },
#     {
#         "dataset_name": "Machine C",
#         "values": {
#             "morning": [
#                 18.5, 19.2, 18.7, 19.1, 18.4, 18.9, 19.3, 18.8, 19.0, 18.6,
#                 18.7, 19.1, 18.5, 18.9, 19.2, 18.8, 19.0, 18.6, 18.9, 19.3
#             ],
#             "afternoon": [
#                 23.2, 22.8, 23.5, 22.9, 23.3, 23.0, 22.7, 23.4, 23.1, 22.6,
#                 23.3, 22.9, 23.2, 23.0, 22.8, 23.5, 22.7, 23.1, 23.4, 22.6
#             ],
#             "evening": [
#                 20.1, 19.8, 20.3, 19.9, 20.2, 20.0, 19.7, 20.4, 20.1, 19.6,
#                 20.2, 19.9, 20.1, 20.0, 19.8, 20.3, 19.7, 20.2, 20.4, 19.6
#             ]
#         }
#     },
#     {
#         "dataset_name": "Machine D",
#         "values": {
#             "spring": [
#                 15.5, 16.2, 15.7, 16.1, 15.4, 15.9, 16.3, 15.8, 16.0, 15.6,
#                 15.7, 16.1, 15.5, 15.9, 16.2, 15.8, 16.0, 15.6, 15.9, 16.3
#             ],
#             "summer": [
#                 25.2, 24.8, 25.5, 24.9, 25.3, 25.0, 24.7, 25.4, 25.1, 24.6,
#                 25.3, 24.9, 25.2, 25.0, 24.8, 25.5, 24.7, 25.1, 25.4, 24.6
#             ],
#             "autumn": [
#                 18.1, 17.8, 18.3, 17.9, 18.2, 18.0, 17.7, 18.4, 18.1, 17.6,
#                 18.2, 17.9, 18.1, 18.0, 17.8, 18.3, 17.7, 18.2, 18.4, 17.6
#             ],
#             "winter": [
#                 5.1, 4.8, 5.3, 4.9, 5.2, 5.0, 4.7, 5.4, 5.1, 4.6,
#                 5.2, 4.9, 5.1, 5.0, 4.8, 5.3, 4.7, 5.2, 5.4, 4.6
#             ]
#         }
#     }
# ]

# BY_CATEGORY_DATASET = {
#     "dataset_name": "Machine E",
#     "values": {
#         "spring": [15.5, 16.2, 15.7, 16.1, 15.4, 15.9, 16.3, 15.8, 16.0, 15.6,
#                    15.7, 16.1, 15.5, 15.9, 16.2, 15.8, 16.0, 15.6, 15.9, 16.3],
#         "summer": [25.2, 24.8, 25.5, 24.9, 25.3, 25.0, 24.7, 25.4, 25.1, 24.6,
#                    25.3, 24.9, 25.2, 25.0, 24.8, 25.5, 24.7, 25.1, 25.4, 24.6],
#         "autumn": [18.1, 17.8, 18.3, 17.9, 18.2, 18.0, 17.7, 18.4, 18.1, 17.6,
#                    18.2, 17.9, 18.1, 18.0, 17.8, 18.3, 17.7, 18.2, 18.4, 17.6],
#         "winter": [5.1, 4.8, 5.3, 4.9, 5.2, 5.0, 4.7, 5.4, 5.1, 4.6,
#                    5.2, 5.0, 4.8, 5.3, 4.7, 5.2, 5.4, 4.6, 5.1, 4.9]
#     },
# }

# MULTIPANEL_COLUMNS_DATASET = {
#     "dataset_name": "Machine F",
#     "values": {
#         "length": [
#             100.2, 99.8, 100.5, 99.9, 100.3, 100.0, 99.7, 100.4, 100.1, 99.6,
#             100.2, 99.9, 100.1, 100.0, 99.8, 100.3, 99.7, 100.2, 100.4, 99.6
#         ],
#         "width": [
#             50.1, 49.8, 50.3, 49.9, 50.2, 50.0, 49.7, 50.4, 50.1, 49.6,
#             50.2, 49.9, 50.1, 50.0, 49.8, 50.3, 49.7, 50.2, 50.4, 49.6
#         ],
#         "height": [
#             25.5, 24.8, 25.3, 24.9, 25.2, 25.0, 24.7, 25.4, 25.1, 24.6,
#             25.2, 24.9, 25.1, 25.0, 24.8, 25.3, 24.7, 25.2, 25.4, 24.6
#         ],
#         "weight": [
#             755.2, 744.8, 753.5, 748.9, 751.3, 750.0, 747.7, 754.4, 751.1, 746.6,
#             752.3, 749.9, 751.2, 750.0, 748.8, 753.5, 747.7, 751.1, 754.4, 746.6
#         ]
#     }
# }

# VARIANT_MAP = {
#     "single": SINGLE_DATASETS,
#     "faceted_by_group": [BY_CATEGORY_DATASET],
#     "multipanel_columns": [MULTIPANEL_COLUMNS_DATASET]
# }


# SCENARIOS = ["normal", "large", "some_nans", "n_less_than_2", "all_nans"]

# # ----------------------------
# # HELPER FUNCTIONS
# # ----------------------------

# def _nanify(values, categories=None, cat_name=None):
#     """
#     Convert some values to NaN for testing, ensuring each category has at least 2 non-NaN values
#     """
#     new_values = [v if i % 2 == 0 else float("nan") for i, v in enumerate(values)]
    
#     if categories and cat_name:
#         cat_vals = categories[cat_name]
#         unique_cats = set(cat_vals)
#         for cat in unique_cats:
#             indices = [i for i, c in enumerate(cat_vals) if c == cat]
#             non_nans = [i for i in indices if not math.isnan(new_values[i])]
#             missing = 2 - len(non_nans)
#             if missing > 0:
#                 # restore first `missing` NaNs in this category
#                 for i in indices:
#                     if math.isnan(new_values[i]) and missing > 0:
#                         new_values[i] = values[i]
#                         missing -= 1
#     return new_values


# def build_scenario_dataset(variant, scenario):
#     """Apply scenario transformations to hard-coded dataset"""
#     for ds in VARIANT_MAP[variant]:
#         dataset = {
#             "dataset_name": ds["dataset_name"],
#             "values": {k: v.copy() for k, v in ds["values"].items()}
#         }
#         if "categories" in ds:
#             dataset["categories"] = {k: v.copy() for k, v in ds["categories"].items()}

#         if scenario == "some_nans":
#             for col in dataset["values"]:
#                 if "categories" in dataset:
#                     dataset["values"][col] = _nanify(
#                         dataset["values"][col], dataset["categories"], "Group"
#                     )
#                 else:
#                     dataset["values"][col] = _nanify(dataset["values"][col])
#         elif scenario == "n_less_than_2":
#             for col in dataset["values"]:
#                 dataset["values"][col] = dataset["values"][col][:1]
#         elif scenario == "all_nans":
#             for col in dataset["values"]:
#                 dataset["values"][col] = [float("nan")] * len(dataset["values"][col])
#         elif scenario == "large":
#             n_repeat = 500
#             for col in dataset["values"]:
#                 dataset["values"][col] = dataset["values"][col] * n_repeat
#             if "categories" in dataset:
#                 for cat_col in dataset["categories"]:
#                     dataset["categories"][cat_col] = dataset["categories"][cat_col] * n_repeat

#         yield dataset

# # ----------------------------
# # INVALID DATASETS TEST
# # ----------------------------

# @pytest.mark.parametrize("variant", VARIANT_MAP.keys())
# @pytest.mark.parametrize("scenario", ["n_less_than_2", "all_nans"])
# def test_invalid_datasets_raise_error(variant, scenario):
#     for dataset in build_scenario_dataset(variant, scenario):
#         data = {
#             "project": "api_test",
#             "step": "eval_charts",
#             "config": {"title": f"{variant}_{scenario}", "variant": variant},
#             "data": dataset
#         }
#         with pytest.raises(BusinessLogicException):
#             Boxplot(data).process()

# # ----------------------------
# # VALID DATASETS TEST
# # ----------------------------

# @pytest.mark.parametrize("variant", VARIANT_MAP.keys())
# @pytest.mark.parametrize("scenario", ["normal", "large", "some_nans"])
# def test_valid_datasets_compute_stats(variant, scenario):
#     for dataset in build_scenario_dataset(variant, scenario):
#         # ensure by_category always has categories
#         if variant == "faceted_by_group" and "categories" not in dataset:
#             dataset["categories"] = {"Group": ["X"] * len(next(iter(dataset["values"].values())))}


#         data = {
#             "project": "api_test",
#             "step": "eval_charts",
#             "config": {"title": f"{variant}_{scenario}", "variant": variant},
#             "data": dataset
#         }

#         boxplot_instance = Boxplot(data)
#         fig = boxplot_instance.process()  # generate figure
#         stats = boxplot_instance.statistics  # table/statistics

#         # ----------------------------
#         # SAVE FIGURE ONLY
#         # ----------------------------
#         if fig is not None:  # MODIFIED
#             fig_file = os.path.join(
#                 OUTPUT_DIR,
#                 f"{dataset['dataset_name']}_{variant}_{scenario}.png"
#             )
#             fig.savefig(fig_file, dpi=150)  # MODIFIED

#         assert fig is not None
#         assert stats is not None

#         for col, vals in dataset["values"].items():
#             assert col in stats
#             valid_vals = [v for v in vals if v is not None and not math.isnan(v)]
#             assert stats[col]["n"] == len(valid_vals)
#             if valid_vals:
#                 assert stats[col]["average"] == pytest.approx(sum(valid_vals)/len(valid_vals))
#                 sorted_vals = sorted(valid_vals)
#                 mid = len(sorted_vals)//2
#                 median = (sorted_vals[mid-1] + sorted_vals[mid])/2 if len(sorted_vals) % 2 == 0 else sorted_vals[mid]
#                 assert stats[col]["median"] == pytest.approx(median)
#                 assert stats[col]["min"] == min(valid_vals)
#                 assert stats[col]["max"] == max(valid_vals)



# # ----------------------------
# # VARIANT-SPECIFIC TESTS
# # ----------------------------

# def test_faceted_by_group_requires_categories():
#     dataset = {
#         "dataset_name": "NoCats",
#         "values": {"A": [1, 2, 3]}
#     }
#     data = {
#         "project": "api_test",
#         "step": "eval_charts",
#         "config": {"title": "Missing Categories", "variant": "faceted_by_group"},
#         "data": dataset
#     }
#     with pytest.raises(ValueError):
#         Boxplot(data).process()

# def test_unknown_variant_raises_error():
#     data = {
#         "project": "api_test",
#         "step": "eval_charts",
#         "config": {"title": "Invalid Variant", "variant": "does_not_exist"},
#         "data": {"dataset_name": "Dataset", "values": {"A": [1, 2, 3]}}
#     }
#     with pytest.raises(BusinessLogicException) as exc_info:
#         Boxplot(data).process()
#     exc = exc_info.value
#     assert exc.error_code == "error_validation"
#     assert "does_not_exist" in exc.details["message"]


