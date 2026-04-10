# api/correlation/optimize_threshold_v2.py

import numpy as np
from scipy import stats
from typing import Dict, List, Tuple
from api.correlation.utils import (
    check_linearity,
    detect_outliers,
    detect_pattern_type,
    has_many_ties,
    check_normality
)
from api.correlation.correlation import CorrelationAnalysis
from api.correlation.schemas import CorrelationMethod

class CorrelationOptimizer:
    """Optimize correlation method selection using ground truth data"""
    
    def __init__(self):
        self.best_params = {
            'rho_threshold': 0.7,
            'outlier_threshold': 0.05,
            'small_sample_threshold': 30,
            'tie_threshold': 0.2
        }
    
    def generate_realistic_cases(self, n_cases=500) -> List[Tuple]:
        """Generate realistic test cases with ground truth"""
        cases = []
        
        # 1. Perfect linear (Pearson)
        for _ in range(50):
            x = np.random.uniform(0, 100, 100)
            noise = np.random.normal(0, np.random.uniform(1, 5), 100)
            y = 2*x + noise
            cases.append((x, y, CorrelationMethod.PEARSON))
        
        # 2. Linear with outliers (Spearman)
        for _ in range(50):
            x = np.random.uniform(0, 100, 100)
            y = 2*x + np.random.normal(0, 2, 100)
            # Add 10% outliers
            outlier_idx = np.random.choice(len(x), size=int(len(x)*0.1), replace=False)
            y[outlier_idx] += np.random.normal(0, 50, len(outlier_idx))
            cases.append((x, y, CorrelationMethod.SPEARMAN))
        
        # 3. Monotonic nonlinear (Spearman)
        for _ in range(50):
            x = np.random.uniform(1, 100, 100)
            y = np.log(x) + np.random.normal(0, 0.1, 100)
            cases.append((x, y, CorrelationMethod.SPEARMAN))
        
        # 4. Non-monotonic quadratic (Kendall - lower correlation)
        for _ in range(50):
            x = np.random.uniform(-5, 5, 100)
            y = x**2 + np.random.normal(0, 1, 100)
            cases.append((x, y, CorrelationMethod.KENDALL))
        
        # 5. Many ties (Kendall)
        for _ in range(50):
            x = np.random.choice([1,2,3,4,5,6,7,8,9,10], size=100)
            y = x * 2 + np.random.choice([-1,0,1], size=100)
            cases.append((x, y, CorrelationMethod.KENDALL))
        
        # 6. Small sample (n<30) - linear (Pearson still works)
        for _ in range(50):
            x = np.random.uniform(0, 100, 20)
            y = 3*x + np.random.normal(0, 5, 20)
            cases.append((x, y, CorrelationMethod.PEARSON))
        
        # 7. Small sample with outliers (Spearman)
        for _ in range(50):
            x = np.random.uniform(0, 100, 20)
            y = 2*x + np.random.normal(0, 3, 20)
            y[0] += 100  # extreme outlier
            cases.append((x, y, CorrelationMethod.SPEARMAN))
        
        # 8. Weak relationships (Kendall - robust)
        for _ in range(50):
            x = np.random.uniform(0, 100, 100)
            y = x + np.random.normal(0, 50, 100)  # high noise
            cases.append((x, y, CorrelationMethod.KENDALL))
        
        # 9. Exponential (Spearman for monotonic)
        for _ in range(50):
            x = np.random.uniform(0, 5, 100)
            y = np.exp(x) + np.random.normal(0, 1, 100)
            cases.append((x, y, CorrelationMethod.SPEARMAN))
        
        # 10. Cyclic/sinusoidal (Kendall - no monotonic trend)
        for _ in range(50):
            x = np.linspace(0, 4*np.pi, 100)
            y = np.sin(x) + np.random.normal(0, 0.1, 100)
            cases.append((x, y, CorrelationMethod.KENDALL))
        
        return cases
    
    def improved_select_method(self, x: np.ndarray, y: np.ndarray, params: Dict) -> CorrelationMethod:
        """Improved method selection with tunable parameters"""
        n = len(x)
        
        # Check ties
        many_ties = has_many_ties(x, threshold=params['tie_threshold']) or \
                    has_many_ties(y, threshold=params['tie_threshold'])
        
        if many_ties:
            return CorrelationMethod.KENDALL
        
        # Small sample handling
        if n < params['small_sample_threshold']:
            # Check for outliers in small samples
            has_outliers = detect_outliers(x) or detect_outliers(y)
            if has_outliers:
                return CorrelationMethod.SPEARMAN
            return CorrelationMethod.PEARSON
        
        # Assumption checks
        is_linear = check_linearity(x, y)
        has_outliers = detect_outliers(x, threshold=3) or detect_outliers(y, threshold=3)
        
        # Calculate correlations
        try:
            r, _ = stats.pearsonr(x, y)
            rho, _ = stats.spearmanr(x, y)
        except:
            r = rho = 0
        
        # Nonlinear monotonic detection
        is_monotonic = abs(rho) > params['rho_threshold']
        is_nonlinear = not is_linear
        nonlinear_monotonic = is_monotonic and is_nonlinear
        
        if nonlinear_monotonic:
            return CorrelationMethod.SPEARMAN
        
        if has_outliers and not is_linear:
            return CorrelationMethod.SPEARMAN
        
        # Default decisions
        if is_linear and n >= params['small_sample_threshold']:
            return CorrelationMethod.PEARSON
        
        return CorrelationMethod.SPEARMAN
    
    def evaluate_params(self, params: Dict, validation_split=0.3) -> float:
        """Evaluate parameter set with cross-validation"""
        all_cases = self.generate_realistic_cases(500)
        
        # Split into train/validation
        np.random.shuffle(all_cases)
        split_idx = int(len(all_cases) * (1 - validation_split))
        train_cases = all_cases[:split_idx]
        val_cases = all_cases[split_idx:]
        
        # No need to train, just evaluate on validation
        correct = 0
        for x, y, expected_method in val_cases:
            predicted_method = self.improved_select_method(x, y, params)
            if predicted_method == expected_method:
                correct += 1
        
        return correct / len(val_cases)
    
    def grid_search(self) -> Dict:
        """Perform grid search over parameter space"""
        param_grid = {
            'rho_threshold': [0.5, 0.6, 0.7, 0.8, 0.9],
            'outlier_threshold': [0.03, 0.05, 0.07, 0.1],
            'small_sample_threshold': [20, 25, 30, 35, 40],
            'tie_threshold': [0.15, 0.2, 0.25, 0.3]
        }
        
        best_score = 0
        best_params = None
        results = []
        
        total_combinations = np.prod([len(v) for v in param_grid.values()])
        print(f"Testing {total_combinations} combinations...")
        
        for rho_th in param_grid['rho_threshold']:
            for out_th in param_grid['outlier_threshold']:
                for sample_th in param_grid['small_sample_threshold']:
                    for tie_th in param_grid['tie_threshold']:
                        params = {
                            'rho_threshold': rho_th,
                            'outlier_threshold': out_th,
                            'small_sample_threshold': sample_th,
                            'tie_threshold': tie_th
                        }
                        
                        # Use 3-fold cross-validation
                        scores = []
                        for fold in range(5):
                            score = self.evaluate_params(params)
                            scores.append(score)
                        
                        avg_score = np.mean(scores)
                        results.append((params, avg_score))
                        
                        if avg_score > best_score:
                            best_score = avg_score
                            best_params = params
                            print(f"New best: {best_score:.3f} with {best_params}")
        
        print(f"\nBest Score: {best_score:.3f}")
        print(f"Best Params: {best_params}")
        
        return best_params
    
    def monte_carlo_optimization(self, n_iterations=100):
        """Random search for parameter optimization"""
        best_score = 0
        best_params = None
        scores = []
        
        for i in range(n_iterations):
            # Random parameter sampling
            params = {
                'rho_threshold': np.random.uniform(0.5, 0.9),
                'outlier_threshold': np.random.uniform(0.02, 0.15),
                'small_sample_threshold': np.random.randint(15, 50),
                'tie_threshold': np.random.uniform(0.1, 0.4)
            }
            
            # Quick evaluation
            score = self.evaluate_params(params, validation_split=0.2)
            scores.append((params, score))
            
            if score > best_score:
                best_score = score
                best_params = params
                print(f"Iteration {i}: Score={best_score:.3f}, Params={best_params}")
        
        # Sort by score
        scores.sort(key=lambda x: x[1], reverse=True)
        
        print("\n=== TOP 5 PARAMETER SETS ===")
        for i in range(min(5, len(scores))):
            print(f"{i+1}. Score={scores[i][1]:.3f}, Params={scores[i][0]}")
        
        return best_params, best_score

