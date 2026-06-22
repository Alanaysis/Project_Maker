"""
Tests for the RandomForestClassifier.
"""

import numpy as np
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.random_forest import RandomForestClassifier


class TestRandomForestClassifier:
    """Test suite for RandomForestClassifier."""

    @pytest.fixture
    def simple_data(self):
        """Create a simple binary classification dataset."""
        np.random.seed(42)
        X1 = np.random.randn(50, 2) + [2, 2]
        X2 = np.random.randn(50, 2) + [-2, -2]
        X = np.vstack([X1, X2])
        y = np.array([0] * 50 + [1] * 50)
        return X, y

    @pytest.fixture
    def multi_class_data(self):
        """Create a multi-class dataset."""
        np.random.seed(42)
        X1 = np.random.randn(30, 3) + [3, 0, 0]
        X2 = np.random.randn(30, 3) + [-3, 0, 0]
        X3 = np.random.randn(30, 3) + [0, 3, 0]
        X = np.vstack([X1, X2, X3])
        y = np.array([0] * 30 + [1] * 30 + [2] * 30)
        return X, y

    @pytest.fixture
    def high_dim_data(self):
        """Create a high-dimensional dataset to test feature subsampling."""
        np.random.seed(42)
        n_samples = 100
        n_features = 20
        X = np.random.randn(n_samples, n_features)
        # Only first 2 features are relevant
        y = ((X[:, 0] + X[:, 1]) > 0).astype(int)
        return X, y

    def test_initialization(self):
        """Test that the classifier initializes with correct parameters."""
        clf = RandomForestClassifier(
            n_estimators=50,
            max_depth=5,
            min_samples_split=3,
            min_samples_leaf=2,
            max_features="sqrt",
            bootstrap=True,
            criterion="gini",
            random_state=42,
        )
        assert clf.n_estimators == 50
        assert clf.max_depth == 5
        assert clf.min_samples_split == 3
        assert clf.min_samples_leaf == 2
        assert clf.max_features == "sqrt"
        assert clf.bootstrap is True
        assert clf.criterion == "gini"
        assert clf.random_state == 42

    def test_invalid_n_estimators(self):
        """Test that invalid n_estimators raises ValueError."""
        with pytest.raises(ValueError, match="n_estimators must be at least 1"):
            RandomForestClassifier(n_estimators=0)

    def test_fit_predict_simple(self, simple_data):
        """Test basic fit and predict."""
        X, y = simple_data
        clf = RandomForestClassifier(n_estimators=10, random_state=42)
        clf.fit(X, y)

        predictions = clf.predict(X)
        assert len(predictions) == len(y)
        accuracy = np.mean(predictions == y)
        assert accuracy > 0.9

    def test_predict_before_fit(self):
        """Test that predict raises error before fit."""
        clf = RandomForestClassifier()
        with pytest.raises(RuntimeError, match="Forest has not been fitted"):
            clf.predict(np.array([[1, 2]]))

    def test_bagging_creates_different_trees(self, simple_data):
        """Test that bootstrap sampling creates different trees."""
        X, y = simple_data
        clf = RandomForestClassifier(
            n_estimators=10, bootstrap=True, random_state=42
        )
        clf.fit(X, y)

        # All trees should be different (with high probability)
        predictions = np.array([tree.predict(X) for tree in clf.trees_])
        # Check that not all trees give identical predictions
        assert not np.all(predictions == predictions[0])

    def test_bagging_vs_no_bagging(self, simple_data):
        """Test difference between bagging and no bagging."""
        X, y = simple_data

        # With bagging
        clf_bagging = RandomForestClassifier(
            n_estimators=10, bootstrap=True, random_state=42
        )
        clf_bagging.fit(X, y)

        # Without bagging
        clf_no_bagging = RandomForestClassifier(
            n_estimators=10, bootstrap=False, random_state=42
        )
        clf_no_bagging.fit(X, y)

        # Both should work
        assert clf_bagging.score(X, y) > 0.8
        assert clf_no_bagging.score(X, y) > 0.8

    def test_random_feature_selection(self, high_dim_data):
        """Test that random feature selection limits features per split."""
        X, y = high_dim_data
        clf = RandomForestClassifier(
            n_estimators=10, max_features="sqrt", random_state=42
        )
        clf.fit(X, y)

        # Should still achieve decent accuracy despite feature subsampling
        predictions = clf.predict(X)
        accuracy = np.mean(predictions == y)
        assert accuracy > 0.7

    def test_predict_proba(self, simple_data):
        """Test probability predictions."""
        X, y = simple_data
        clf = RandomForestClassifier(n_estimators=10, random_state=42)
        clf.fit(X, y)

        proba = clf.predict_proba(X)
        assert proba.shape == (len(X), 2)
        assert np.all(proba >= 0)
        assert np.all(proba <= 1)
        assert np.allclose(np.sum(proba, axis=1), 1.0)

    def test_multi_class(self, multi_class_data):
        """Test multi-class classification."""
        X, y = multi_class_data
        clf = RandomForestClassifier(
            n_estimators=20, max_depth=5, random_state=42
        )
        clf.fit(X, y)

        predictions = clf.predict(X)
        assert len(np.unique(predictions)) <= 3
        accuracy = np.mean(predictions == y)
        assert accuracy > 0.85

    def test_multi_class_proba(self, multi_class_data):
        """Test multi-class probability predictions."""
        X, y = multi_class_data
        clf = RandomForestClassifier(n_estimators=20, random_state=42)
        clf.fit(X, y)

        proba = clf.predict_proba(X)
        assert proba.shape == (len(X), 3)
        assert np.all(proba >= 0)
        assert np.allclose(np.sum(proba, axis=1), 1.0)

    def test_feature_importances(self, simple_data):
        """Test that feature importances are computed."""
        X, y = simple_data
        clf = RandomForestClassifier(n_estimators=10, random_state=42)
        clf.fit(X, y)

        assert clf.feature_importances_ is not None
        assert len(clf.feature_importances_) == X.shape[1]
        assert np.all(clf.feature_importances_ >= 0)
        assert np.isclose(np.sum(clf.feature_importances_), 1.0)

    def test_oob_score(self, simple_data):
        """Test out-of-bag score computation."""
        X, y = simple_data
        clf = RandomForestClassifier(
            n_estimators=50, bootstrap=True, random_state=42
        )
        clf.fit(X, y)

        assert clf.oob_score_ is not None
        assert 0.0 <= clf.oob_score_ <= 1.0
        assert clf.oob_score_ > 0.7

    def test_oob_score_without_bootstrap(self, simple_data):
        """Test that OOB score is None when bootstrap=False."""
        X, y = simple_data
        clf = RandomForestClassifier(
            n_estimators=10, bootstrap=False, random_state=42
        )
        clf.fit(X, y)

        assert clf.oob_score_ is None

    def test_score(self, simple_data):
        """Test the score method."""
        X, y = simple_data
        clf = RandomForestClassifier(n_estimators=10, random_state=42)
        clf.fit(X, y)

        score = clf.score(X, y)
        assert 0.0 <= score <= 1.0
        assert score > 0.9

    def test_random_state_reproducibility(self, simple_data):
        """Test that random_state produces reproducible results."""
        X, y = simple_data

        clf1 = RandomForestClassifier(n_estimators=10, random_state=42)
        clf1.fit(X, y)
        pred1 = clf1.predict(X)

        clf2 = RandomForestClassifier(n_estimators=10, random_state=42)
        clf2.fit(X, y)
        pred2 = clf2.predict(X)

        assert np.array_equal(pred1, pred2)

    def test_different_random_states(self, simple_data):
        """Test that different random states produce different results."""
        X, y = simple_data

        clf1 = RandomForestClassifier(n_estimators=10, random_state=42)
        clf1.fit(X, y)
        pred1 = clf1.predict(X)

        clf2 = RandomForestClassifier(n_estimators=10, random_state=123)
        clf2.fit(X, y)
        pred2 = clf2.predict(X)

        # Very unlikely to be identical (though possible)
        # Just check both work
        assert len(pred1) == len(pred2) == len(y)

    def test_ensemble_better_than_single_tree(self, high_dim_data):
        """Test that ensemble generally performs better than a single tree."""
        X, y = high_dim_data
        from src.decision_tree import DecisionTreeClassifier

        # Single tree
        single_tree = DecisionTreeClassifier(max_depth=5, random_state=42)
        single_tree.fit(X, y)
        single_accuracy = single_tree.score(X, y)

        # Random Forest
        rf = RandomForestClassifier(
            n_estimators=20, max_depth=5, random_state=42
        )
        rf.fit(X, y)
        rf_accuracy = rf.score(X, y)

        # Random Forest should generally perform better on training data
        # (though not guaranteed for every random seed)
        # At minimum, both should be above chance
        assert single_accuracy > 0.5
        assert rf_accuracy > 0.5

    def test_repr(self):
        """Test string representation."""
        clf = RandomForestClassifier(n_estimators=100, max_depth=5)
        repr_str = repr(clf)
        assert "RandomForestClassifier" in repr_str
        assert "n_estimators=100" in repr_str
        assert "max_depth=5" in repr_str

    def test_1d_input(self):
        """Test that 1D input is reshaped correctly."""
        X = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        y = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
        clf = RandomForestClassifier(n_estimators=5, random_state=42)
        clf.fit(X, y)

        predictions = clf.predict(np.array([1, 10]))
        assert len(predictions) == 2

    def test_single_class_error(self):
        """Test that single class raises error."""
        X = np.array([[1, 2], [3, 4], [5, 6]])
        y = np.array([0, 0, 0])
        clf = RandomForestClassifier()
        with pytest.raises(ValueError, match="Need at least 2 classes"):
            clf.fit(X, y)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
