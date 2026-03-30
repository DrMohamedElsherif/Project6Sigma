import numpy as np
from api.correlation.correlation import CorrelationAnalysis
from api.correlation.schemas import CorrelationConfig, CorrelationMethod


# -----------------------
# Create analysis instance
# -----------------------
def create_analysis():
    config = CorrelationConfig(
        title="Tuning",
        method=CorrelationMethod.AUTO,
        show_regression=False,
        show_confidence_interval=False,
        alpha=0.05
    )

    data = {
        "project": "tuning",
        "step": "analyze",
        "config": config.model_dump(),
        "data": {
            "dataset_name": "dummy",
            "x_values": [1, 2, 3],
            "y_values": [1, 2, 3],
            "x_label": "X",
            "y_label": "Y"
        }
    }

    return CorrelationAnalysis(data)


# -----------------------
# Synthetic training data
# -----------------------
def generate_training_cases():
    cases = []
    n = 200

    # Linear → Pearson
    x = np.linspace(1, 100, n)
    y = 3*x + np.random.normal(0, 1, n)
    cases.append((x, y, "pearson"))

    # Monotonic nonlinear → Spearman
    x = np.linspace(1, 100, n)
    y = np.log(x)
    cases.append((x, y, "spearman"))

    # Nonlinear non-monotonic → Kendall
    x = np.linspace(1, 100, n)
    y = x**2
    cases.append((x, y, "kendall"))

    # Outliers → Spearman
    x = np.linspace(1, 100, n)
    y = 2*x.copy()
    y[10] += 10000
    cases.append((x, y, "spearman"))

    # Ties → Kendall
    x = np.random.choice([1,2,3,4,5], size=n)
    y = x * 10
    cases.append((x, y, "kendall"))
    
    # Weak monotonic (borderline)
    y = np.log(x) + np.random.normal(0, 5, n)
    cases.append((x, y, "spearman"))

    # Noisy linear (Pearson should still win)
    y = 3*x + np.random.normal(0, 20, n)
    cases.append((x, y, "pearson"))

    # Slightly non-monotonic
    y = x + 10*np.sin(x/10)
    cases.append((x, y, "spearman"))

    # Almost random
    y = np.random.normal(0, 1, n)
    cases.append((x, y, "kendall"))

    return cases


# -----------------------
# Evaluate one threshold
# -----------------------
def evaluate_threshold(threshold, cases):
    analysis = create_analysis()
    correct = 0

    for x, y, expected in cases:
        method = analysis.select_method(x, y, rho_threshold=threshold).value
        if method == expected:
            correct += 1
    
    return correct / len(cases)


# -----------------------
# Grid search
# -----------------------
def find_best_threshold():
    best_t = None
    best_score = -1

    thresholds = np.linspace(0.5, 0.9, 20)

    for t in thresholds:
        cases = generate_training_cases()
        score = evaluate_threshold(t, cases)

        print(f"threshold={t:.3f} → accuracy={score:.2%}")

        if score > best_score:
            best_score = score
            best_t = t

    print("\n=== BEST RESULT ===")
    print(f"threshold={best_t:.3f}, accuracy={best_score:.2%}")

    return best_t


# -----------------------
# Monte Carlo (robust)
# -----------------------
def monte_carlo_optimization(runs=30):
    thresholds = np.linspace(0.5, 0.9, 20)
    scores = {t: [] for t in thresholds}

    for _ in range(runs):
        cases = generate_training_cases()

        for t in thresholds:
            score = evaluate_threshold(t, cases)
            scores[t].append(score)

    avg_scores = {t: np.mean(v) for t, v in scores.items()}
    best = max(avg_scores.items(), key=lambda x: x[1])

    print("\n=== MONTE CARLO RESULTS ===")
    for t, s in sorted(avg_scores.items()):
        print(f"{t:.3f} → {s:.3f}")

    print(f"\nBEST: threshold={best[0]:.3f}, score={best[1]:.3f}")

    return best


# -----------------------
# Run
# -----------------------
if __name__ == "__main__":
    np.random.seed(42)

    print("\n--- SIMPLE GRID SEARCH ---")
    find_best_threshold()

    print("\n--- MONTE CARLO ---")
    monte_carlo_optimization()