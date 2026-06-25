"""
Evaluation Metrics for Text Classification.

This module provides comprehensive evaluation metrics for classification tasks:
- Accuracy: Overall correctness
- Precision: Exactness (how many selected items are relevant)
- Recall: Completeness (how many relevant items are selected)
- F1 Score: Harmonic mean of precision and recall
- Confusion Matrix: Detailed breakdown of predictions vs actual labels

These metrics help understand model performance beyond simple accuracy.
"""

from collections import defaultdict
from typing import Dict, List, Optional, Tuple


def accuracy(y_true: List[str], y_pred: List[str]) -> float:
    """
    Compute accuracy classification score.

    Parameters
    ----------
    y_true : list of str
        Ground truth (correct) labels.
    y_pred : list of str
        Predicted labels, as returned by a classifier.

    Returns
    -------
    float
        Accuracy score in range [0, 1].
    """
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have the same length")

    if len(y_true) == 0:
        return 0.0

    correct = sum(1 for true, pred in zip(y_true, y_pred) if true == pred)
    return correct / len(y_true)


def precision(
    y_true: List[str],
    y_pred: List[str],
    average: str = "macro",
) -> float:
    """
    Compute precision score.

    Parameters
    ----------
    y_true : list of str
        Ground truth labels.
    y_pred : list of str
        Predicted labels.
    average : str, default='macro'
        Averaging strategy: 'macro', 'micro', 'weighted'.

    Returns
    -------
    float
        Precision score.
    """
    classes = sorted(set(y_true) | set(y_pred))

    if average == "micro":
        tp_total = 0
        fp_total = 0
        for cls in classes:
            tp = sum(1 for t, p in zip(y_true, y_pred) if t == cls and p == cls)
            fp = sum(1 for t, p in zip(y_true, y_pred) if t != cls and p == cls)
            tp_total += tp
            fp_total += fp
        return tp_total / (tp_total + fp_total) if (tp_total + fp_total) > 0 else 0.0

    precisions = []
    weights = []
    for cls in classes:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == cls and p == cls)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != cls and p == cls)
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        precisions.append(prec)
        weights.append(sum(1 for t in y_true if t == cls))

    if average == "weighted":
        total = sum(weights)
        return sum(p * w for p, w in zip(precisions, weights)) / total if total > 0 else 0.0
    else:  # macro
        return sum(precisions) / len(precisions) if precisions else 0.0


def recall(
    y_true: List[str],
    y_pred: List[str],
    average: str = "macro",
) -> float:
    """
    Compute recall score.

    Parameters
    ----------
    y_true : list of str
        Ground truth labels.
    y_pred : list of str
        Predicted labels.
    average : str, default='macro'
        Averaging strategy: 'macro', 'micro', 'weighted'.

    Returns
    -------
    float
        Recall score.
    """
    classes = sorted(set(y_true) | set(y_pred))

    if average == "micro":
        tp_total = 0
        fn_total = 0
        for cls in classes:
            tp = sum(1 for t, p in zip(y_true, y_pred) if t == cls and p == cls)
            fn = sum(1 for t, p in zip(y_true, y_pred) if t == cls and p != cls)
            tp_total += tp
            fn_total += fn
        return tp_total / (tp_total + fn_total) if (tp_total + fn_total) > 0 else 0.0

    recalls = []
    weights = []
    for cls in classes:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == cls and p == cls)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == cls and p != cls)
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        recalls.append(rec)
        weights.append(sum(1 for t in y_true if t == cls))

    if average == "weighted":
        total = sum(weights)
        return sum(r * w for r, w in zip(recalls, weights)) / total if total > 0 else 0.0
    else:  # macro
        return sum(recalls) / len(recalls) if recalls else 0.0


def f1_score(
    y_true: List[str],
    y_pred: List[str],
    average: str = "macro",
) -> float:
    """
    Compute F1 score.

    Parameters
    ----------
    y_true : list of str
        Ground truth labels.
    y_pred : list of str
        Predicted labels.
    average : str, default='macro'
        Averaging strategy: 'macro', 'micro', 'weighted'.

    Returns
    -------
    float
        F1 score.
    """
    p = precision(y_true, y_pred, average)
    r = recall(y_true, y_pred, average)

    if p + r == 0:
        return 0.0

    return 2 * p * r / (p + r)


