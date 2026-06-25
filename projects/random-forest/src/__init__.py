"""
Random Forest - A from-scratch implementation of Random Forest for learning ensemble methods.

This package implements:
- DecisionTreeClassifier: A CART decision tree with support for Gini impurity and entropy
- RandomForestClassifier: An ensemble of decision trees using bagging and random feature selection
- DecisionTreeRegressor: A CART regression tree using MSE as the splitting criterion
- RandomForestRegressor: An ensemble of regression trees using bagging and averaging
- evaluation: Metrics for classification (accuracy, precision, recall, F1) and regression (MSE, R2)
"""

from .decision_tree import DecisionTreeClassifier
from .random_forest import RandomForestClassifier
from .random_forest_regressor import DecisionTreeRegressor, RandomForestRegressor
from .evaluation import (
    accuracy,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
    mean_squared_error,
    root_mean_squared_error,
    mean_absolute_error,
    r2_score,
    permutation_importance,
    train_test_split,
)

__version__ = "0.2.0"
__all__ = [
    "DecisionTreeClassifier",
    "RandomForestClassifier",
    "DecisionTreeRegressor",
    "RandomForestRegressor",
    "accuracy",
    "precision_score",
    "recall_score",
    "f1_score",
    "confusion_matrix",
    "classification_report",
    "mean_squared_error",
    "root_mean_squared_error",
    "mean_absolute_error",
    "r2_score",
    "permutation_importance",
    "train_test_split",
]