def analyze_decision_boundaries():
    """Analyze where decisions are made"""
    optimizer = CorrelationOptimizer()
    
    # Test different scenarios
    test_scenarios = [
        ("Small linear clean", np.random.uniform(0,100,25), 
         lambda x: 2*x + np.random.normal(0,2,25)),
        ("Small linear outliers", np.random.uniform(0,100,25),
         lambda x: 2*x + np.random.normal(0,2,25), True),
        ("Large linear clean", np.random.uniform(0,100,200),
         lambda x: 2*x + np.random.normal(0,2,200)),
        ("Large monotonic", np.random.uniform(1,100,200),
         lambda x: np.log(x) + np.random.normal(0,0.1,200)),
        ("Many ties", np.random.choice([1,2,3,4,5], size=100),
         lambda x: x*2),
    ]
    
    print("\n=== DECISION BOUNDARY ANALYSIS ===")
    params = optimizer.best_params
    
    for name, x_gen, y_gen in test_scenarios:
        x = x_gen if callable(x_gen) else x_gen
        if callable(y_gen):
            y = y_gen(x)
        
        method = optimizer.improved_select_method(x, y, params)
        
        # Calculate statistics
        r, _ = stats.pearsonr(x, y)
        rho, _ = stats.spearmanr(x, y)
        n_ties_x = len(np.unique(x)) / len(x)
        n_ties_y = len(np.unique(y)) / len(y)
        
        print(f"\n{name}:")
        print(f"  n={len(x)}, r={r:.3f}, ρ={rho:.3f}")
        print(f"  Unique ratio: x={n_ties_x:.2f}, y={n_ties_y:.2f}")
        print(f"  Selected: {method.value}")
        print(f"  Linear: {check_linearity(x, y)}")
        print(f"  Outliers: {detect_outliers(x) or detect_outliers(y)}")

