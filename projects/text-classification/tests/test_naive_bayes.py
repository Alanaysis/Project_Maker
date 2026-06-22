"""
Tests for Naive Bayes Classifier.
"""

import math
import pytest
from src.naive_bayes import NaiveBayesClassifier


class TestNaiveBayesMultinomial:
    """Test suite for Multinomial Naive Bayes."""

    def test_basic_fit_predict(self):
        """Test basic fit and predict functionality."""
        # Simple binary classification
        X = [
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1],
            [1, 0, 0],
        ]
        y = ["a", "b", "c", "a"]

        clf = NaiveBayesClassifier(alpha=1.0)
        clf.fit(X, y)

        # Check that classifier learned
        assert len(clf.classes_) == 3
        assert "a" in clf.classes_
        assert "b" in clf.classes_
        assert "c" in clf.classes_

    def test_predict(self):
        """Test prediction on new data."""
        X_train = [
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1],
            [1, 0, 0],
            [0, 1, 0],
        ]
        y_train = ["a", "b", "c", "a", "b"]

        clf = NaiveBayesClassifier(alpha=1.0)
        clf.fit(X_train, y_train)

        # Test predictions
        X_test = [
            [1, 0, 0],  # Should be "a"
            [0, 1, 0],  # Should be "b"
            [0, 0, 1],  # Should be "c"
        ]
        predictions = clf.predict(X_test)

        assert len(predictions) == 3
        assert predictions[0] == "a"
        assert predictions[1] == "b"
        assert predictions[2] == "c"

    def test_predict_proba(self):
        """Test probability predictions."""
        X_train = [
            [1, 0],
            [0, 1],
            [1, 0],
            [0, 1],
        ]
        y_train = ["a", "b", "a", "b"]

        clf = NaiveBayesClassifier(alpha=1.0)
        clf.fit(X_train, y_train)

        X_test = [[1, 0]]
        probas = clf.predict_proba(X_test)

        assert len(probas) == 1
        assert "a" in probas[0]
        assert "b" in probas[0]

        # Probabilities should sum to 1
        total = sum(probas[0].values())
        assert abs(total - 1.0) < 1e-6

        # Class "a" should have higher probability
        assert probas[0]["a"] > probas[0]["b"]

    def test_score(self):
        """Test accuracy scoring."""
        X_train = [
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1],
            [1, 0, 0],
        ]
        y_train = ["a", "b", "c", "a"]

        clf = NaiveBayesClassifier(alpha=1.0)
        clf.fit(X_train, y_train)

        # Perfect predictions on training data
        score = clf.score(X_train, y_train)
        assert score == 1.0

    def test_laplace_smoothing(self):
        """Test Laplace smoothing (alpha=1.0)."""
        X_train = [
            [1, 0],
            [0, 1],
        ]
        y_train = ["a", "b"]

        # With alpha=1.0 (Laplace smoothing)
        clf = NaiveBayesClassifier(alpha=1.0)
        clf.fit(X_train, y_train)

        # Should still make predictions
        predictions = clf.predict([[1, 0]])
        assert predictions[0] == "a"

    def test_no_smoothing(self):
        """Test without smoothing (alpha=0)."""
        # Use data where all features have non-zero counts in each class
        X_train = [
            [1, 2],
            [2, 1],
        ]
        y_train = ["a", "b"]

        clf = NaiveBayesClassifier(alpha=0.0)
        clf.fit(X_train, y_train)

        predictions = clf.predict([[1, 2]])
        assert predictions[0] == "a"

    def test_class_priors(self):
        """Test that class priors are computed correctly."""
        X_train = [
            [1, 0],
            [1, 0],
            [0, 1],
        ]
        y_train = ["a", "a", "b"]

        clf = NaiveBayesClassifier(alpha=1.0)
        clf.fit(X_train, y_train)

        # P(a) = 2/3, P(b) = 1/3
        assert abs(clf.class_log_prior_["a"] - math.log(2 / 3)) < 1e-6
        assert abs(clf.class_log_prior_["b"] - math.log(1 / 3)) < 1e-6

    def test_feature_log_probs(self):
        """Test that feature log probabilities are computed."""
        X_train = [
            [2, 1],
            [1, 2],
        ]
        y_train = ["a", "b"]

        clf = NaiveBayesClassifier(alpha=1.0)
        clf.fit(X_train, y_train)

        # Should have feature log probs for each class
        assert "a" in clf.feature_log_prob_
        assert "b" in clf.feature_log_prob_
        assert len(clf.feature_log_prob_["a"]) == 2
        assert len(clf.feature_log_prob_["b"]) == 2

    def test_predict_before_fit(self):
        """Test that predict raises error before fit."""
        clf = NaiveBayesClassifier()

        with pytest.raises(RuntimeError, match="not been fitted"):
            clf.predict([[1, 0]])

    def test_predict_proba_before_fit(self):
        """Test that predict_proba raises error before fit."""
        clf = NaiveBayesClassifier()

        with pytest.raises(RuntimeError, match="not been fitted"):
            clf.predict_proba([[1, 0]])

    def test_multiple_features(self):
        """Test with multiple features."""
        X_train = [
            [1, 2, 3],
            [4, 5, 6],
            [7, 8, 9],
            [1, 2, 3],
        ]
        y_train = ["a", "b", "c", "a"]

        clf = NaiveBayesClassifier(alpha=1.0)
        clf.fit(X_train, y_train)

        predictions = clf.predict([[1, 2, 3]])
        assert predictions[0] == "a"

    def test_get_params(self):
        """Test getting parameters."""
        clf = NaiveBayesClassifier(alpha=0.5, model_type="multinomial")

        params = clf.get_params()
        assert params["alpha"] == 0.5
        assert params["model_type"] == "multinomial"

    def test_imbalanced_classes(self):
        """Test with imbalanced classes."""
        X_train = [
            [1, 0],
            [1, 0],
            [1, 0],
            [1, 0],
            [0, 1],
        ]
        y_train = ["a", "a", "a", "a", "b"]

        clf = NaiveBayesClassifier(alpha=1.0)
        clf.fit(X_train, y_train)

        # Class "a" should have higher prior
        assert clf.class_log_prior_["a"] > clf.class_log_prior_["b"]

    def test_zero_features(self):
        """Test with zero feature values."""
        X_train = [
            [0, 0, 1],
            [0, 1, 0],
            [1, 0, 0],
        ]
        y_train = ["a", "b", "c"]

        clf = NaiveBayesClassifier(alpha=1.0)
        clf.fit(X_train, y_train)

        predictions = clf.predict([[0, 0, 1]])
        assert predictions[0] == "a"


