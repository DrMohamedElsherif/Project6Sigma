# import numpy as np
# import pytest

# from sklearn import datasets
# import seaborn as sns

# from api.correlation.correlation import CorrelationAnalysis, CorrelationMethod
# from api.correlation.schemas import CorrelationConfig


# # =========================
# # Helper
# # =========================
# def create_analysis():
#     config = CorrelationConfig(
#         title="Real Data Test",
#         method=CorrelationMethod.AUTO,
#         show_regression=False,
#         show_confidence_interval=False,
#         alpha=0.05
#     )

#     data = {
#         "project": "real_data",
#         "step": "analyze",
#         "config": config.model_dump(),
#         "data": {
#             "dataset_name": "Real Dataset",
#             "x_values": [1, 2, 3],
#             "y_values": [1, 2, 3],
#             "x_label": "X",
#             "y_label": "Y"
#         }
#     }
#     return CorrelationAnalysis(data)


# # =========================
# # 1. IRIS → linear → Pearson
# # =========================
# def test_iris_linear_relationship():
#     iris = datasets.load_iris()

#     x = iris.data[:, 0]  # sepal length
#     y = iris.data[:, 2]  # petal length

#     analysis = create_analysis()
#     method = analysis.select_method(x, y)

#     assert method == CorrelationMethod.PEARSON


# # =========================
# # 2. Tips → monotonic → Spearman
# # =========================
# def test_tips_monotonic_relationship():
#     tips = sns.load_dataset("tips")

#     x = tips["total_bill"].values
#     y = tips["tip"].values

#     analysis = create_analysis()
#     method = analysis.select_method(x, y)

#     assert method in {
#         CorrelationMethod.SPEARMAN,
#         CorrelationMethod.PEARSON,  # allow fallback
#     }


# # =========================
# # 3. Anscombe → detect nonlinearity
# # =========================
# def test_anscombe_nonlinear_detected():
#     df = sns.load_dataset("anscombe")

#     dataset = df[df["dataset"] == "II"]

#     x = dataset["x"].values
#     y = dataset["y"].values

#     analysis = create_analysis()
#     method = analysis.select_method(x, y)

#     # Dataset II is nonlinear → should NOT be Pearson
#     assert method in {
#         CorrelationMethod.SPEARMAN,
#         CorrelationMethod.KENDALL,
#     }


# # =========================
# # 4. Anscombe with outliers
# # =========================
# def test_anscombe_outliers_detected():
#     df = sns.load_dataset("anscombe")

#     dataset = df[df["dataset"] == "III"]

#     x = dataset["x"].values
#     y = dataset["y"].values

#     analysis = create_analysis()
#     method = analysis.select_method(x, y)

#     # Contains outliers → avoid Pearson
#     assert method in {
#         CorrelationMethod.SPEARMAN,
#         CorrelationMethod.KENDALL,
#     }


# # =========================
# # 5. Stability on real data
# # =========================
# def test_real_data_noise_stability():
#     iris = datasets.load_iris()

#     x = iris.data[:, 0]
#     y = iris.data[:, 2]

#     noisy_y = y + np.random.normal(0, 0.5, len(y))

#     analysis = create_analysis()

#     m1 = analysis.select_method(x, y)
#     m2 = analysis.select_method(x, noisy_y)

#     assert m2 in {
#         CorrelationMethod.PEARSON,
#         CorrelationMethod.SPEARMAN,
#     }