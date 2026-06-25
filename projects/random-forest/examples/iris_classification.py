"""
Iris Classification Example - Random Forest on the classic Iris dataset.

This example demonstrates:
1. Loading and preparing the Iris dataset (without sklearn)
2. Training a Random Forest classifier
3. Evaluating with accuracy, precision, recall, F1
4. Analyzing feature importances
5. Comparing with a single decision tree

The Iris dataset contains 150 samples with 4 features:
- sepal length, sepal width, petal length, petal width
- 3 classes: setosa, versicolor, virginica (50 samples each)
"""

import numpy as np
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import RandomForestClassifier
from src.decision_tree import DecisionTreeClassifier
from src.evaluation import (
    accuracy,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
    train_test_split,
)


def load_iris_data():
    """Load the Iris dataset from raw data.

    Returns:
        Tuple of (X, y, feature_names, class_names).
    """
    # Iris dataset (Fisher, 1936) - 150 samples, 4 features, 3 classes
    # Features: sepal_length, sepal_width, petal_length, petal_width
    # Classes: 0=setosa, 1=versicolor, 2=virginica

    # Setosa (50 samples)
    setosa = np.array([
        [5.1, 3.5, 1.4, 0.2], [4.9, 3.0, 1.4, 0.2], [4.7, 3.2, 1.3, 0.2],
        [4.6, 3.1, 1.5, 0.2], [5.0, 3.6, 1.4, 0.2], [5.4, 3.9, 1.7, 0.4],
        [4.6, 3.4, 1.4, 0.3], [5.0, 3.4, 1.5, 0.2], [4.4, 2.9, 1.4, 0.2],
        [4.9, 3.1, 1.5, 0.1], [5.4, 3.7, 1.5, 0.2], [4.8, 3.4, 1.6, 0.2],
        [4.8, 3.0, 1.4, 0.1], [4.3, 3.0, 1.1, 0.1], [5.8, 4.0, 1.2, 0.2],
        [5.7, 4.4, 1.5, 0.4], [5.4, 3.9, 1.3, 0.4], [5.1, 3.5, 1.4, 0.3],
        [5.7, 3.8, 1.7, 0.3], [5.1, 3.8, 1.5, 0.3], [5.4, 3.4, 1.7, 0.2],
        [5.1, 3.7, 1.5, 0.4], [4.6, 3.6, 1.0, 0.2], [5.1, 3.3, 1.7, 0.5],
        [4.8, 3.4, 1.9, 0.2], [5.0, 3.0, 1.6, 0.2], [5.0, 3.4, 1.6, 0.4],
        [5.2, 3.5, 1.5, 0.2], [5.2, 3.4, 1.4, 0.2], [4.7, 3.2, 1.6, 0.2],
        [4.8, 3.1, 1.6, 0.2], [5.4, 3.4, 1.5, 0.4], [5.2, 4.1, 1.5, 0.1],
        [5.5, 4.2, 1.4, 0.2], [4.9, 3.1, 1.5, 0.2], [5.0, 3.2, 1.2, 0.2],
        [5.5, 3.5, 1.3, 0.2], [4.9, 3.6, 1.4, 0.1], [4.4, 3.0, 1.3, 0.2],
        [5.1, 3.4, 1.5, 0.2], [5.0, 3.5, 1.3, 0.3], [4.5, 2.3, 1.3, 0.3],
        [4.4, 3.2, 1.3, 0.2], [5.0, 3.5, 1.6, 0.6], [5.1, 3.8, 1.9, 0.4],
        [4.8, 3.0, 1.4, 0.3], [5.1, 3.8, 1.6, 0.2], [4.6, 3.2, 1.4, 0.2],
        [5.3, 3.7, 1.5, 0.2], [5.0, 3.3, 1.4, 0.2],
    ])

    # Versicolor (50 samples)
    versicolor = np.array([
        [7.0, 3.2, 4.7, 1.4], [6.4, 3.2, 4.5, 1.5], [6.9, 3.1, 4.9, 1.5],
        [5.5, 2.3, 4.0, 1.3], [6.5, 2.8, 4.6, 1.5], [5.7, 2.8, 4.5, 1.3],
        [6.3, 3.3, 4.7, 1.6], [4.9, 2.4, 3.3, 1.0], [6.6, 2.9, 4.6, 1.3],
        [5.2, 2.7, 3.9, 1.4], [5.0, 2.0, 3.5, 1.0], [5.9, 3.0, 4.2, 1.5],
        [6.0, 2.2, 4.0, 1.0], [6.1, 2.9, 4.7, 1.4], [5.6, 2.9, 3.6, 1.3],
        [6.7, 3.1, 4.4, 1.4], [5.6, 3.0, 4.5, 1.5], [5.8, 2.7, 4.1, 1.0],
        [6.2, 2.2, 4.5, 1.5], [5.6, 2.5, 3.9, 1.1], [5.9, 3.2, 4.8, 1.8],
        [6.1, 2.8, 4.0, 1.3], [6.3, 2.5, 4.9, 1.5], [6.1, 2.8, 4.7, 1.2],
        [6.4, 2.9, 4.3, 1.3], [6.6, 3.0, 4.4, 1.4], [6.8, 2.8, 4.8, 1.4],
        [6.7, 3.0, 5.0, 1.7], [6.0, 2.9, 4.5, 1.5], [5.7, 2.6, 3.5, 1.0],
        [5.5, 2.4, 3.8, 1.1], [5.5, 2.4, 3.7, 1.0], [5.8, 2.7, 3.9, 1.2],
        [6.0, 2.7, 5.1, 1.6], [5.4, 3.0, 4.5, 1.5], [6.0, 3.4, 4.5, 1.6],
        [6.7, 3.1, 4.7, 1.5], [6.3, 2.3, 4.4, 1.3], [5.6, 3.0, 4.1, 1.3],
        [5.5, 2.5, 4.0, 1.3], [5.5, 2.6, 4.4, 1.2], [6.1, 3.0, 4.6, 1.4],
        [5.8, 2.6, 4.0, 1.2], [5.0, 2.3, 3.3, 1.0], [5.6, 2.7, 4.2, 1.3],
        [5.7, 3.0, 4.2, 1.2], [5.7, 2.9, 4.2, 1.3], [6.2, 2.9, 4.3, 1.3],
        [5.1, 2.5, 3.0, 1.1], [5.7, 2.8, 4.1, 1.3],
    ])

    # Virginica (50 samples)
    virginica = np.array([
        [6.3, 3.3, 6.0, 2.5], [5.8, 2.7, 5.1, 1.9], [7.1, 3.0, 5.9, 2.1],
        [6.3, 2.9, 5.6, 1.8], [6.5, 3.0, 5.8, 2.2], [7.6, 3.0, 6.6, 2.1],
        [4.9, 2.5, 4.5, 1.7], [7.3, 2.9, 6.3, 1.8], [6.7, 2.5, 5.8, 1.8],
        [7.2, 3.6, 6.1, 2.5], [6.5, 3.2, 5.1, 2.0], [6.4, 2.7, 5.3, 1.9],
        [6.8, 3.0, 5.5, 2.1], [5.7, 2.5, 5.0, 2.0], [5.8, 2.8, 5.1, 2.4],
        [6.4, 3.2, 5.3, 2.3], [6.5, 3.0, 5.5, 1.8], [7.7, 3.8, 6.7, 2.2],
        [7.7, 2.6, 6.9, 2.3], [6.0, 2.2, 5.0, 1.5], [6.9, 3.2, 5.7, 2.3],
        [5.6, 2.8, 4.9, 2.0], [7.7, 2.8, 6.7, 2.0], [6.3, 2.7, 4.9, 1.8],
        [6.7, 3.3, 5.7, 2.1], [7.2, 3.2, 6.0, 1.8], [6.2, 2.8, 4.8, 1.8],
        [6.1, 3.0, 4.9, 1.8], [6.4, 2.8, 5.6, 2.1], [7.2, 3.0, 5.8, 1.6],
        [7.4, 2.8, 6.1, 1.9], [7.9, 3.8, 6.4, 2.0], [6.4, 2.8, 5.6, 2.2],
        [6.3, 2.8, 5.1, 1.5], [6.1, 2.6, 5.6, 1.4], [7.7, 3.0, 6.1, 2.3],
        [6.3, 3.4, 5.6, 2.4], [6.4, 3.1, 5.5, 1.8], [6.0, 3.0, 4.8, 1.8],
        [6.9, 3.1, 5.4, 2.1], [6.7, 3.1, 5.6, 2.4], [6.9, 3.1, 5.1, 2.3],
        [5.8, 2.7, 5.1, 1.9], [6.8, 3.2, 5.9, 2.3], [6.7, 3.3, 5.7, 2.5],
        [6.7, 3.0, 5.2, 2.3], [6.3, 2.5, 5.0, 1.9], [6.5, 3.0, 5.2, 2.0],
        [6.2, 3.4, 5.4, 2.3], [5.9, 3.0, 5.1, 1.8],
    ])

    X = np.vstack([setosa, versicolor, virginica])
    y = np.array([0] * 50 + [1] * 50 + [2] * 50)

    feature_names = ["sepal_length", "sepal_width", "petal_length", "petal_width"]
    class_names = ["setosa", "versicolor", "virginica"]

    return X, y, feature_names, class_names


