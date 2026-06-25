"""
Tests for Logistic Regression Classifier.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.logistic_regression import LogisticRegressionClassifier


class TestLogisticRegressionClassifier:
    """Test LogisticRegressionClassifier functionality."""

    def test_init(self):
        """Test classifier initialization."""
        clf = LogisticRegressionClassifier()
        assert clf.learning_rate == 0.01
        assert clf.max_iter == 1000
        assert clf.regularization == 0.01

    def test_sigmoid(self):
        """Test sigmoid function."""
        clf = LogisticRegressionClassifier()

        # sigmoid(0) = 0.5
        assert abs(clf._sigmoid(0) - 0.5) < 1e-6

        # Large positive -> ~1
        assert clf._sigmoid(100) > 0.99

        # Large negative -> ~0
        assert clf._sigmoid(-100) < 0.01

    def test_fit_binary(self):
        """Test binary classification."""
        X = [
            [1, 0],
            [0, 1],
            [1, 0],
            [0, 1],
        ]
        y = ["a", "b", "a", "b"]

        clf = LogisticRegressionClassifier(learning_rate=0.1, max_iter=100)
        clf.fit(X, y)

        assert len(clf.classes_) == 2
        assert "a" in clf.classes_
        assert "b" in clf.classes_

    def test_predict_binary(self):
        """Test binary prediction."""
        X_train = [
            [1, 0],
            [0, 1],
            [1, 0],
            [0, 1],
        ]
        y_train = ["a", "b", "a", "b"]

        clf = LogisticRegressionClassifier(learning_rate=0.1, max_iter=100)
        clf.fit(X_train, y_train)

        predictions = clf.predict([[1, 0], [0, 1]])
        assert predictions[0] == "a"
        assert predictions[1] == "b"

    def test_fit_multiclass(self):
        """Test multiclass classification."""
        X = [
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1],
            [1, 0, 0],
        ]
        y = ["a", "b", "c", "a"]

        clf = LogisticRegressionClassifier(learning_rate=0.1, max_iter=100)
        clf.fit(X, y)

        assert len(clf.classes_) == 3

    def test_predict_multiclass(self):
        """Test multiclass prediction."""
        X_train = [
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1],
            [1, 0, 0],
        ]
        y_train = ["a", "b", "c", "a"]

        clf = LogisticRegressionClassifier(learning_rate=0.1, max_iter=100)
        clf.fit(X_train, y_train)

        predictions = clf.predict([[1, 0, 0]])
        assert predictions[0] in ["a", "b", "c"]

    def test_predict_proba(self):
        """Test probability prediction."""
        X_train = [
            [1, 0],
            [0, 1],
            [1, 0],
            [0, 1],
        ]
        y_train = ["a", "b", "a", "b"]

        clf = LogisticRegressionClassifier(learning_rate=0.1, max_iter=100)
        clf.fit(X_train, y_train)

        probas = clf.predict_proba([[1, 0]])
        assert len(probas) == 1
        assert "a" in probas[0]
        assert "b" in probas[0]
        assert abs(sum(probas[0].values()) - 1.0) < 1e-6

    def test_score(self):
        """Test accuracy scoring."""
        X_train = [
            [1, 0],
            [0, 1],
            [1, 0],
            [0, 1],
        ]
        y_train = ["a", "b", "a", "b"]

        clf = LogisticRegressionClassifier(learning_rate=0.1, max_iter=100)
        clf.fit(X_train, y_train)

        score = clf.score(X_train, y_train)
        assert score > 0.5  # Should be better than random

    def test_get_params(self):
        """Test getting parameters."""
        clf = LogisticRegressionClassifier(learning_rate=0.05, max_iter=500)
        params = clf.get_params()

        assert params["learning_rate"] == 0.05
        assert params["max_iter"] == 500

    def test_predict_before_fit(self):
        """Test that predict raises error before fit."""
        clf = LogisticRegressionClassifier()
        with pytest.raises(RuntimeError):
            clf.predict([[1, 0]])

    def test_convergence(self):
        """Test that training converges."""
        # Linearly separable data
        X = [[i, 0] for i in range(10)] + [[0, i] for i in range(10)]
        y = ["a"] * 10 + ["b"] * 10

        clf = LogisticRegressionClassifier(learning_rate=0.1, max_iter=1000)
        clf.fit(X, y)

        score = clf.score(X, y)
        assert score > 0.9  # Should converge to high accuracy


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
