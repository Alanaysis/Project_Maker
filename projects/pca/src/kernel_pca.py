"""
核 PCA (Kernel PCA)

非线性降维方法，通过核技巧将数据映射到高维特征空间后再进行 PCA。
"""

import numpy as np
from typing import Optional, Literal


class KernelPCA:
    """
    核主成分分析

    通过核函数实现非线性降维。

    Parameters
    ----------
    n_components : int
        保留的主成分数量。
    kernel : str
        核函数类型: 'rbf', 'poly', 'sigmoid', 'linear'
    gamma : float or None
        RBF 核的参数。None 表示使用 1/n_features。
    degree : int
        多项式核的阶数。
    coef0 : float
        poly 和 sigmoid 核的常数项。
    """

    def __init__(
        self,
        n_components: int = 2,
        kernel: Literal['rbf', 'poly', 'sigmoid', 'linear'] = 'rbf',
        gamma: Optional[float] = None,
        degree: int = 3,
        coef0: float = 1.0
    ):
        self.n_components = n_components
        self.kernel = kernel
        self.gamma = gamma
        self.degree = degree
        self.coef0 = coef0

        self.X_fit_ = None
        self.lambdas_ = None  # 特征值
        self.alphas_ = None  # 特征向量
        self.gamma_ = None
        self.K_fit_ = None

    def _compute_kernel(self, X: np.ndarray, Y: Optional[np.ndarray] = None) -> np.ndarray:
        """计算核矩阵"""
        if Y is None:
            Y = X

        if self.kernel == 'linear':
            K = X @ Y.T

        elif self.kernel == 'rbf':
            # K(x, y) = exp(-gamma * ||x - y||^2)
            sq_dists = np.sum(X**2, axis=1, keepdims=True) + \
                       np.sum(Y**2, axis=1, keepdims=True).T - \
                       2 * X @ Y.T
            K = np.exp(-self.gamma_ * sq_dists)

        elif self.kernel == 'poly':
            K = (self.gamma_ * X @ Y.T + self.coef0) ** self.degree

        elif self.kernel == 'sigmoid':
            K = np.tanh(self.gamma_ * X @ Y.T + self.coef0)

        else:
            raise ValueError(f"未知核函数: {self.kernel}")

        return K

    def fit(self, X: np.ndarray) -> 'KernelPCA':
        """
        拟合核 PCA 模型

        Parameters
        ----------
        X : np.ndarray, shape (n_samples, n_features)

        Returns
        -------
        self
        """
        X = np.asarray(X, dtype=np.float64)
        n_samples, n_features = X.shape
        self.X_fit_ = X.copy()

        # 设置 gamma
        if self.gamma is None:
            self.gamma_ = 1.0 / n_features
        else:
            self.gamma_ = self.gamma

        # 计算核矩阵
        K = self._compute_kernel(X)
        self.K_fit_ = K

        # 中心化核矩阵
        one_n = np.ones((n_samples, n_samples)) / n_samples
        K_centered = K - one_n @ K - K @ one_n + one_n @ K @ one_n

        # 特征值分解
        eigenvalues, eigenvectors = np.linalg.eigh(K_centered)

        # 按特征值降序排列
        idx = np.argsort(eigenvalues)[::-1]
        eigenvalues = eigenvalues[idx]
        eigenvectors = eigenvectors[:, idx]

        # 选择正特征值
        positive_idx = eigenvalues > 1e-10
        eigenvalues = eigenvalues[positive_idx]
        eigenvectors = eigenvectors[:, positive_idx]

        # 选择前 n_components 个
        n_components = min(self.n_components, len(eigenvalues))
        self.lambdas_ = eigenvalues[:n_components]
        self.alphas_ = eigenvectors[:, :n_components]

        # 归一化特征向量
        self.alphas_ = self.alphas_ / np.sqrt(self.lambdas_)[np.newaxis, :]

        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        将数据投影到核 PCA 空间

        Parameters
        ----------
        X : np.ndarray, shape (n_samples, n_features)

        Returns
        -------
        X_new : np.ndarray, shape (n_samples, n_components)
        """
        K = self._compute_kernel(X, self.X_fit_)

        # 中心化
        n_fit = self.X_fit_.shape[0]
        one_n_train = np.ones((X.shape[0], n_fit)) / n_fit
        one_n = np.ones((n_fit, n_fit)) / n_fit
        K_centered = K - one_n_train @ self.K_fit_ - K @ one_n + one_n_train @ self.K_fit_ @ one_n

        return K_centered @ self.alphas_

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        """拟合并转换数据"""
        self.fit(X)
        return self.transform(X)

    def __repr__(self) -> str:
        return (f"KernelPCA(n_components={self.n_components}, "
                f"kernel='{self.kernel}', gamma={self.gamma})")
