"""
Tests for SVM Classifier.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.svm_classifier import SVMClassifier


class TestSVMClassifier:
    """Test SVMClassifier functionality."""

    def test_init(self):
        """Test classifier initialization."""
        clf = SVMClassifier()
        assert clf.C == 1.0
        assert clf.max_iter == 1000
        assert clf.learning_rate == 0.01

    def test_fit_binary(self):
        """Test binary classification."""
        X = [
            [1, 0],
            [0, 1],
            [1, 0],
            [0, 1],
        ]
        y = ["a", "b", "a", "b"]

        clf = SVMClassifier(C=1.0, max_iter=100)
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

        clf = SVMClassifier(C=1.0, max_iter=100)
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

        clf = SVMClassifier(C=1.0, max_iter=100)
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

        clf = SVMClassifier(C=1.0, max_iter=100)
        clf.fit(X_train, y_train)

        predictions = clf.predict([[1, 0, 0]])
        assert predictions[0] in ["a", "b", "c"]

    def test_decision_function(self):
        """Test decision function."""
        X_train = [
            [1, 0],
            [0, 1],
            [1, 0],
            [0, 1],
        ]
        y_train = ["a", "b", "a", "b"]

        clf = SVMClassifier(C=1.0, max_iter=100)
        clf.fit(X_train, y_train)

        scores = clf.decision_function([1, 0])
        assert isinstance(scores, dict)
        assert "a" in scores
        assert "b" in scores

    def test_predict_proba(self):
        """Test probability prediction."""
        X_train = [
            [1, 0],
            [0, 1],
            [1, 0],
            [0, 1],
        ]
        y_train = ["a", "b", "a", "b"]

        clf = SVMClassifier(C=1.0, max_iter=100)
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

        clf = SVMClassifier(C=1.0, max_iter=100)
        clf.fit(X_train, y_train)

        score = clf.score(X_train, y_train)
        assert score > 0.5

    def test_get_params(self):
        """Test getting parameters."""
        clf = SVMClassifier(C=0.5, max_iter=500)
        params = clf.get_params()

        assert params["C"] == 0.5
        assert params["max_iter"] == 500

    def test_predict_before_fit(self):
        """Test that predict raises error before fit."""
        clf = SVMClassifier()
        with pytest.raises(RuntimeError):
            clf.predict([[1, 0]])

    def test_linearly_separable(self):
        """Test on linearly separable data."""
        # Create clearly separated data
        X = [[i, 0] for i in range(1, 11)] + [[0, i] for i in range(1, 11)]
        y = ["a"] * 10 + ["b"] * 10

        clf = SVMClassifier(C=1.0, max_iter=500)
        clf.fit(X, y)

        score = clf.score(X, y)
        assert score > 0.8


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
