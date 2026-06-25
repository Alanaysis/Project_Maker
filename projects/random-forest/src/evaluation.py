"""
Model Evaluation Metrics - From-scratch implementation of common ML metrics.

This module provides:
- Classification metrics: accuracy, precision, recall, F1-score
- Regression metrics: MSE, RMSE, MAE, R-squared
- Permutation importance: model-agnostic feature importance
- Confusion matrix and classification report utilities

All metrics are implemented from scratch using only NumPy.
"""

import numpy as np
from typing import Optional, Dict, List


# =============================================================================
# Classification Metrics
# =============================================================================


def accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate classification accuracy.

    Accuracy = (number of correct predictions) / (total predictions)

    Args:
        y_true: True class labels (n_samples,).
        y_pred: Predicted class labels (n_samples,).

    Returns:
        Accuracy score in [0, 1].
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    return np.mean(y_true == y_pred)


def confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray, labels: Optional[np.ndarray] = None) -> np.ndarray:
    """Compute the confusion matrix.

    The confusion matrix C is such that C[i, j] is the number of observations
    known to be in group i and predicted to be in group j.

    Args:
        y_true: True class labels.
        y_pred: Predicted class labels.
        labels: List of labels to index the matrix. If None, uses sorted unique labels.

    Returns:
        Confusion matrix of shape (n_classes, n_classes).
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    if labels is None:
        labels = np.unique(np.concatenate([y_true, y_pred]))

    n_labels = len(labels)
    label_to_idx = {label: idx for idx, label in enumerate(labels)}

    cm = np.zeros((n_labels, n_labels), dtype=int)
    for true, pred in zip(y_true, y_pred):
        if true in label_to_idx and pred in label_to_idx:
            cm[label_to_idx[true], label_to_idx[pred]] += 1

    return cm


def precision_score(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    average: str = "macro",
    labels: Optional[np.ndarray] = None,
) -> float:
    """Calculate precision.

    Precision = TP / (TP + FP)

    For multiclass, supports averaging strategies:
    - 'macro': Calculate precision for each class, then take unweighted mean.
    - 'micro': Calculate global TP, FP, FN, then compute precision.
    - 'weighted': Weighted mean by support (number of true samples per class).

    Args:
        y_true: True class labels.
        y_pred: Predicted class labels.
        average: Averaging strategy ('macro', 'micro', 'weighted').
        labels: Class labels.

    Returns:
        Precision score.
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    if labels is None:
        labels = np.unique(np.concatenate([y_true, y_pred]))

    cm = confusion_matrix(y_true, y_pred, labels)

    if average == "micro":
        tp = np.trace(cm)
        total_predicted = np.sum(cm)
        return tp / total_predicted if total_predicted > 0 else 0.0

    precisions = np.zeros(len(labels))
    for i in range(len(labels)):
        tp = cm[i, i]
        fp = np.sum(cm[:, i]) - tp
        precisions[i] = tp / (tp + fp) if (tp + fp) > 0 else 0.0

    if average == "macro":
        return np.mean(precisions)
    elif average == "weighted":
        support = np.sum(cm, axis=1)
        total = np.sum(support)
        return np.sum(precisions * support) / total if total > 0 else 0.0
    else:
        raise ValueError(f"Unknown average: {average}")


