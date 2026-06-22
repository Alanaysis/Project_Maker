"""
Random Forest - A from-scratch implementation of Random Forest for learning ensemble methods.

This package implements:
- DecisionTreeClassifier: A CART decision tree with support for Gini impurity and entropy
- RandomForestClassifier: An ensemble of decision trees using bagging and random feature selection
"""

from .decision_tree import DecisionTreeClassifier
from .random_forest import RandomForestClassifier

__version__ = "0.1.0"
__all__ = ["DecisionTreeClassifier", "RandomForestClassifier"]
