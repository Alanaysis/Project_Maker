"""
Feature Importance Analysis - Deep dive into how Random Forest measures feature importance.

This example demonstrates:
1. Impurity-based importance (built into the tree)
2. Permutation importance (model-agnostic)
3. Comparing the two methods
4. Visualizing importance rankings
5. Understanding when each method is appropriate
"""

import numpy as np
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import RandomForestClassifier
from src.random_forest_regressor import RandomForestRegressor
from src.evaluation import (
    permutation_importance,
    train_test_split,
    accuracy,
    r2_score,
)


def generate_classification_data(n_samples=300, random_state=42):
    """Generate data where we know which features are important.

    Features:
    - feature_0: Strong signal (directly determines class)
    - feature_1: Strong signal (directly determines class)
    - feature_2: Weak signal (noisy correlation)
    - feature_3: Noise (no relationship to class)
    - feature_4: Noise (no relationship to class)
    - feature_5: Noise (no relationship to class)

    Args:
        n_samples: Number of samples.
        random_state: Random seed.

    Returns:
        Tuple of (X, y, feature_names, true_importance).
    """
    rng = np.random.RandomState(random_state)

    feature_0 = rng.randn(n_samples)
    feature_1 = rng.randn(n_samples)
    feature_2 = rng.randn(n_samples) * 0.5 + 0.3 * feature_0  # Weak, correlated
    feature_3 = rng.randn(n_samples)  # Pure noise
    feature_4 = rng.randn(n_samples)  # Pure noise
    feature_5 = rng.randn(n_samples)  # Pure noise

    X = np.column_stack([feature_0, feature_1, feature_2, feature_3, feature_4, feature_5])

    # Class determined mainly by feature_0 and feature_1
    y = ((feature_0 + feature_1 + 0.2 * feature_2) > 0).astype(int)

    feature_names = [
        "feature_0 (strong)",
        "feature_1 (strong)",
        "feature_2 (weak)",
        "feature_3 (noise)",
        "feature_4 (noise)",
        "feature_5 (noise)",
    ]

    # True relative importance (approximate)
    true_importance = np.array([0.40, 0.40, 0.10, 0.03, 0.03, 0.03])

    return X, y, feature_names, true_importance


def generate_regression_data(n_samples=300, random_state=42):
    """Generate regression data with known feature importance.

    Args:
        n_samples: Number of samples.
        random_state: Random seed.

    Returns:
        Tuple of (X, y, feature_names, true_importance).
    """
    rng = np.random.RandomState(random_state)

    feature_0 = rng.uniform(0, 10, n_samples)
    feature_1 = rng.uniform(0, 10, n_samples)
    feature_2 = rng.uniform(0, 10, n_samples)
    feature_3 = rng.randn(n_samples)  # Noise
    feature_4 = rng.randn(n_samples)  # Noise

    X = np.column_stack([feature_0, feature_1, feature_2, feature_3, feature_4])

    # Target is dominated by feature_0, with some contribution from feature_1
    y = 10 * feature_0 + 3 * feature_1 + 0.5 * feature_2 + rng.normal(0, 1, n_samples)

    feature_names = [
        "x0 (strong, coef=10)",
        "x1 (medium, coef=3)",
        "x2 (weak, coef=0.5)",
        "x3 (noise)",
        "x4 (noise)",
    ]

    true_importance = np.array([0.70, 0.20, 0.05, 0.025, 0.025])

    return X, y, feature_names, true_importance


def print_importance_table(feature_names, importances, title):
    """Print a formatted importance table."""
    print(f"\n  {title}:")
    print(f"  {'Feature':>25} {'Importance':>12} {'Bar'}")
    print(f"  {'-'*25} {'-'*12} {'-'*30}")

    # Sort by importance
    sorted_indices = np.argsort(-importances)
    for idx in sorted_indices:
        name = feature_names[idx]
        imp = importances[idx]
        bar = "#" * max(0, int(imp * 50))
        print(f"  {name:>25} {imp:>12.4f} {bar}")


