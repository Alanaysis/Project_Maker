"""
Tests for the evaluation metrics module.
"""

import numpy as np
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.evaluation import (
    accuracy,
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    mean_squared_error,
    root_mean_squared_error,
    mean_absolute_error,
    r2_score,
    permutation_importance,
    train_test_split,
)


# =============================================================================
# Classification Metrics Tests
# =============================================================================


class TestAccuracy:
    """Test suite for the accuracy function."""

    def test_perfect_accuracy(self):
        y_true = np.array([0, 1, 2, 0, 1])
        y_pred = np.array([0, 1, 2, 0, 1])
        assert accuracy(y_true, y_pred) == 1.0

    def test_zero_accuracy(self):
        y_true = np.array([0, 0, 0])
        y_pred = np.array([1, 1, 1])
        assert accuracy(y_true, y_pred) == 0.0

    def test_partial_accuracy(self):
        y_true = np.array([0, 1, 0, 1])
        y_pred = np.array([0, 0, 0, 1])
        assert accuracy(y_true, y_pred) == 0.75

    def test_binary_classification(self):
        y_true = np.array([0, 1, 1, 0, 1, 1, 0, 0])
        y_pred = np.array([0, 1, 0, 0, 1, 1, 1, 0])
        assert accuracy(y_true, y_pred) == 0.75


class TestConfusionMatrix:
    """Test suite for the confusion_matrix function."""

    def test_binary_confusion_matrix(self):
        y_true = np.array([0, 0, 1, 1])
        y_pred = np.array([0, 1, 0, 1])
        cm = confusion_matrix(y_true, y_pred)
        assert cm.shape == (2, 2)
        assert cm[0, 0] == 1  # TN
        assert cm[0, 1] == 1  # FP
        assert cm[1, 0] == 1  # FN
        assert cm[1, 1] == 1  # TP

    def test_perfect_predictions(self):
        y_true = np.array([0, 0, 1, 1])
        y_pred = np.array([0, 0, 1, 1])
        cm = confusion_matrix(y_true, y_pred)
        assert cm[0, 0] == 2
        assert cm[1, 1] == 2
        assert cm[0, 1] == 0
        assert cm[1, 0] == 0

    def test_multiclass_confusion_matrix(self):
        y_true = np.array([0, 1, 2, 0, 1, 2])
        y_pred = np.array([0, 1, 2, 1, 1, 0])
        cm = confusion_matrix(y_true, y_pred)
        assert cm.shape == (3, 3)
        assert cm[0, 0] == 1  # class 0 correct
        assert cm[1, 1] == 2  # class 1 correct (2 times)
        assert cm[2, 2] == 1  # class 2 correct

    def test_with_custom_labels(self):
        y_true = np.array([0, 1])
        y_pred = np.array([0, 1])
        cm = confusion_matrix(y_true, y_pred, labels=np.array([0, 1, 2]))
        assert cm.shape == (3, 3)


class TestPrecisionRecallF1:
    """Test suite for precision, recall, and F1."""

    def test_perfect_precision(self):
        y_true = np.array([0, 0, 1, 1])
        y_pred = np.array([0, 0, 1, 1])
        assert precision_score(y_true, y_pred, average="macro") == 1.0

    def test_perfect_recall(self):
        y_true = np.array([0, 0, 1, 1])
        y_pred = np.array([0, 0, 1, 1])
        assert recall_score(y_true, y_pred, average="macro") == 1.0

    def test_perfect_f1(self):
        y_true = np.array([0, 0, 1, 1])
        y_pred = np.array([0, 0, 1, 1])
        assert f1_score(y_true, y_pred, average="macro") == 1.0

    def test_precision_binary(self):
        # Predicted 1 for 2 samples: 1 correct, 1 wrong
        y_true = np.array([0, 1, 1, 1])
        y_pred = np.array([1, 1, 0, 1])
        # Class 1: TP=2, FP=1 -> precision=2/3
        # Class 0: TP=0, FP=1 -> precision=0
        p = precision_score(y_true, y_pred, average="macro")
        assert abs(p - (2/3 + 0) / 2) < 1e-10

    def test_recall_binary(self):
        # Actual 1 for 3 samples: 2 recalled, 1 missed
        y_true = np.array([0, 1, 1, 1])
        y_pred = np.array([1, 1, 0, 1])
        # Class 1: TP=2, FN=1 -> recall=2/3
        # Class 0: TP=0, FN=1 -> recall=0
        r = recall_score(y_true, y_pred, average="macro")
        assert abs(r - (2/3 + 0) / 2) < 1e-10

    def test_micro_average(self):
        y_true = np.array([0, 0, 1, 1])
        y_pred = np.array([0, 1, 0, 1])
        # micro precision = total TP / total predicted = 2/4 = 0.5
        p = precision_score(y_true, y_pred, average="micro")
        assert abs(p - 0.5) < 1e-10

    def test_weighted_average(self):
        y_true = np.array([0, 0, 0, 1])
        y_pred = np.array([0, 0, 1, 1])
        # Class 0: TP=2, FP=0, support=3 -> precision=1.0
        # Class 1: TP=1, FP=1, support=1 -> precision=0.5
        # weighted = (1.0*3 + 0.5*1) / 4 = 3.5/4 = 0.875
        p = precision_score(y_true, y_pred, average="weighted")
        assert abs(p - 0.875) < 1e-10

    def test_f1_balances_precision_recall(self):
        y_true = np.array([0, 0, 1, 1])
        y_pred = np.array([0, 0, 1, 1])
        f1 = f1_score(y_true, y_pred, average="macro")
        p = precision_score(y_true, y_pred, average="macro")
        r = recall_score(y_true, y_pred, average="macro")
        assert abs(f1 - 2 * p * r / (p + r)) < 1e-10


