# Postman Testing Guide — Boxplot Evaluation

This guide explains how to use the Postman pre-request and test scripts for validating the Boxplot API (`/boxplot` endpoint).

---

## 1. Purpose of the Tests

The Postman tests are designed to validate:

- ✅ **API Response**  
  - Correct HTTP status code (200 for success, 400/422 for invalid input)  
  - Response time under 1000ms  

- ✅ **Success Response Structure**  
  - `success` field is `true`  
  - `chart_id` is a non-empty string  
  - `url` is a valid image URL (`.png`, `.jpg`, `.jpeg`)  
  - `statistics` object is present and properly formatted  

- ✅ **Statistics Validation**  
  - Required fields exist (`column_name`, `n`, `average`, `median`, `min`, `max`, `range`, `standard_deviation`, `ci_95_lower`, `ci_95_upper`, `ci_95`, `q1`, `q3`, `iqr`)  
  - Numeric fields are valid numbers  
  - Invariants are enforced:  
    - Quartiles ordering: `min ≤ Q1 ≤ median ≤ Q3 ≤ max`  
    - IQR = Q3 - Q1  
    - 95% CI bounds around the mean  

- ✅ **Variant-Specific Assertions**  
  - **single**: exactly one boxplot with one or multiple columns plotted  
  - **faceted_by_group**: contains all categories e.g. (`spring`, `summer`, `autumn`, `winter`)  
  - **multipanel_columns**: all expected dimensions e.g. (`length`, `width`, `height`, `weight`)  

- ✅ **Scenario-Specific Assertions**  
  - **normal / some_nans**: at least 2 valid data points per column  
  - **large**: n > 1000, standard deviation > 0, IQR > 0  

- ✅ **Error Response Validation**  
  - Proper structure with `success = false`, `error_code`, and `details`  
  - Specific error messages for:  
    - All-NaN datasets  
    - Less than 2 valid points  
    - Missing categories for `faceted_by_group` variant  

---

## 2. Configurable Options

### Variant (`variant`)
Determines the type of boxplot to generate:

| Variant | Description |
|---------|-------------|
| `single` | Single boxplot (vertical or horizontal) (Replaces old Boxplot1-4)|
| `faceted_by_group` | Faceted boxplots per category group e.g. (`spring`, `summer`, `autumn`, `winter`) (Replaces old Boxplot5)|
| `multipanel_columns` | Multiple columns rendered as separate panels e.g. (`length`, `width`, `height`, `weight`) (Replaces old Boxplot6)|

---

### Scenario (`scenario`)
Determines the dataset used for testing:

| Scenario | Description |
|----------|-------------|
| `normal` | Standard dataset with valid values |
| `some_nans` | Dataset containing some missing values (NaNs) |
| `large` | Large dataset (~10,000 points) to test performance |
| `n_less_than_2` | Dataset with fewer than 2 valid points, triggers validation error |
| `all_nans` | Dataset containing only NaN values, triggers validation error |

---

## 3. How to Run the Test

1. Set the desired **variant** and **scenario** in the pre-request script:
```javascript
pm.variables.set("variant", "faceted_by_group");
pm.variables.set("scenario", "normal");
```
2. Run the Postman request. The pre-request script automatically generates the payload.