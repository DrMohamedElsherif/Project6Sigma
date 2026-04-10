# api/charts/evaluation/tests/test_utils.py
import math

SCENARIOS = ["normal", "large", "some_nans", "n_less_than_2", "all_nans"]

def apply_nan_scenario(values, categories=None, cat_name=None):
    """
    Convert some values to NaN for testing, ensuring each category has at least 2 non-NaN values
    """
    new_values = [v if i % 2 == 0 else float("nan") for i, v in enumerate(values)]

    if categories and cat_name:
        cat_vals = categories[cat_name]
        
        # ✅ SAFETY: align lengths
        min_len = min(len(cat_vals), len(new_values))
        cat_vals = cat_vals[:min_len]
        new_values = new_values[:min_len]
        
        unique_cats = set(cat_vals)
        for cat in unique_cats:
            indices = [i for i, c in enumerate(cat_vals) if c == cat]
            non_nans = [i for i in indices if not math.isnan(new_values[i])]
            missing = 2 - len(non_nans)
            if missing > 0:
                for i in indices:
                    if math.isnan(new_values[i]) and missing > 0:
                        new_values[i] = values[i]
                        missing -= 1
    return new_values


def apply_scenario_to_dataset(dataset, scenario):
    """
    Apply one of the standard scenarios to a dataset dict {'values': {...}, 'categories': {...} optional}
    """
    REPEAT = 20  # ✅ not 500
    new_dataset = {
        "dataset_name": dataset.get("dataset_name"),
        "values": {col: vals.copy() for col, vals in dataset["values"].items()}
    }
    if "categories" in dataset:
        new_dataset["categories"] = {k: v.copy() for k, v in dataset["categories"].items()}

    for col, vals in new_dataset["values"].items():
        if scenario == "some_nans":
            if "categories" in new_dataset:
                new_dataset["values"][col] = apply_nan_scenario(vals, new_dataset["categories"], "Group")
            else:
                new_dataset["values"][col] = apply_nan_scenario(vals)
        elif scenario == "n_less_than_2":
            new_dataset["values"][col] = vals[:1]
        elif scenario == "all_nans":
            new_dataset["values"][col] = [float("nan")] * len(vals)
        elif scenario == "large":
            for col in new_dataset["values"]:
                new_dataset["values"][col] = new_dataset["values"][col] * REPEAT

            if "categories" in new_dataset:
                for cat_col in new_dataset["categories"]:
                    new_dataset["categories"][cat_col] = new_dataset["categories"][cat_col] * REPEAT
    return new_dataset