class TestClassificationReport:
    """Test suite for the classification report."""

    def test_report_output(self):
        y_true = np.array([0, 0, 1, 1, 2, 2])
        y_pred = np.array([0, 1, 1, 1, 2, 0])
        report = classification_report(y_true, y_pred, target_names=["A", "B", "C"])
        assert "precision" in report
        assert "recall" in report
        assert "f1-score" in report
        assert "A" in report
        assert "B" in report
        assert "C" in report

    def test_report_contains_weighted_avg(self):
        y_true = np.array([0, 1, 0, 1])
        y_pred = np.array([0, 1, 0, 1])
        report = classification_report(y_true, y_pred)
        assert "weighted avg" in report


# =============================================================================
# Regression Metrics Tests
# =============================================================================


class TestMSE:
    """Test suite for MSE."""

    def test_zero_mse(self):
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([1.0, 2.0, 3.0])
        assert mean_squared_error(y_true, y_pred) == 0.0

    def test_mse_calculation(self):
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([1.5, 2.5, 3.5])
        # MSE = mean([0.25, 0.25, 0.25]) = 0.25
        assert abs(mean_squared_error(y_true, y_pred) - 0.25) < 1e-10

    def test_mse_large_errors(self):
        y_true = np.array([0.0, 0.0])
        y_pred = np.array([10.0, 10.0])
        assert mean_squared_error(y_true, y_pred) == 100.0


class TestRMSE:
    """Test suite for RMSE."""

    def test_zero_rmse(self):
        y_true = np.array([1.0, 2.0])
        y_pred = np.array([1.0, 2.0])
        assert root_mean_squared_error(y_true, y_pred) == 0.0

    def test_rmse_calculation(self):
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([1.5, 2.5, 3.5])
        # RMSE = sqrt(0.25) = 0.5
        assert abs(root_mean_squared_error(y_true, y_pred) - 0.5) < 1e-10


class TestMAE:
    """Test suite for MAE."""

    def test_zero_mae(self):
        y_true = np.array([1.0, 2.0])
        y_pred = np.array([1.0, 2.0])
        assert mean_absolute_error(y_true, y_pred) == 0.0

    def test_mae_calculation(self):
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([1.5, 2.5, 3.5])
        # MAE = mean([0.5, 0.5, 0.5]) = 0.5
        assert abs(mean_absolute_error(y_true, y_pred) - 0.5) < 1e-10


class TestR2Score:
    """Test suite for R-squared."""

    def test_perfect_r2(self):
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([1.0, 2.0, 3.0])
        assert abs(r2_score(y_true, y_pred) - 1.0) < 1e-10

    def test_mean_prediction_r2(self):
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([2.0, 2.0, 2.0])  # Predicting the mean
        assert abs(r2_score(y_true, y_pred)) < 1e-10

    def test_r2_poor_prediction(self):
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([10.0, 20.0, 30.0])  # Very bad predictions
        assert r2_score(y_true, y_pred) < 0

    def test_r2_good_prediction(self):
        np.random.seed(42)
        y_true = np.random.randn(100) * 10 + 50
        y_pred = y_true + np.random.randn(100) * 1  # Small noise
        r2 = r2_score(y_true, y_pred)
        assert r2 > 0.9