def recall_score(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    average: str = "macro",
    labels: Optional[np.ndarray] = None,
) -> float:
    """Calculate recall.

    Recall = TP / (TP + FN)

    Args:
        y_true: True class labels.
        y_pred: Predicted class labels.
        average: Averaging strategy ('macro', 'micro', 'weighted').
        labels: Class labels.

    Returns:
        Recall score.
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    if labels is None:
        labels = np.unique(np.concatenate([y_true, y_pred]))

    cm = confusion_matrix(y_true, y_pred, labels)

    if average == "micro":
        tp = np.trace(cm)
        total_actual = np.sum(cm)
        return tp / total_actual if total_actual > 0 else 0.0

    recalls = np.zeros(len(labels))
    for i in range(len(labels)):
        tp = cm[i, i]
        fn = np.sum(cm[i, :]) - tp
        recalls[i] = tp / (tp + fn) if (tp + fn) > 0 else 0.0

    if average == "macro":
        return np.mean(recalls)
    elif average == "weighted":
        support = np.sum(cm, axis=1)
        total = np.sum(support)
        return np.sum(recalls * support) / total if total > 0 else 0.0
    else:
        raise ValueError(f"Unknown average: {average}")


def f1_score(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    average: str = "macro",
    labels: Optional[np.ndarray] = None,
) -> float:
    """Calculate F1-score.

    F1 = 2 * (precision * recall) / (precision + recall)

    This is the harmonic mean of precision and recall, providing a single
    metric that balances both concerns.

    Args:
        y_true: True class labels.
        y_pred: Predicted class labels.
        average: Averaging strategy ('macro', 'micro', 'weighted').
        labels: Class labels.

    Returns:
        F1-score.
    """
    p = precision_score(y_true, y_pred, average=average, labels=labels)
    r = recall_score(y_true, y_pred, average=average, labels=labels)

    if p + r == 0:
        return 0.0
    return 2 * (p * r) / (p + r)


def classification_report(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    labels: Optional[np.ndarray] = None,
    target_names: Optional[List[str]] = None,
) -> str:
    """Build a text report showing the main classification metrics.

    Args:
        y_true: True class labels.
        y_pred: Predicted class labels.
        labels: Class labels.
        target_names: Display names for each class.

    Returns:
        Formatted classification report string.
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    if labels is None:
        labels = np.unique(np.concatenate([y_true, y_pred]))

    if target_names is None:
        target_names = [str(label) for label in labels]

    cm = confusion_matrix(y_true, y_pred, labels)

    lines = []
    header = f"{'':>15} {'precision':>10} {'recall':>10} {'f1-score':>10} {'support':>10}"
    lines.append(header)
    lines.append("-" * len(header))

    total_support = 0
    weighted_precision = 0.0
    weighted_recall = 0.0
    weighted_f1 = 0.0

    for i, name in enumerate(target_names):
        tp = cm[i, i]
        fp = np.sum(cm[:, i]) - tp
        fn = np.sum(cm[i, :]) - tp
        support = np.sum(cm[i, :])

        p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (p * r) / (p + r) if (p + r) > 0 else 0.0

        lines.append(f"{name:>15} {p:>10.2f} {r:>10.2f} {f1:>10.2f} {support:>10d}")

        total_support += support
        weighted_precision += p * support
        weighted_recall += r * support
        weighted_f1 += f1 * support

    lines.append("-" * len(header))

    wp = weighted_precision / total_support if total_support > 0 else 0.0
    wr = weighted_recall / total_support if total_support > 0 else 0.0
    wf = weighted_f1 / total_support if total_support > 0 else 0.0
    lines.append(f"{'weighted avg':>15} {wp:>10.2f} {wr:>10.2f} {wf:>10.2f} {total_support:>10d}")

    return "\n".join(lines)


# =============================================================================
# Regression Metrics
# =============================================================================


