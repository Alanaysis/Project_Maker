"""
协方差矩阵计算模块

协方差矩阵是 PCA 的核心组件，它描述了数据各个特征之间的线性关系。
对于一个 n×d 的数据矩阵 X（n 个样本，d 个特征），协方差矩阵是一个 d×d 的对称矩阵。

数学公式：
    C = (1 / (n-1)) * X_centered^T * X_centered

其中 X_centered 是中心化后的数据（每列减去该列的均值）。

对角线元素是各特征的方差，非对角线元素是特征之间的协方差。
"""

import numpy as np
from numpy.typing import NDArray


def compute_covariance_matrix(X: NDArray[np.float64]) -> NDArray[np.float64]:
    """
    计算数据矩阵的协方差矩阵。

    Parameters
    ----------
    X : np.ndarray of shape (n_samples, n_features)
        输入数据矩阵，每行是一个样本，每列是一个特征。
        数据应该是已经中心化的（即每列均值为0）。

    Returns
    -------
    cov : np.ndarray of shape (n_features, n_features)
        协方差矩阵。

    Raises
    ------
    ValueError
        如果输入不是2D矩阵，或者样本数少于2。

    Examples
    --------
    >>> import numpy as np
    >>> X = np.array([[1, 2], [3, 4], [5, 6]], dtype=np.float64)
    >>> X_centered = X - X.mean(axis=0)
    >>> cov = compute_covariance_matrix(X_centered)
    >>> cov.shape
    (2, 2)
    """
    X = np.asarray(X, dtype=np.float64)

    if X.ndim != 2:
        raise ValueError(f"输入必须是2D矩阵，当前维度: {X.ndim}")

    n_samples, n_features = X.shape

    if n_samples < 2:
        raise ValueError(f"样本数必须 >= 2，当前: {n_samples}")

    # 协方差矩阵: C = (1 / (n-1)) * X^T * X
    # 使用 n-1 进行无偏估计（Bessel校正）
    cov = (1.0 / (n_samples - 1)) * (X.T @ X)

    return cov


def compute_covariance_matrix_manual(X: NDArray[np.float64]) -> NDArray[np.float64]:
    """
    手动逐元素计算协方差矩阵（用于教学目的）。

    这个函数展示了协方差矩阵的原始定义，不使用矩阵乘法优化。
    实际使用请调用 compute_covariance_matrix()。

    Parameters
    ----------
    X : np.ndarray of shape (n_samples, n_features)
        已中心化的数据矩阵。

    Returns
    -------
    cov : np.ndarray of shape (n_features, n_features)
        协方差矩阵。
    """
    X = np.asarray(X, dtype=np.float64)
    n_samples, n_features = X.shape

    cov = np.zeros((n_features, n_features), dtype=np.float64)

    for i in range(n_features):
        for j in range(n_features):
            # 协方差公式: Cov(Xi, Xj) = (1/(n-1)) * sum((Xi - mean_i) * (Xj - mean_j))
            # 由于数据已中心化，mean_i = mean_j = 0
            cov[i, j] = np.sum(X[:, i] * X[:, j]) / (n_samples - 1)

    return cov


def center_data(X: NDArray[np.float64]) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """
    对数据进行中心化处理（每列减去该列的均值）。

    中心化是 PCA 的第一步，确保数据以原点为中心。

    Parameters
    ----------
    X : np.ndarray of shape (n_samples, n_features)
        原始数据矩阵。

    Returns
    -------
    X_centered : np.ndarray of shape (n_samples, n_features)
        中心化后的数据矩阵。
    mean : np.ndarray of shape (n_features,)
        各特征的均值向量。
    """
    X = np.asarray(X, dtype=np.float64)
    mean = np.mean(X, axis=0)
    X_centered = X - mean
    return X_centered, mean
