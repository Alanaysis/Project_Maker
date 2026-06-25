"""
Tests for Evaluation Metrics.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.evaluation import (
    accuracy,
    precision,
    recall,
    f1_score,
    confusion_matrix,
    classification_report,
    evaluate_classifier,
)


class TestEvaluationMetrics:
    """Test evaluation metric functions."""

    def test_accuracy_perfect(self):
        """Test accuracy with perfect predictions."""
        y_true = ["a", "b", "c", "a", "b"]
        y_pred = ["a", "b", "c", "a", "b"]

        assert accuracy(y_true, y_pred) == 1.0

    def test_accuracy_zero(self):
        """Test accuracy with all wrong predictions."""
        y_true = ["a", "a", "a"]
        y_pred = ["b", "b", "b"]

        assert accuracy(y_true, y_pred) == 0.0

    def test_accuracy_partial(self):
        """Test accuracy with partial correct predictions."""
        y_true = ["a", "b", "a", "b"]
        y_pred = ["a", "a", "b", "b"]

        assert accuracy(y_true, y_pred) == 0.5

    def test_precision_macro(self):
        """Test macro precision."""
        y_true = ["a", "a", "b", "b"]
        y_pred = ["a", "b", "a", "b"]

        p = precision(y_true, y_pred, average="macro")
        assert 0 <= p <= 1

    def test_precision_micro(self):
        """Test micro precision."""
        y_true = ["a", "a", "b", "b"]
        y_pred = ["a", "b", "a", "b"]

        p = precision(y_true, y_pred, average="micro")
        assert p == 0.5

    def test_precision_weighted(self):
        """Test weighted precision."""
        y_true = ["a", "a", "a", "b"]
        y_pred = ["a", "a", "b", "b"]

        p = precision(y_true, y_pred, average="weighted")
        assert 0 <= p <= 1

    def test_recall_macro(self):
        """Test macro recall."""
        y_true = ["a", "a", "b", "b"]
        y_pred = ["a", "b", "a", "b"]

        r = recall(y_true, y_pred, average="macro")
        assert 0 <= r <= 1

    def test_recall_micro(self):
        """Test micro recall."""
        y_true = ["a", "a", "b", "b"]
        y_pred = ["a", "b", "a", "b"]

        r = recall(y_true, y_pred, average="micro")
        assert r == 0.5

    def test_recall_weighted(self):
        """Test weighted recall."""
        y_true = ["a", "a", "a", "b"]
        y_pred = ["a", "a", "b", "b"]

        r = recall(y_true, y_pred, average="weighted")
        assert 0 <= r <= 1

    def test_f1_score_macro(self):
        """Test macro F1 score."""
        y_true = ["a", "a", "b", "b"]
        y_pred = ["a", "b", "a", "b"]

        f1 = f1_score(y_true, y_pred, average="macro")
        assert 0 <= f1 <= 1

    def test_f1_score_micro(self):
        """Test micro F1 score."""
        y_true = ["a", "a", "b", "b"]
        y_pred = ["a", "b", "a", "b"]

        f1 = f1_score(y_true, y_pred, average="micro")
        assert f1 == 0.5

    def test_f1_perfect(self):
        """Test F1 with perfect predictions."""
        y_true = ["a", "b", "c"]
        y_pred = ["a", "b", "c"]

        f1 = f1_score(y_true, y_pred)
        assert f1 == 1.0

    def test_confusion_matrix(self):
        """Test confusion matrix."""
        y_true = ["a", "a", "b", "b"]
        y_pred = ["a", "b", "a", "b"]

        matrix = confusion_matrix(y_true, y_pred)

        assert matrix["a"]["a"] == 1  # True positive for a
        assert matrix["a"]["b"] == 1  # False negative for a
        assert matrix["b"]["a"] == 1  # False positive for a
        assert matrix["b"]["b"] == 1  # True negative for a

    def test_confusion_matrix_perfect(self):
        """Test confusion matrix with perfect predictions."""
        y_true = ["a", "b", "c"]
        y_pred = ["a", "b", "c"]

        matrix = confusion_matrix(y_true, y_pred)

        assert matrix["a"]["a"] == 1
        assert matrix["b"]["b"] == 1
        assert matrix["c"]["c"] == 1
        assert matrix["a"]["b"] == 0
        assert matrix["a"]["c"] == 0

    def test_classification_report(self):
        """Test classification report."""
        y_true = ["a", "a", "b", "b", "c", "c"]
        y_pred = ["a", "b", "b", "c", "c", "a"]

        report = classification_report(y_true, y_pred)

        assert isinstance(report, str)
        assert "Precision" in report
        assert "Recall" in report
        assert "F1-Score" in report
        assert "Accuracy" in report

    def test_evaluate_classifier(self):
        """Test comprehensive evaluation."""
        y_true = ["a", "a", "b", "b"]
        y_pred = ["a", "b", "a", "b"]

        metrics = evaluate_classifier(y_true, y_pred)

        assert "accuracy" in metrics
        assert "precision_macro" in metrics
        assert "recall_macro" in metrics
        assert "f1_macro" in metrics

    def test_length_mismatch(self):
        """Test that mismatched lengths raise error."""
        y_true = ["a", "b"]
        y_pred = ["a"]

        with pytest.raises(ValueError):
            accuracy(y_true, y_pred)

    def test_empty_lists(self):
        """Test with empty lists."""
        assert accuracy([], []) == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
