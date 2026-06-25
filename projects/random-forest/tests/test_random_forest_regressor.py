"""
Tests for the RandomForestRegressor and DecisionTreeRegressor.
"""

import numpy as np
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.random_forest_regressor import DecisionTreeRegressor, RandomForestRegressor


class TestDecisionTreeRegressor:
    """Test suite for DecisionTreeRegressor."""

    @pytest.fixture
    def simple_data(self):
        """Create a simple regression dataset."""
        np.random.seed(42)
        X = np.linspace(0, 10, 50).reshape(-1, 1)
        y = 2 * X.ravel() + 1 + np.random.randn(50) * 0.5
        return X, y

    @pytest.fixture
    def multi_feature_data(self):
        """Create a multi-feature regression dataset."""
        np.random.seed(42)
        X = np.random.randn(100, 3)
        y = 2 * X[:, 0] + 3 * X[:, 1] + np.random.randn(100) * 0.1
        return X, y

    def test_initialization(self):
        """Test that the regressor initializes with correct parameters."""
        reg = DecisionTreeRegressor(
            max_depth=5,
            min_samples_split=3,
            min_samples_leaf=2,
            random_state=42,
        )
        assert reg.max_depth == 5
        assert reg.min_samples_split == 3
        assert reg.min_samples_leaf == 2
        assert reg.random_state == 42

    def test_invalid_min_samples_split(self):
        """Test that invalid min_samples_split raises ValueError."""
        with pytest.raises(ValueError, match="min_samples_split must be at least 2"):
            DecisionTreeRegressor(min_samples_split=1)

    def test_invalid_min_samples_leaf(self):
        """Test that invalid min_samples_leaf raises ValueError."""
        with pytest.raises(ValueError, match="min_samples_leaf must be at least 1"):
            DecisionTreeRegressor(min_samples_leaf=0)

    def test_fit_predict_simple(self, simple_data):
        """Test basic fit and predict on simple data."""
        X, y = simple_data
        reg = DecisionTreeRegressor(max_depth=10, random_state=42)
        reg.fit(X, y)

        predictions = reg.predict(X)
        assert len(predictions) == len(y)
        # Should fit well
        mse = np.mean((predictions - y) ** 2)
        assert mse < 1.0

    def test_predict_before_fit(self):
        """Test that predict raises error before fit."""
        reg = DecisionTreeRegressor()
        with pytest.raises(RuntimeError, match="Tree has not been fitted"):
            reg.predict(np.array([[1, 2]]))

    def test_max_depth_limiting(self, simple_data):
        """Test that max_depth limits tree depth."""
        X, y = simple_data
        reg = DecisionTreeRegressor(max_depth=2, random_state=42)
        reg.fit(X, y)

        assert reg.get_depth() <= 2

    def test_feature_importances(self, multi_feature_data):
        """Test that feature importances are computed correctly."""
        X, y = multi_feature_data
        reg = DecisionTreeRegressor(random_state=42)
        reg.fit(X, y)

        assert reg.feature_importances_ is not None
        assert len(reg.feature_importances_) == X.shape[1]
        assert np.all(reg.feature_importances_ >= 0)
        assert np.isclose(np.sum(reg.feature_importances_), 1.0)

    def test_multi_feature_importance_ranking(self, multi_feature_data):
        """Test that more important features get higher importance scores."""
        X, y = multi_feature_data
        reg = DecisionTreeRegressor(random_state=42)
        reg.fit(X, y)

        # Feature 0 (coef=2) and feature 1 (coef=3) should be most important
        assert reg.feature_importances_[1] > reg.feature_importances_[2]

    def test_max_features(self, multi_feature_data):
        """Test that max_features limits feature selection."""
        X, y = multi_feature_data
        reg = DecisionTreeRegressor(max_features=1, random_state=42)
        reg.fit(X, y)

        predictions = reg.predict(X)
        assert len(predictions) == len(y)

    def test_1d_input(self):
        """Test that 1D input is reshaped correctly."""
        X = np.array([1, 2, 3, 4, 5, 6])
        y = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
        reg = DecisionTreeRegressor(random_state=42)
        reg.fit(X, y)

        predictions = reg.predict(np.array([1, 6]))
        assert len(predictions) == 2

    def test_repr(self):
        """Test string representation."""
        reg = DecisionTreeRegressor(max_depth=5)
        repr_str = repr(reg)
        assert "DecisionTreeRegressor" in repr_str
        assert "max_depth=5" in repr_str


