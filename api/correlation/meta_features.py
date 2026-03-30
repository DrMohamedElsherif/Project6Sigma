# import numpy as np
# from scipy import stats
# from api.correlation.utils import (
#     check_linearity,
#     detect_outliers,
#     detect_pattern_type,
#     has_many_ties
# )

# def extract_features(x, y):
#     n = len(x)

#     try:
#         r, _ = stats.pearsonr(x, y)
#     except:
#         r = 0

#     try:
#         rho, _ = stats.spearmanr(x, y)
#     except:
#         rho = 0

#     pattern = detect_pattern_type(x, y)

#     return [
#         n,
#         int(check_linearity(x, y)),
#         int(detect_outliers(x) or detect_outliers(y)),
#         int(has_many_ties(x) or has_many_ties(y)),
#         abs(r),
#         abs(rho),
#         abs(rho) - abs(r),
#         int(pattern == "linear"),
#         int(pattern == "quadratic"),
#         int(pattern == "exponential"),
#     ]