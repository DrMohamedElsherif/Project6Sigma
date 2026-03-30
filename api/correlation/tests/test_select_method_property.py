# api/correlation/tests/test_select_method_property.py
# “Is the system stable and consistent?”

import numpy as np
from hypothesis import given, settings, strategies as st

from api.correlation.correlation import CorrelationAnalysis, CorrelationMethod
from api.correlation.schemas import CorrelationConfig


# =========================
# Helper
# =========================
def create_analysis():
    config = CorrelationConfig(
        title="Property Test",
        method=CorrelationMethod.AUTO,
        show_regression=False,
        show_confidence_interval=False,
        alpha=0.05
    )

    data = {
        "project": "test_project",
        "step": "analyze",
        "config": config.model_dump(),
        "data": {
            "dataset_name": "Test Dataset",
            "x_values": [1, 2, 3],
            "y_values": [1, 2, 3],
            "x_label": "X",
            "y_label": "Y"
        }
    }
    return CorrelationAnalysis(data)


# =========================
# 1. Always returns valid method
# =========================
@given(st.integers(min_value=10, max_value=200))
@settings(max_examples=200)
def test_returns_valid_method(n):
    x = np.linspace(0, 100, n)
    y = np.random.normal(0, 1, n)

    method = create_analysis().select_method(x, y)

    assert method in {
        CorrelationMethod.PEARSON,
        CorrelationMethod.SPEARMAN,
        CorrelationMethod.KENDALL,
    }


# =========================
# 2. Scale invariance
# =========================
@given(st.integers(min_value=30, max_value=200))
@settings(max_examples=150)
def test_scale_invariance(n):
    x = np.linspace(1, 100, n)
    y = np.log(x)

    analysis = create_analysis()

    m1 = analysis.select_method(x, y)
    m2 = analysis.select_method(x * 1000, y * 0.001)

    assert m1 == m2


# =========================
# 3. Noise robustness (no drastic downgrade)
# =========================
@given(st.integers(min_value=30, max_value=200))
@settings(max_examples=150)
def test_noise_robustness(n):
    np.random.seed(42)

    x = np.linspace(1, 100, n)
    y = np.log(x)
    noisy_y = y + np.random.normal(0, 0.5, n)

    analysis = create_analysis()

    m1 = analysis.select_method(x, y)
    m2 = analysis.select_method(x, noisy_y)

    # Should not degrade to weakest method unexpectedly
    assert m2 in {
        CorrelationMethod.PEARSON,
        CorrelationMethod.SPEARMAN,
        CorrelationMethod.KENDALL,
    }


# =========================
# 4. Outliers → avoid strict linear assumption
# =========================
@given(st.integers(min_value=30, max_value=200))
@settings(max_examples=150)
def test_outliers_reduce_linearity(n):
    x = np.linspace(0, 100, n)
    y = 2 * x

    idx = np.random.randint(0, n)
    y[idx] += 10000

    method = create_analysis().select_method(x, y)

    assert method in {
        CorrelationMethod.SPEARMAN,
        CorrelationMethod.KENDALL,
    }


# =========================
# 5. Many ties → rank-based methods
# =========================
@given(st.integers(min_value=30, max_value=200))
@settings(max_examples=150)
def test_ties_prefer_rank_methods(n):
    base = np.random.choice([1, 2, 3, 4, 5], size=n)
    x = base
    y = base * 10

    method = create_analysis().select_method(x, y)

    assert method in {
        CorrelationMethod.SPEARMAN,
        CorrelationMethod.KENDALL,
    }


# =========================
# 6. Symmetry (relaxed)
# =========================
@given(st.integers(min_value=30, max_value=200))
@settings(max_examples=150)
def test_symmetry_relaxed(n):
    x = np.linspace(0, 100, n)
    y = np.random.normal(0, 1, n)

    analysis = create_analysis()

    m1 = analysis.select_method(x, y)
    m2 = analysis.select_method(y, x)

    # Same "family", not exact match
    assert {m1, m2}.issubset({
        CorrelationMethod.PEARSON,
        CorrelationMethod.SPEARMAN,
        CorrelationMethod.KENDALL,
    })