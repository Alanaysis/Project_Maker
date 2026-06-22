"""
核函数模块
==========

实现 SVM 中常用的核函数:
- 线性核 (Linear Kernel): K(x, y) = x · y
- RBF 核 (Radial Basis Function): K(x, y) = exp(-gamma * ||x - y||^2)
- 多项式核 (Polynomial Kernel): K(x, y) = (x · y + coef0)^degree

核函数的作用是将数据映射到高维空间，使得在低维空间中线性不可分的数据
在高维空间中变得线性可分。这就是"核技巧"(Kernel Trick)。
"""

import numpy as np
from typing import Callable


def linear_kernel() -> Callable[[np.ndarray, np.ndarray], float]:
    """
    线性核函数: K(x, y) = x · y

    最简单的核函数，等价于在原始空间中进行线性分类。
    适用于线性可分的数据。

    返回:
        核函数，接受两个向量，返回它们的内积
    """
    def kernel(x: np.ndarray, y: np.ndarray) -> float:
        return np.dot(x, y)
    return kernel


def rbf_kernel(gamma: float = 1.0) -> Callable[[np.ndarray, np.ndarray], float]:
    """
    RBF 核函数 (高斯核): K(x, y) = exp(-gamma * ||x - y||^2)

    最常用的核函数之一，可以将数据映射到无限维空间。
    gamma 参数控制高斯函数的宽度:
    - gamma 大: 每个支持向量只影响附近的数据点，可能导致过拟合
    - gamma 小: 每个支持向量影响更广的区域，可能导致欠拟合

    参数:
        gamma: 高斯核的宽度参数，必须为正数

    返回:
        核函数，接受两个向量，返回它们的 RBF 核值
    """
    if gamma <= 0:
        raise ValueError("gamma 必须为正数")

    def kernel(x: np.ndarray, y: np.ndarray) -> float:
        diff = x - y
        return np.exp(-gamma * np.dot(diff, diff))
    return kernel


def polynomial_kernel(
    degree: int = 3,
    coef0: float = 1.0
) -> Callable[[np.ndarray, np.ndarray], float]:
    """
    多项式核函数: K(x, y) = (x · y + coef0)^degree

    将数据映射到多项式特征空间。
    degree 控制多项式的阶数，coef0 控制独立项的权重。

    参数:
        degree: 多项式的阶数，必须为正整数
        coef0: 核函数的独立项系数

    返回:
        核函数，接受两个向量，返回它们的多项式核值
    """
    if degree <= 0:
        raise ValueError("degree 必须为正整数")

    def kernel(x: np.ndarray, y: np.ndarray) -> float:
        return (np.dot(x, y) + coef0) ** degree
    return kernel


def precompute_kernel_matrix(
    X: np.ndarray,
    kernel_func: Callable[[np.ndarray, np.ndarray], float]
) -> np.ndarray:
    """
    预计算核矩阵 (Gram 矩阵)

    对于数据集 X = {x1, x2, ..., xn}，核矩阵 K 的元素为:
    K[i][j] = kernel(xi, xj)

    预计算核矩阵可以避免在 SMO 优化过程中重复计算核函数值。

    参数:
        X: 训练数据，形状为 (n_samples, n_features)
        kernel_func: 核函数

    返回:
        核矩阵，形状为 (n_samples, n_samples)
    """
    n_samples = X.shape[0]
    K = np.zeros((n_samples, n_samples))

    for i in range(n_samples):
        for j in range(i, n_samples):
            K[i, j] = kernel_func(X[i], X[j])
            K[j, i] = K[i, j]  # 核矩阵是对称的

    return K