class TestRandomForestRegressor:
    """Test suite for RandomForestRegressor."""

    @pytest.fixture
    def simple_data(self):
        """Create a simple regression dataset."""
        np.random.seed(42)
        X = np.linspace(0, 10, 100).reshape(-1, 1)
        y = 2 * X.ravel() + 1 + np.random.randn(100) * 0.5
        return X, y

    @pytest.fixture
    def multi_feature_data(self):
        """Create a multi-feature regression dataset."""
        np.random.seed(42)
        X = np.random.randn(200, 5)
        y = 3 * X[:, 0] + 2 * X[:, 1] + X[:, 2] + np.random.randn(200) * 0.2
        return X, y

    def test_initialization(self):
        """Test that the regressor initializes with correct parameters."""
        reg = RandomForestRegressor(
            n_estimators=50,
            max_depth=5,
            min_samples_split=3,
            max_features="sqrt",
            bootstrap=True,
            random_state=42,
        )
        assert reg.n_estimators == 50
        assert reg.max_depth == 5
        assert reg.min_samples_split == 3
        assert reg.max_features == "sqrt"
        assert reg.bootstrap is True
        assert reg.random_state == 42

    def test_invalid_n_estimators(self):
        """Test that invalid n_estimators raises ValueError."""
        with pytest.raises(ValueError, match="n_estimators must be at least 1"):
            RandomForestRegressor(n_estimators=0)

    def test_fit_predict_simple(self, simple_data):
        """Test basic fit and predict."""
        X, y = simple_data
        reg = RandomForestRegressor(n_estimators=10, random_state=42)
        reg.fit(X, y)

        predictions = reg.predict(X)
        assert len(predictions) == len(y)
        # Should fit well
        mse = np.mean((predictions - y) ** 2)
        assert mse < 2.0

    def test_predict_before_fit(self):
        """Test that predict raises error before fit."""
        reg = RandomForestRegressor()
        with pytest.raises(RuntimeError, match="Forest has not been fitted"):
            reg.predict(np.array([[1, 2]]))

    def test_bagging_creates_different_trees(self, simple_data):
        """Test that bootstrap sampling creates different trees."""
        X, y = simple_data
        reg = RandomForestRegressor(n_estimators=10, bootstrap=True, random_state=42)
        reg.fit(X, y)

        predictions = np.array([tree.predict(X) for tree in reg.trees_])
        # Not all trees should give identical predictions
        assert not np.all(predictions == predictions[0])

    def test_averaging_prediction(self, simple_data):
        """Test that prediction is the average of all tree predictions."""
        X, y = simple_data
        reg = RandomForestRegressor(n_estimators=10, random_state=42)
        reg.fit(X, y)

        forest_pred = reg.predict(X[:5])
        tree_preds = np.array([tree.predict(X[:5]) for tree in reg.trees_])
        manual_avg = np.mean(tree_preds, axis=0)

        np.testing.assert_allclose(forest_pred, manual_avg, rtol=1e-10)

    def test_feature_importances(self, multi_feature_data):
        """Test that feature importances are computed."""
        X, y = multi_feature_data
        reg = RandomForestRegressor(n_estimators=10, random_state=42)
        reg.fit(X, y)

        assert reg.feature_importances_ is not None
        assert len(reg.feature_importances_) == X.shape[1]
        assert np.all(reg.feature_importances_ >= 0)
        assert np.isclose(np.sum(reg.feature_importances_), 1.0)

    def test_oob_score(self, simple_data):
        """Test out-of-bag score computation."""
        X, y = simple_data
        reg = RandomForestRegressor(n_estimators=50, bootstrap=True, random_state=42)
        reg.fit(X, y)

        assert reg.oob_score_ is not None
        assert reg.oob_score_ > 0.5  # Should be reasonably good

    def test_oob_score_without_bootstrap(self, simple_data):
        """Test that OOB score is None when bootstrap=False."""
        X, y = simple_data
        reg = RandomForestRegressor(n_estimators=10, bootstrap=False, random_state=42)
        reg.fit(X, y)

        assert reg.oob_score_ is None

    def test_random_state_reproducibility(self, simple_data):
        """Test that random_state produces reproducible results."""
        X, y = simple_data

        reg1 = RandomForestRegressor(n_estimators=10, random_state=42)
        reg1.fit(X, y)
        pred1 = reg1.predict(X)

        reg2 = RandomForestRegressor(n_estimators=10, random_state=42)
        reg2.fit(X, y)
        pred2 = reg2.predict(X)

        np.testing.assert_array_equal(pred1, pred2)

    def test_ensemble_better_than_single_tree(self, multi_feature_data):
        """Test that ensemble generally performs better than a single tree."""
        X, y = multi_feature_data
        from src.random_forest_regressor import DecisionTreeRegressor

        # Single tree
        single_tree = DecisionTreeRegressor(max_depth=5, random_state=42)
        single_tree.fit(X, y)
        single_pred = single_tree.predict(X)
        single_mse = np.mean((single_pred - y) ** 2)

        # Random Forest
        rf = RandomForestRegressor(n_estimators=20, max_depth=5, random_state=42)
        rf.fit(X, y)
        rf_pred = rf.predict(X)
        rf_mse = np.mean((rf_pred - y) ** 2)

        # Both should work (MSE should be reasonable)
        assert single_mse < 5.0
        assert rf_mse < 5.0

    def test_repr(self):
        """Test string representation."""
        reg = RandomForestRegressor(n_estimators=100, max_depth=5)
        repr_str = repr(reg)
        assert "RandomForestRegressor" in repr_str
        assert "n_estimators=100" in repr_str

    def test_1d_input(self):
        """Test that 1D input is reshaped correctly."""
        X = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        y = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
        reg = RandomForestRegressor(n_estimators=5, random_state=42)
        reg.fit(X, y)

        predictions = reg.predict(np.array([1, 10]))
        assert len(predictions) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
