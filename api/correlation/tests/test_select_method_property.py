# # Test suite for CorrelationAnalysis.select_method property
# # api/correlation/tests/test_select_method_property.py

# import numpy as np
# import pytest
# from hypothesis import given, settings, strategies as st, assume

# from api.correlation.correlation import CorrelationAnalysis, CorrelationMethod
# from api.correlation.schemas import CorrelationConfig


# # =========================
# # Helper
# # =========================
# def create_analysis():
#     config = CorrelationConfig(
#         title="Property Test",
#         method=CorrelationMethod.AUTO,
#         show_regression=False,
#         show_confidence_interval=False,
#         alpha=0.05
#     )

#     data = {
#         "project": "test_project",
#         "step": "analyze",
#         "config": config.model_dump(),
#         "data": {
#             "dataset_name": "Test Dataset",
#             "x_values": [1, 2, 3],
#             "y_values": [1, 2, 3],
#             "x_label": "X",
#             "y_label": "Y"
#         }
#     }
#     return CorrelationAnalysis(data)


# # =========================
# # 1. Always returns valid method
# # =========================
# @given(
#     x=st.lists(st.floats(-1e6, 1e6, allow_nan=False, allow_infinity=False), min_size=10, max_size=200),
#     y=st.lists(st.floats(-1e6, 1e6, allow_nan=False, allow_infinity=False), min_size=10, max_size=200),
# )
# @settings(max_examples=300)
# def test_always_returns_valid_method(x, y):
#     assume(len(x) == len(y))

#     analysis = create_analysis()
#     method = analysis.select_method(np.array(x), np.array(y))

#     assert method in {
#         CorrelationMethod.PEARSON,
#         CorrelationMethod.SPEARMAN,
#         CorrelationMethod.KENDALL,
#     }


# # =========================
# # 2. Linear data → Pearson
# # =========================
# @given(st.integers(min_value=10, max_value=200))
# @settings(max_examples=150)
# def test_linear_data_prefers_pearson(n):
#     x = np.linspace(0, 100, n)
#     noise = np.random.normal(0, 0.1, n)
#     y = 3 * x + 5 + noise

#     analysis = create_analysis()
#     method = analysis.select_method(x, y)

#     assert method == CorrelationMethod.PEARSON


# # =========================
# # 3. Monotonic nonlinear → Spearman
# # =========================
# @given(st.integers(min_value=10, max_value=200))
# @settings(max_examples=150)
# def test_monotonic_nonlinear_prefers_spearman(n):
#     x = np.linspace(1, 100, n)
#     y = np.log(x)

#     analysis = create_analysis()
#     method = analysis.select_method(x, y)

#     assert method == CorrelationMethod.SPEARMAN


# # =========================
# # 4. Outliers → NOT Pearson
# # =========================
# @given(st.integers(min_value=20, max_value=200))
# @settings(max_examples=150)
# def test_outliers_avoid_pearson(n):
#     x = np.linspace(0, 100, n)
#     y = 2 * x

#     # Inject strong outlier
#     idx = np.random.randint(0, n)
#     y[idx] += np.random.uniform(1000, 10000)

#     analysis = create_analysis()
#     method = analysis.select_method(x, y)

#     assert method in {
#         CorrelationMethod.SPEARMAN,
#         CorrelationMethod.KENDALL,
#     }


# # =========================
# # 5. Many ties → Kendall
# # =========================
# @given(st.integers(min_value=20, max_value=200))
# @settings(max_examples=150)
# def test_many_ties_prefers_kendall(n):
#     base = np.random.choice([1, 2, 3, 4, 5], size=n)
#     x = base
#     y = base * 10

#     analysis = create_analysis()
#     method = analysis.select_method(x, y)

#     assert method == CorrelationMethod.KENDALL


# # =========================
# # 6. Symmetry: f(x,y) == f(y,x)
# # =========================
# @given(
#     x=st.lists(st.floats(-100, 100, allow_nan=False, allow_infinity=False), min_size=20, max_size=200),
#     y=st.lists(st.floats(-100, 100, allow_nan=False, allow_infinity=False), min_size=20, max_size=200),
# )
# @settings(max_examples=200)
# def test_symmetry(x, y):
#     assume(len(x) == len(y))

#     x = np.array(x)
#     y = np.array(y)

#     analysis = create_analysis()

#     m1 = analysis.select_method(x, y)
#     m2 = analysis.select_method(y, x)

#     assert m1 == m2


# # =========================
# # 7. Scale invariance
# # =========================
# @given(st.integers(min_value=20, max_value=200))
# @settings(max_examples=150)
# def test_scale_invariance(n):
#     x = np.linspace(1, 100, n)
#     y = np.log(x)

#     analysis = create_analysis()

#     m1 = analysis.select_method(x, y)
#     m2 = analysis.select_method(x * 1000, y * 0.001)

#     assert m1 == m2


# # =========================
# # 8. Noise robustness
# # =========================
# @given(st.integers(min_value=20, max_value=200))
# @settings(max_examples=150)
# def test_noise_stability(n):
#     x = np.linspace(1, 100, n)
#     y = np.log(x)

#     noisy_y = y + np.random.normal(0, 0.5, n)

#     analysis = create_analysis()

#     m1 = analysis.select_method(x, y)
#     m2 = analysis.select_method(x, noisy_y)

#     assert m1 == m2


# # =========================
# # 9. Monotonic + outlier → Spearman
# # =========================
# @given(st.integers(min_value=20, max_value=200))
# @settings(max_examples=150)
# def test_monotonic_with_outlier_prefers_spearman(n):
#     x = np.linspace(1, 100, n)
#     y = np.log(x)

#     # Add outlier
#     idx = np.random.randint(0, n)
#     y[idx] += 50

#     analysis = create_analysis()
#     method = analysis.select_method(x, y)

#     assert method == CorrelationMethod.SPEARMAN


# # =========================
# # 10. Constant data should fail
# # =========================
# @given(st.integers(min_value=5, max_value=50))
# @settings(max_examples=50)
# def test_constant_data_raises(n):
#     x = np.ones(n)
#     y = np.ones(n)

#     analysis = create_analysis()

#     with pytest.raises(Exception):
#         analysis.select_method(x, y)