class TestNaiveBayesGaussian:
    """Test suite for Gaussian Naive Bayes."""

    def test_basic_fit_predict(self):
        """Test basic fit and predict functionality."""
        X_train = [
            [1.0, 2.0],
            [2.0, 3.0],
            [10.0, 11.0],
            [11.0, 12.0],
        ]
        y_train = ["a", "a", "b", "b"]

        clf = NaiveBayesClassifier(model_type="gaussian")
        clf.fit(X_train, y_train)

        assert len(clf.classes_) == 2

    def test_predict(self):
        """Test prediction on new data."""
        X_train = [
            [1.0, 2.0],
            [1.5, 2.5],
            [10.0, 11.0],
            [10.5, 11.5],
        ]
        y_train = ["a", "a", "b", "b"]

        clf = NaiveBayesClassifier(model_type="gaussian")
        clf.fit(X_train, y_train)

        X_test = [
            [1.0, 2.0],  # Close to class "a"
            [10.0, 11.0],  # Close to class "b"
        ]
        predictions = clf.predict(X_test)

        assert predictions[0] == "a"
        assert predictions[1] == "b"

    def test_predict_proba(self):
        """Test probability predictions."""
        X_train = [
            [1.0, 2.0],
            [1.5, 2.5],
            [10.0, 11.0],
            [10.5, 11.5],
        ]
        y_train = ["a", "a", "b", "b"]

        clf = NaiveBayesClassifier(model_type="gaussian")
        clf.fit(X_train, y_train)

        probas = clf.predict_proba([[1.0, 2.0]])

        assert len(probas) == 1
        assert "a" in probas[0]
        assert "b" in probas[0]

        # Probabilities should sum to 1
        total = sum(probas[0].values())
        assert abs(total - 1.0) < 1e-6

    def test_gaussian_parameters(self):
        """Test that Gaussian parameters (mean, variance) are computed."""
        X_train = [
            [1.0, 2.0],
            [3.0, 4.0],
        ]
        y_train = ["a", "a"]

        clf = NaiveBayesClassifier(model_type="gaussian")
        clf.fit(X_train, y_train)

        # Mean should be [2.0, 3.0]
        assert abs(clf.theta_["a"][0] - 2.0) < 1e-6
        assert abs(clf.theta_["a"][1] - 3.0) < 1e-6

        # Variance should be [1.0, 1.0]
        assert abs(clf.sigma_["a"][0] - 1.0) < 1e-6
        assert abs(clf.sigma_["a"][1] - 1.0) < 1e-6

    def test_score(self):
        """Test accuracy scoring."""
        X_train = [
            [1.0, 2.0],
            [1.5, 2.5],
            [10.0, 11.0],
            [10.5, 11.5],
        ]
        y_train = ["a", "a", "b", "b"]

        clf = NaiveBayesClassifier(model_type="gaussian")
        clf.fit(X_train, y_train)

        score = clf.score(X_train, y_train)
        assert score == 1.0

    def test_unknown_model_type(self):
        """Test that unknown model type raises error."""
        clf = NaiveBayesClassifier(model_type="unknown")

        with pytest.raises(ValueError, match="Unknown model_type"):
            clf.fit([[1, 0]], ["a"])