def main():
    """Run the feature importance analysis."""
    print("=" * 70)
    print("  Feature Importance Analysis with Random Forest")
    print("=" * 70)

    # =========================================================================
    # Part 1: Classification
    # =========================================================================
    print("\n" + "=" * 70)
    print("  PART 1: Classification Feature Importance")
    print("=" * 70)

    # Generate data
    print("\n[1] Generating classification data...")
    X, y, feature_names, true_importance = generate_classification_data()
    print(f"    Samples: {X.shape[0]}, Features: {X.shape[1]}")
    print(f"    Class distribution: {dict(zip(*np.unique(y, return_counts=True)))}")

    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

    # Train
    print("\n[2] Training Random Forest Classifier (200 trees)...")
    rf = RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42)
    rf.fit(X_train, y_train)

    print(f"    Train accuracy: {accuracy(y_train, rf.predict(X_train)):.4f}")
    print(f"    Test accuracy:  {accuracy(y_test, rf.predict(X_test)):.4f}")
    print(f"    OOB accuracy:   {rf.oob_score_:.4f}")

    # Impurity-based importance
    print_importance_table(feature_names, rf.feature_importances_, "Impurity-based Importance")

    # Permutation importance
    print("\n[3] Computing permutation importance (50 repeats)...")
    perm_result = permutation_importance(
        rf, X_test, y_test, n_repeats=50, random_state=42, scoring="accuracy"
    )
    print_importance_table(
        feature_names, perm_result["importances_mean"], "Permutation Importance (Test Set)"
    )

    # Compare methods
    print("\n[4] Comparison of Methods:")
    print(f"    {'Feature':>25} {'Impurity':>10} {'Permutation':>12} {'True':>10}")
    print(f"    {'-'*25} {'-'*10} {'-'*12} {'-'*10}")
    for i, name in enumerate(feature_names):
        imp = rf.feature_importances_[i]
        perm = perm_result["importances_mean"][i]
        true = true_importance[i]
        print(f"    {name:>25} {imp:>10.4f} {perm:>12.4f} {true:>10.4f}")

    # =========================================================================
    # Part 2: Regression
    # =========================================================================
    print("\n" + "=" * 70)
    print("  PART 2: Regression Feature Importance")
    print("=" * 70)

    # Generate data
    print("\n[1] Generating regression data...")
    X, y, feature_names, true_importance = generate_regression_data()
    print(f"    Samples: {X.shape[0]}, Features: {X.shape[1]}")

    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

    # Train
    print("\n[2] Training Random Forest Regressor (200 trees)...")
    rf_reg = RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42)
    rf_reg.fit(X_train, y_train)

    train_r2 = r2_score(y_train, rf_reg.predict(X_train))
    test_r2 = r2_score(y_test, rf_reg.predict(X_test))
    print(f"    Train R-squared: {train_r2:.4f}")
    print(f"    Test R-squared:  {test_r2:.4f}")
    print(f"    OOB R-squared:   {rf_reg.oob_score_:.4f}")

    # Impurity-based importance
    print_importance_table(feature_names, rf_reg.feature_importances_, "Impurity-based Importance")

    # Permutation importance
    print("\n[3] Computing permutation importance (50 repeats)...")
    perm_result_reg = permutation_importance(
        rf_reg, X_test, y_test, n_repeats=50, random_state=42, scoring="r2"
    )
    print_importance_table(
        feature_names, perm_result_reg["importances_mean"], "Permutation Importance (Test Set)"
    )

    # Compare methods
    print("\n[4] Comparison of Methods:")
    print(f"    {'Feature':>25} {'Impurity':>10} {'Permutation':>12} {'True':>10}")
    print(f"    {'-'*25} {'-'*10} {'-'*12} {'-'*10}")
    for i, name in enumerate(feature_names):
        imp = rf_reg.feature_importances_[i]
        perm = perm_result_reg["importances_mean"][i]
        true = true_importance[i]
        print(f"    {name:>25} {imp:>10.4f} {perm:>12.4f} {true:>10.4f}")

    # =========================================================================
    # Part 3: Key Insights
    # =========================================================================
    print("\n" + "=" * 70)
    print("  KEY INSIGHTS")
    print("=" * 70)
    print("""
    1. Impurity-based importance:
       - Fast to compute (calculated during training)
       - Can be biased toward high-cardinality features
       - Tends to overestimate importance of correlated features

    2. Permutation importance:
       - Model-agnostic (works with any model)
       - More reliable for correlated features
       - Slower (requires multiple predictions)
       - Can be negative (feature hurts performance)

    3. Both methods should agree on truly important features.
       When they disagree, permutation importance is usually more trustworthy.

    4. Always check importance on TEST data to avoid overfitting bias.
    """)

    print("=" * 70)
    print("  Done!")
    print("=" * 70)


if __name__ == "__main__":
    main()
