"""
SVM 支持向量机 - 从零实现
========================

核心组件:
- kernel: 核函数实现 (线性核、RBF核、多项式核)
- smo: SMO 优化算法
- svm: SVM 分类器
"""

from .svm import SVM
from .kernel import linear_kernel, rbf_kernel, polynomial_kernel

__version__ = "1.0.0"
__all__ = ["SVM", "linear_kernel", "rbf_kernel", "polynomial_kernel"]