def confusion_matrix(
    y_true: List[str],
    y_pred: List[str],
) -> Dict[str, Dict[str, int]]:
    """
    Compute confusion matrix.

    Parameters
    ----------
    y_true : list of str
        Ground truth labels.
    y_pred : list of str
        Predicted labels.

    Returns
    -------
    dict of dict
        Confusion matrix as nested dictionary.
        matrix[true_label][pred_label] = count.
    """
    classes = sorted(set(y_true) | set(y_pred))

    matrix = {cls: {c: 0 for c in classes} for cls in classes}

    for true, pred in zip(y_true, y_pred):
        matrix[true][pred] += 1

    return matrix


def classification_report(
    y_true: List[str],
    y_pred: List[str],
) -> str:
    """
    Build a text report showing the main classification metrics.

    Parameters
    ----------
    y_true : list of str
        Ground truth labels.
    y_pred : list of str
        Predicted labels.

    Returns
    -------
    str
        Text summary of the precision, recall, F1 score for each class.
    """
    classes = sorted(set(y_true) | set(y_pred))

    # Compute per-class metrics
    report_lines = []
    report_lines.append(f"{'Class':<15} {'Precision':>10} {'Recall':>10} {'F1-Score':>10} {'Support':>10}")
    report_lines.append("-" * 60)

    total_support = 0
    weighted_precision = 0.0
    weighted_recall = 0.0
    weighted_f1 = 0.0

    for cls in classes:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == cls and p == cls)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != cls and p == cls)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == cls and p != cls)

        support = sum(1 for t in y_true if t == cls)
        total_support += support

        p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0

        weighted_precision += p * support
        weighted_recall += r * support
        weighted_f1 += f1 * support

        report_lines.append(f"{cls:<15} {p:>10.4f} {r:>10.4f} {f1:>10.4f} {support:>10}")

    report_lines.append("-" * 60)

    # Macro averages
    macro_p = precision(y_true, y_pred, "macro")
    macro_r = recall(y_true, y_pred, "macro")
    macro_f1 = f1_score(y_true, y_pred, "macro")
    report_lines.append(f"{'Macro Avg':<15} {macro_p:>10.4f} {macro_r:>10.4f} {macro_f1:>10.4f} {total_support:>10}")

    # Weighted averages
    w_p = weighted_precision / total_support if total_support > 0 else 0.0
    w_r = weighted_recall / total_support if total_support > 0 else 0.0
    w_f1 = weighted_f1 / total_support if total_support > 0 else 0.0
    report_lines.append(f"{'Weighted Avg':<15} {w_p:>10.4f} {w_r:>10.4f} {w_f1:>10.4f} {total_support:>10}")

    # Overall accuracy
    acc = accuracy(y_true, y_pred)
    report_lines.append(f"\nAccuracy: {acc:.4f}")

    return "\n".join(report_lines)


def evaluate_classifier(
    y_true: List[str],
    y_pred: List[str],
) -> Dict[str, float]:
    """
    Compute all evaluation metrics.

    Parameters
    ----------
    y_true : list of str
        Ground truth labels.
    y_pred : list of str
        Predicted labels.

    Returns
    -------
    dict
        Dictionary containing all metrics.
    """
    return {
        "accuracy": accuracy(y_true, y_pred),
        "precision_macro": precision(y_true, y_pred, "macro"),
        "precision_micro": precision(y_true, y_pred, "micro"),
        "precision_weighted": precision(y_true, y_pred, "weighted"),
        "recall_macro": recall(y_true, y_pred, "macro"),
        "recall_micro": recall(y_true, y_pred, "micro"),
        "recall_weighted": recall(y_true, y_pred, "weighted"),
        "f1_macro": f1_score(y_true, y_pred, "macro"),
        "f1_micro": f1_score(y_true, y_pred, "micro"),
        "f1_weighted": f1_score(y_true, y_pred, "weighted"),
    }
