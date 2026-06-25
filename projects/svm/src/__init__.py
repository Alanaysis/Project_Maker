"""
SVM 支持向量机 - 从零实现
========================

核心组件:
- kernel: 核函数实现 (线性核、RBF核、多项式核、Sigmoid核)
- smo: SMO 优化算法
- svm: SVM 分类器
- svr: SVR 回归器
- multiclass: 多分类策略 (One-vs-Rest, One-vs-One)
- metrics: 模型评估指标
"""

from .svm import SVM
from .svr import SVR
from .multiclass import OneVsRestSVM, OneVsOneSVM
from .kernel import linear_kernel, rbf_kernel, polynomial_kernel, sigmoid_kernel
from .metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    mean_squared_error,
    r2_score,
    mean_absolute_error,
)

__version__ = "2.0.0"
__all__ = [
    "SVM",
    "SVR",
    "OneVsRestSVM",
    "OneVsOneSVM",
    "linear_kernel",
    "rbf_kernel",
    "polynomial_kernel",
    "sigmoid_kernel",
    "accuracy_score",
    "precision_score",
    "recall_score",
    "f1_score",
    "confusion_matrix",
    "mean_squared_error",
    "r2_score",
    "mean_absolute_error",
]