if __name__ == "__main__":
    np.random.seed(42)
    
    optimizer = CorrelationOptimizer()
    
    print("=== MONTE CARLO OPTIMIZATION ===")
    best_params, best_score = optimizer.monte_carlo_optimization(n_iterations=200)
    
    print("\n=== FINAL RECOMMENDED PARAMETERS ===")
    print(f"rho_threshold: {best_params['rho_threshold']:.3f}")
    print(f"outlier_threshold: {best_params['outlier_threshold']:.3f}")
    print(f"small_sample_threshold: {best_params['small_sample_threshold']:.0f}")
    print(f"tie_threshold: {best_params['tie_threshold']:.3f}")
    print(f"Expected accuracy: {best_score:.1%}")
    
    # Update the correlation.py file with these parameters
    print("\n=== UPDATE YOUR correlation.py ===")
    print(f"""
    # In select_method method, update:
    def select_method(self, x: np.ndarray, y: np.ndarray) -> CorrelationMethod:
        # Use these optimized parameters:
        rho_threshold = {best_params['rho_threshold']:.3f}
        outlier_threshold = {best_params['outlier_threshold']:.3f}
        small_sample_threshold = {best_params['small_sample_threshold']:.0f}
        tie_threshold = {best_params['tie_threshold']:.3f}
        
        # ... rest of the method using these parameters
    """)