def mean_squared_error(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate mean squared error.

    MSE = (1/n) * sum((y_true - y_pred)^2)

    Args:
        y_true: True values.
        y_pred: Predicted values.

    Returns:
        MSE value (lower is better, 0 = perfect).
    """
    y_true = np.asarray(y_true, dtype=np.float64)
    y_pred = np.asarray(y_pred, dtype=np.float64)
    return np.mean((y_true - y_pred) ** 2)


def root_mean_squared_error(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate root mean squared error.

    RMSE = sqrt(MSE)

    Same unit as the target variable, making it more interpretable than MSE.

    Args:
        y_true: True values.
        y_pred: Predicted values.

    Returns:
        RMSE value (lower is better, 0 = perfect).
    """
    return np.sqrt(mean_squared_error(y_true, y_pred))


def mean_absolute_error(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate mean absolute error.

    MAE = (1/n) * sum(|y_true - y_pred|)

    Args:
        y_true: True values.
        y_pred: Predicted values.

    Returns:
        MAE value (lower is better, 0 = perfect).
    """
    y_true = np.asarray(y_true, dtype=np.float64)
    y_pred = np.asarray(y_pred, dtype=np.float64)
    return np.mean(np.abs(y_true - y_pred))


def r2_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate R-squared (coefficient of determination).

    R^2 = 1 - SS_res / SS_tot
    where:
        SS_res = sum((y_true - y_pred)^2)  (residual sum of squares)
        SS_tot = sum((y_true - mean(y_true))^2)  (total sum of squares)

    Interpretation:
        - R^2 = 1: Perfect predictions
        - R^2 = 0: Predictions are as good as predicting the mean
        - R^2 < 0: Predictions are worse than predicting the mean

    Args:
        y_true: True values.
        y_pred: Predicted values.

    Returns:
        R-squared value (higher is better, max = 1).
    """
    y_true = np.asarray(y_true, dtype=np.float64)
    y_pred = np.asarray(y_pred, dtype=np.float64)

    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)

    if ss_tot == 0:
        return 0.0

    return 1.0 - ss_res / ss_tot


# =============================================================================
# Permutation Importance
# =============================================================================


def permutation_importance(
    model,
    X: np.ndarray,
    y: np.ndarray,
    n_repeats: int = 10,
    random_state: Optional[int] = None,
    scoring: str = "accuracy",
) -> Dict[str, np.ndarray]:
    """Calculate permutation importance for each feature.

    Permutation importance measures how much the model's performance drops
    when a single feature's values are randomly shuffled. This breaks the
    relationship between the feature and the target.

    Algorithm:
    1. Compute baseline score with all features intact
    2. For each feature:
       a. Repeat n_repeats times:
          - Randomly shuffle the feature's values
          - Compute the model's score on the permuted data
       b. Importance = baseline_score - mean(permuted_scores)
    3. Features with higher importance are more valuable to the model

    This is model-agnostic: it works with any model that has a predict method.

    Args:
        model: A fitted model with predict() method.
        X: Feature matrix (n_samples, n_features).
        y: True labels or values.
        n_repeats: Number of times to repeat the permutation per feature.
        random_state: Random seed for reproducibility.
        scoring: Scoring function name ('accuracy', 'mse', 'r2').

    Returns:
        Dictionary with:
        - 'importances_mean': Mean importance for each feature (n_features,)
        - 'importances_std': Standard deviation of importance (n_features,)
        - 'importances': Raw importance values (n_features, n_repeats)
    """
    X = np.asarray(X, dtype=np.float64)
    y = np.asarray(y)

    rng = np.random.RandomState(random_state)
    n_samples, n_features = X.shape

    # Select scoring function
    if scoring == "accuracy":
        score_fn = lambda y_true, y_pred: np.mean(y_true == y_pred)
    elif scoring == "mse":
        score_fn = lambda y_true, y_pred: -np.mean((y_true - y_pred) ** 2)  # Negative so higher is better
    elif scoring == "r2":
        score_fn = lambda y_true, y_pred: 1 - np.sum((y_true - y_pred) ** 2) / np.sum((y_true - np.mean(y_true)) ** 2) if np.sum((y_true - np.mean(y_true)) ** 2) > 0 else 0.0
    else:
        raise ValueError(f"Unknown scoring: {scoring}")

    # Compute baseline score
    baseline_pred = model.predict(X)
    baseline_score = score_fn(y, baseline_pred)

    # Compute importance for each feature
    importances = np.zeros((n_features, n_repeats))

    for feature_idx in range(n_features):
        for repeat in range(n_repeats):
            # Create a copy with the feature shuffled
            X_permuted = X.copy()
            X_permuted[:, feature_idx] = rng.permutation(X_permuted[:, feature_idx])

            # Compute score with permuted feature
            permuted_pred = model.predict(X_permuted)
            permuted_score = score_fn(y, permuted_pred)

            # Importance = drop in performance
            importances[feature_idx, repeat] = baseline_score - permuted_score

    return {
        "importances_mean": np.mean(importances, axis=1),
        "importances_std": np.std(importances, axis=1),
        "importances": importances,
        "baseline_score": baseline_score,
    }


# =============================================================================
# Train/Test Split Utility
# =============================================================================


def train_test_split(
    X: np.ndarray,
    y: np.ndarray,
    test_size: float = 0.2,
    random_state: Optional[int] = None,
) -> tuple:
    """Split arrays into random train and test subsets.

    Args:
        X: Feature matrix.
        y: Target values.
        test_size: Fraction of data to use for testing (0-1).
        random_state: Random seed for reproducibility.

    Returns:
        Tuple of (X_train, X_test, y_train, y_test).
    """
    X = np.asarray(X)
    y = np.asarray(y)

    n_samples = len(X)
    n_test = int(n_samples * test_size)
    n_train = n_samples - n_test

    rng = np.random.RandomState(random_state)
    indices = rng.permutation(n_samples)

    train_indices = indices[:n_train]
    test_indices = indices[n_train:]

    return X[train_indices], X[test_indices], y[train_indices], y[test_indices]