# =============================================================================
# Permutation Importance Tests
# =============================================================================


class TestPermutationImportance:
    """Test suite for permutation importance."""

    @pytest.fixture
    def simple_model(self):
        """Create a simple model for testing."""
        from src import RandomForestClassifier

        np.random.seed(42)
        X = np.random.randn(100, 3)
        y = (X[:, 0] > 0).astype(int)  # Only feature 0 matters

        clf = RandomForestClassifier(n_estimators=20, random_state=42)
        clf.fit(X, y)
        return clf, X, y

    def test_returns_correct_keys(self, simple_model):
        """Test that permutation importance returns the correct dictionary keys."""
        clf, X, y = simple_model
        result = permutation_importance(clf, X, y, n_repeats=5, random_state=42)

        assert "importances_mean" in result
        assert "importances_std" in result
        assert "importances" in result
        assert "baseline_score" in result

    def test_importances_shape(self, simple_model):
        """Test that importances have the correct shape."""
        clf, X, y = simple_model
        n_features = X.shape[1]
        n_repeats = 10

        result = permutation_importance(clf, X, y, n_repeats=n_repeats, random_state=42)

        assert result["importances_mean"].shape == (n_features,)
        assert result["importances_std"].shape == (n_features,)
        assert result["importances"].shape == (n_features, n_repeats)

    def test_important_feature_higher_importance(self, simple_model):
        """Test that the truly important feature gets higher importance."""
        clf, X, y = simple_model
        result = permutation_importance(clf, X, y, n_repeats=20, random_state=42)

        # Feature 0 is the only important feature
        assert result["importances_mean"][0] > result["importances_mean"][1]
        assert result["importances_mean"][0] > result["importances_mean"][2]

    def test_reproducibility(self, simple_model):
        """Test that results are reproducible with the same random_state."""
        clf, X, y = simple_model

        result1 = permutation_importance(clf, X, y, n_repeats=5, random_state=42)
        result2 = permutation_importance(clf, X, y, n_repeats=5, random_state=42)

        np.testing.assert_array_equal(result1["importances"], result2["importances"])

    def test_scoring_mse(self):
        """Test permutation importance with MSE scoring."""
        from src.random_forest_regressor import RandomForestRegressor

        np.random.seed(42)
        X = np.random.randn(100, 3)
        y = 3 * X[:, 0] + np.random.randn(100) * 0.1

        reg = RandomForestRegressor(n_estimators=20, random_state=42)
        reg.fit(X, y)

        result = permutation_importance(reg, X, y, n_repeats=5, random_state=42, scoring="mse")

        assert "importances_mean" in result
        # Feature 0 should have highest importance
        assert result["importances_mean"][0] > result["importances_mean"][1]


# =============================================================================
# Train/Test Split Tests
# =============================================================================


class TestTrainTestSplit:
    """Test suite for train_test_split."""

    def test_split_sizes(self):
        X = np.arange(100).reshape(50, 2)
        y = np.arange(50)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        assert len(X_train) == 40
        assert len(X_test) == 10
        assert len(y_train) == 40
        assert len(y_test) == 10

    def test_no_data_leakage(self):
        X = np.arange(100).reshape(50, 2)
        y = np.arange(50)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Train and test should not overlap
        train_set = set(map(tuple, X_train))
        test_set = set(map(tuple, X_test))
        assert len(train_set & test_set) == 0

    def test_reproducibility(self):
        X = np.random.randn(50, 3)
        y = np.random.randint(0, 2, 50)

        X_train1, X_test1, y_train1, y_test1 = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        X_train2, X_test2, y_train2, y_test2 = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        np.testing.assert_array_equal(X_train1, X_train2)
        np.testing.assert_array_equal(X_test1, X_test2)

    def test_all_data_present(self):
        X = np.arange(100).reshape(50, 2)
        y = np.arange(50)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # All original data should be in either train or test
        all_X = np.vstack([X_train, X_test])
        all_y = np.concatenate([y_train, y_test])
        assert len(all_X) == len(X)
        assert len(all_y) == len(y)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