def main():
    """Run the Iris classification example."""
    print("=" * 60)
    print("  Iris Classification with Random Forest")
    print("=" * 60)

    # 1. Load data
    print("\n[1] Loading Iris dataset...")
    X, y, feature_names, class_names = load_iris_data()
    print(f"    Samples: {X.shape[0]}, Features: {X.shape[1]}")
    print(f"    Classes: {class_names}")
    print(f"    Feature names: {feature_names}")

    # 2. Split data
    print("\n[2] Splitting data (80% train, 20% test)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"    Train: {len(X_train)} samples")
    print(f"    Test:  {len(X_test)} samples")

    # 3. Train Random Forest
    print("\n[3] Training Random Forest (100 trees)...")
    rf = RandomForestClassifier(
        n_estimators=100,
        max_depth=5,
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
    print(f"    Accuracy:  {accuracy(y_test, y_pred):.4f}")
    print(f"    Precision: {precision_score(y_test, y_pred, average='macro'):.4f}")
    print(f"    Recall:    {recall_score(y_test, y_pred, average='macro'):.4f}")
    print(f"    F1-Score:  {f1_score(y_test, y_pred, average='macro'):.4f}")

    # 6. Classification report
    print("\n[6] Classification Report:")
    print(classification_report(y_test, y_pred, target_names=class_names))

    # 7. Confusion matrix
    print("\n[7] Confusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    print(f"    {'':>12} ", end="")
    for name in class_names:
        print(f"{name:>12}", end="")
    print()
    for i, name in enumerate(class_names):
        print(f"    {name:>12} ", end="")
        for j in range(len(class_names)):
            print(f"{cm[i, j]:>12d}", end="")
        print()

    # 8. Feature importance
    print("\n[8] Feature Importance (Impurity-based):")
    for name, imp in zip(feature_names, rf.feature_importances_):
        bar = "#" * int(imp * 40)
        print(f"    {name:>15}: {imp:.4f} {bar}")

    # 9. OOB Score
    print(f"\n[9] Out-of-Bag Score: {rf.oob_score_:.4f}")

    # 10. Compare with single tree
    print("\n[10] Comparison with Single Decision Tree:")
    single_tree = DecisionTreeClassifier(max_depth=5, random_state=42)
    single_tree.fit(X_train, y_train)
    single_accuracy = single_tree.score(X_test, y_test)
    rf_accuracy = rf.score(X_test, y_test)

    print(f"     Single Tree Accuracy:  {single_accuracy:.4f}")
    print(f"     Random Forest Accuracy: {rf_accuracy:.4f}")
    print(f"     Improvement:            {rf_accuracy - single_accuracy:+.4f}")

    print("\n" + "=" * 60)
    print("  Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