class TestNaiveBayesEdgeCases:
    """Test edge cases for Naive Bayes."""

    def test_single_class(self):
        """Test with single class."""
        X_train = [
            [1, 0],
            [0, 1],
        ]
        y_train = ["a", "a"]

        clf = NaiveBayesClassifier(alpha=1.0)
        clf.fit(X_train, y_train)

        predictions = clf.predict([[1, 0]])
        assert predictions[0] == "a"

    def test_single_sample_per_class(self):
        """Test with single sample per class."""
        X_train = [
            [1, 0],
            [0, 1],
        ]
        y_train = ["a", "b"]

        clf = NaiveBayesClassifier(alpha=1.0)
        clf.fit(X_train, y_train)

        predictions = clf.predict([[1, 0]])
        assert predictions[0] == "a"

    def test_large_feature_values(self):
        """Test with large feature values."""
        X_train = [
            [1000, 2000],
            [3000, 4000],
        ]
        y_train = ["a", "b"]

        clf = NaiveBayesClassifier(alpha=1.0)
        clf.fit(X_train, y_train)

        predictions = clf.predict([[1000, 2000]])
        assert predictions[0] == "a"

    def test_many_classes(self):
        """Test with many classes."""
        X_train = [[i, i * 2] for i in range(10)]
        y_train = [f"class_{i}" for i in range(10)]

        clf = NaiveBayesClassifier(alpha=1.0)
        clf.fit(X_train, y_train)

        assert len(clf.classes_) == 10

    def test_sparse_features(self):
        """Test with sparse-like features (many zeros)."""
        X_train = [
            [1, 0, 0, 0, 0],
            [0, 0, 0, 0, 1],
        ]
        y_train = ["a", "b"]

        clf = NaiveBayesClassifier(alpha=1.0)
        clf.fit(X_train, y_train)

        predictions = clf.predict([[1, 0, 0, 0, 0]])
        assert predictions[0] == "a"

    def test_equal_features(self):
        """Test when both classes have similar features."""
        X_train = [
            [1, 1],
            [1, 1],
            [1, 1],
            [1, 1],
        ]
        y_train = ["a", "a", "b", "b"]

        clf = NaiveBayesClassifier(alpha=1.0)
        clf.fit(X_train, y_train)

        # With identical features, prior probabilities determine prediction
        predictions = clf.predict([[1, 1]])
        assert predictions[0] in ["a", "b"]

    def test_probability_distribution(self):
        """Test that probability distribution is valid."""
        X_train = [
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1],
        ]
        y_train = ["a", "b", "c"]

        clf = NaiveBayesClassifier(alpha=1.0)
        clf.fit(X_train, y_train)

        probas = clf.predict_proba([[1, 0, 0]])

        # Check probability distribution
        for prob_dict in probas:
            assert all(0 <= p <= 1 for p in prob_dict.values())
            assert abs(sum(prob_dict.values()) - 1.0) < 1e-6
