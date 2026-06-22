"""
Tests for the DecisionTreeClassifier.
"""

import numpy as np
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.decision_tree import DecisionTreeClassifier, Node


class TestDecisionTreeClassifier:
    """Test suite for DecisionTreeClassifier."""

    @pytest.fixture
    def simple_data(self):
        """Create a simple binary classification dataset."""
        # XOR-like problem
        X = np.array([
            [0, 0],
            [0, 1],
            [1, 0],
            [1, 1],
        ])
        y = np.array([0, 1, 1, 0])
        return X, y

    @pytest.fixture
    def linear_separable_data(self):
        """Create a linearly separable dataset."""
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
        X1 = np.random.randn(30, 2) + [3, 0]
        X2 = np.random.randn(30, 2) + [-3, 0]
        X3 = np.random.randn(30, 2) + [0, 3]
        X = np.vstack([X1, X2, X3])
        y = np.array([0] * 30 + [1] * 30 + [2] * 30)
        return X, y

    def test_initialization(self):
        """Test that the classifier initializes with correct parameters."""
        clf = DecisionTreeClassifier(
            max_depth=5,
            min_samples_split=3,
            min_samples_leaf=2,
            criterion="gini",
            random_state=42,
        )
        assert clf.max_depth == 5
        assert clf.min_samples_split == 3
        assert clf.min_samples_leaf == 2
        assert clf.criterion == "gini"
        assert clf.random_state == 42

    def test_invalid_criterion(self):
        """Test that invalid criterion raises ValueError."""
        with pytest.raises(ValueError, match="Criterion must be one of"):
            DecisionTreeClassifier(criterion="invalid")

    def test_invalid_min_samples_split(self):
        """Test that invalid min_samples_split raises ValueError."""
        with pytest.raises(ValueError, match="min_samples_split must be at least 2"):
            DecisionTreeClassifier(min_samples_split=1)

    def test_invalid_min_samples_leaf(self):
        """Test that invalid min_samples_leaf raises ValueError."""
        with pytest.raises(ValueError, match="min_samples_leaf must be at least 1"):
            DecisionTreeClassifier(min_samples_leaf=0)

    def test_fit_predict_simple(self, simple_data):
        """Test basic fit and predict on simple data."""
        X, y = simple_data
        clf = DecisionTreeClassifier(max_depth=10, random_state=42)
        clf.fit(X, y)

        predictions = clf.predict(X)
        assert len(predictions) == len(y)
        # Should perfectly fit this data
        assert np.array_equal(predictions, y)

    def test_fit_predict_linear(self, linear_separable_data):
        """Test fit and predict on linearly separable data."""
        X, y = linear_separable_data
        clf = DecisionTreeClassifier(max_depth=5, random_state=42)
        clf.fit(X, y)

        predictions = clf.predict(X)
        assert len(predictions) == len(y)
        # Should achieve high accuracy
        accuracy = np.mean(predictions == y)
        assert accuracy > 0.95

    def test_predict_before_fit(self):
        """Test that predict raises error before fit."""
        clf = DecisionTreeClassifier()
        with pytest.raises(RuntimeError, match="Tree has not been fitted"):
            clf.predict(np.array([[1, 2]]))

    def test_max_depth_limiting(self, linear_separable_data):
        """Test that max_depth limits tree depth."""
        X, y = linear_separable_data
        clf = DecisionTreeClassifier(max_depth=2, random_state=42)
        clf.fit(X, y)

        assert clf.get_depth() <= 2

    def test_min_samples_split(self, linear_separable_data):
        """Test that min_samples_split prevents splitting small nodes."""
        X, y = linear_separable_data
        clf = DecisionTreeClassifier(
            max_depth=10, min_samples_split=50, random_state=42
        )
        clf.fit(X, y)

        # With high min_samples_split, tree should be shallow
        assert clf.get_depth() < 5

    def test_min_samples_leaf(self, linear_separable_data):
        """Test that min_samples_leaf creates proper leaf sizes."""
        X, y = linear_separable_data
        clf = DecisionTreeClassifier(
            max_depth=10, min_samples_leaf=10, random_state=42
        )
        clf.fit(X, y)

        # Tree should have fewer leaves with larger min_samples_leaf
        assert clf.get_n_leaves() < 50

    def test_gini_criterion(self, linear_separable_data):
        """Test Gini impurity criterion."""
        X, y = linear_separable_data
        clf = DecisionTreeClassifier(criterion="gini", random_state=42)
        clf.fit(X, y)

        predictions = clf.predict(X)
        accuracy = np.mean(predictions == y)
        assert accuracy > 0.95

    def test_entropy_criterion(self, linear_separable_data):
        """Test entropy criterion."""
        X, y = linear_separable_data
        clf = DecisionTreeClassifier(criterion="entropy", random_state=42)
        clf.fit(X, y)

        predictions = clf.predict(X)
        accuracy = np.mean(predictions == y)
        assert accuracy > 0.95

    def test_multi_class(self, multi_class_data):
        """Test multi-class classification."""
        X, y = multi_class_data
        clf = DecisionTreeClassifier(max_depth=5, random_state=42)
        clf.fit(X, y)

        predictions = clf.predict(X)
        assert len(np.unique(predictions)) <= 3
        accuracy = np.mean(predictions == y)
        assert accuracy > 0.9

    def test_feature_importances(self, linear_separable_data):
        """Test that feature importances are computed correctly."""
        X, y = linear_separable_data
        clf = DecisionTreeClassifier(random_state=42)
        clf.fit(X, y)

        assert clf.feature_importances_ is not None
        assert len(clf.feature_importances_) == X.shape[1]
        assert np.all(clf.feature_importances_ >= 0)
        assert np.isclose(np.sum(clf.feature_importances_), 1.0)

    def test_max_features(self, linear_separable_data):
        """Test that max_features limits feature selection."""
        X, y = linear_separable_data
        clf = DecisionTreeClassifier(max_features=1, random_state=42)
        clf.fit(X, y)

        predictions = clf.predict(X)
        assert len(predictions) == len(y)

    def test_score(self, linear_separable_data):
        """Test the score method."""
        X, y = linear_separable_data
        clf = DecisionTreeClassifier(random_state=42)
        clf.fit(X, y)

        score = clf.score(X, y)
        assert 0.0 <= score <= 1.0
        assert score > 0.95

    def test_repr(self):
        """Test string representation."""
        clf = DecisionTreeClassifier(max_depth=5, criterion="gini")
        repr_str = repr(clf)
        assert "DecisionTreeClassifier" in repr_str
        assert "max_depth=5" in repr_str
        assert "gini" in repr_str

    def test_1d_input(self):
        """Test that 1D input is reshaped correctly."""
        X = np.array([1, 2, 3, 4, 5, 6])
        y = np.array([0, 0, 0, 1, 1, 1])
        clf = DecisionTreeClassifier(random_state=42)
        clf.fit(X, y)

        predictions = clf.predict(np.array([1, 6]))
        assert len(predictions) == 2

    def test_single_class_error(self):
        """Test that single class raises error."""
        X = np.array([[1, 2], [3, 4]])
        y = np.array([0, 0])
        clf = DecisionTreeClassifier()
        with pytest.raises(ValueError, match="Need at least 2 classes"):
            clf.fit(X, y)


class TestNode:
    """Test suite for the Node class."""

    def test_leaf_node(self):
        """Test leaf node creation."""
        node = Node(value=0, samples=10, impurity=0.0)
        assert node.is_leaf is True
        assert node.value == 0
        assert node.samples == 10

    def test_internal_node(self):
        """Test internal node creation."""
        left = Node(value=0, samples=5)
        right = Node(value=1, samples=5)
        node = Node(
            feature_index=0,
            threshold=0.5,
            left=left,
            right=right,
            samples=10,
            impurity=0.5,
        )
        assert node.is_leaf is False
        assert node.feature_index == 0
        assert node.threshold == 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
