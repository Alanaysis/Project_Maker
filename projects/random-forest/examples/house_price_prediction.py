"""
House Price Prediction Example - Random Forest Regressor on synthetic housing data.

This example demonstrates:
1. Generating a realistic synthetic housing dataset
2. Training a Random Forest regressor
3. Evaluating with MSE, RMSE, MAE, R-squared
4. Analyzing feature importances
5. Comparing with a single regression tree
6. Permutation importance analysis
"""

import numpy as np
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.random_forest_regressor import RandomForestRegressor, DecisionTreeRegressor
from src.evaluation import (
    mean_squared_error,
    root_mean_squared_error,
    mean_absolute_error,
    r2_score,
    permutation_importance,
    train_test_split,
)


def generate_housing_data(n_samples: int = 500, random_state: int = 42):
    """Generate a synthetic housing dataset.

    Features:
    - area: House area in square meters (50-300)
    - bedrooms: Number of bedrooms (1-5)
    - age: Age of the house in years (0-50)
    - distance_center: Distance to city center in km (1-30)
    - has_garden: Whether the house has a garden (0 or 1)
    - floors: Number of floors (1-3)

    Price is a nonlinear function of these features with some noise.

    Args:
        n_samples: Number of samples to generate.
        random_state: Random seed.

    Returns:
        Tuple of (X, y, feature_names).
    """
    rng = np.random.RandomState(random_state)

    # Generate features
    area = rng.uniform(50, 300, n_samples)
    bedrooms = rng.randint(1, 6, n_samples).astype(float)
    age = rng.uniform(0, 50, n_samples)
    distance_center = rng.uniform(1, 30, n_samples)
    has_garden = rng.randint(0, 2, n_samples).astype(float)
    floors = rng.randint(1, 4, n_samples).astype(float)

    # Generate price (nonlinear function with interactions)
    price = (
        2000 * area                       # Area is most important
        + 15000 * bedrooms                # More bedrooms = higher price
        - 500 * age                       # Older houses are cheaper
        - 3000 * distance_center          # Closer to center = more expensive
        + 25000 * has_garden              # Garden adds value
        + 10000 * floors                  # More floors = higher price
        + 5 * area * bedrooms             # Interaction: large + many bedrooms
        - 10 * area * (age / 50)          # Interaction: large but old
        + rng.normal(0, 20000, n_samples)  # Random noise
    )

    # Ensure positive prices
    price = np.maximum(price, 50000)

    X = np.column_stack([area, bedrooms, age, distance_center, has_garden, floors])
    feature_names = ["area", "bedrooms", "age", "distance_center", "has_garden", "floors"]

    return X, price, feature_names


def main():
    """Run the house price prediction example."""
    print("=" * 60)
    print("  House Price Prediction with Random Forest Regressor")
    print("=" * 60)

    # 1. Generate data
    print("\n[1] Generating synthetic housing dataset...")
    X, y, feature_names = generate_housing_data(n_samples=500, random_state=42)
    print(f"    Samples: {X.shape[0]}, Features: {X.shape[1]}")
    print(f"    Features: {feature_names}")
    print(f"    Price range: ${y.min():,.0f} - ${y.max():,.0f}")
    print(f"    Mean price:  ${y.mean():,.0f}")

    # 2. Split data
    print("\n[2] Splitting data (80% train, 20% test)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"    Train: {len(X_train)} samples")
    print(f"    Test:  {len(X_test)} samples")

    # 3. Train Random Forest Regressor
    print("\n[3] Training Random Forest Regressor (100 trees)...")
    rf = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        max_features="sqrt",
        bootstrap=True,
        random_state=42,
    )
    rf.fit(X_train, y_train)

    # 4. Predictions
    print("\n[4] Making predictions...")
    y_pred = rf.predict(X_test)

    # 5. Evaluation metrics
    print("\n[5] Evaluation Metrics:")
    print(f"    MSE:  {mean_squared_error(y_test, y_pred):,.0f}")
    print(f"    RMSE: {root_mean_squared_error(y_test, y_pred):,.0f}")
    print(f"    MAE:  {mean_absolute_error(y_test, y_pred):,.0f}")
    print(f"    R-squared: {r2_score(y_test, y_pred):.4f}")

    # 6. OOB Score
    print(f"\n[6] Out-of-Bag R-squared: {rf.oob_score_:.4f}")

    # 7. Feature importance (impurity-based)
    print("\n[7] Feature Importance (Impurity-based):")
    for name, imp in sorted(
        zip(feature_names, rf.feature_importances_), key=lambda x: -x[1]
    ):
        bar = "#" * int(imp * 40)
        print(f"    {name:>18}: {imp:.4f} {bar}")

    # 8. Permutation importance
    print("\n[8] Feature Importance (Permutation-based):")
    perm_imp = permutation_importance(
        rf, X_test, y_test, n_repeats=20, random_state=42, scoring="r2"
    )
    sorted_idx = np.argsort(-perm_imp["importances_mean"])
    for idx in sorted_idx:
        name = feature_names[idx]
        mean_imp = perm_imp["importances_mean"][idx]
        std_imp = perm_imp["importances_std"][idx]
        bar = "#" * max(0, int(mean_imp * 40))
        print(f"    {name:>18}: {mean_imp:.4f} (+/- {std_imp:.4f}) {bar}")

    # 9. Show some predictions vs actual
    print("\n[9] Sample Predictions (first 10 test samples):")
    print(f"    {'Actual':>15} {'Predicted':>15} {'Error':>15} {'Error%':>10}")
    print(f"    {'-'*15} {'-'*15} {'-'*15} {'-'*10}")
    for i in range(min(10, len(y_test))):
        actual = y_test[i]
        predicted = y_pred[i]
        error = predicted - actual
        error_pct = abs(error / actual) * 100
        print(f"    ${actual:>13,.0f} ${predicted:>13,.0f} ${error:>13,.0f} {error_pct:>9.1f}%")

    # 10. Compare with single tree
    print("\n[10] Comparison with Single Regression Tree:")
    single_tree = DecisionTreeRegressor(max_depth=10, random_state=42)
    single_tree.fit(X_train, y_train)
    single_pred = single_tree.predict(X_test)

    single_r2 = r2_score(y_test, single_pred)
    rf_r2 = r2_score(y_test, y_pred)

    print(f"     Single Tree R-squared:  {single_r2:.4f}")
    print(f"     Random Forest R-squared: {rf_r2:.4f}")
    print(f"     Improvement:             {rf_r2 - single_r2:+.4f}")

    single_rmse = root_mean_squared_error(y_test, single_pred)
    rf_rmse = root_mean_squared_error(y_test, y_pred)
    print(f"     Single Tree RMSE:  ${single_rmse:,.0f}")
    print(f"     Random Forest RMSE: ${rf_rmse:,.0f}")

    print("\n" + "=" * 60)
    print("  Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
