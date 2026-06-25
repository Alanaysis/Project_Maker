"""
实际应用模块

包含最小二乘、SVM 求解、投资组合优化等应用。
"""

from .least_squares import LeastSquares, RidgeRegression, LassoRegression
from .svm import SVM, KernelSVM
from .portfolio import PortfolioOptimizer

__all__ = [
    "LeastSquares",
    "RidgeRegression",
    "LassoRegression",
    "SVM",
    "KernelSVM",
    "PortfolioOptimizer",
]
