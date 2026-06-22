"""
PCA 主成分分析核心模块

主成分分析（Principal Component Analysis, PCA）是一种常用的无监督降维方法。
它的目标是找到数据方差最大的方向（主成分），将高维数据投影到这些方向上，
从而实现降维。

核心循环：数据 → 中心化 → 协方差矩阵 → 特征值分解 → 投影

数学原理：
    1. 对数据 X 进行中心化：X_centered = X - mean(X)
    2. 计算协方差矩阵：C = (1/(n-1)) * X_centered^T * X_centered
    3. 对 C 进行特征值分解：C = V * Λ * V^T
    4. 选择前 k 个最大特征值对应的特征向量
    5. 投影：X_pca = X_centered * V_k
"""

import numpy as np
from numpy.typing import NDArray

from .covariance import compute_covariance_matrix, center_data
from .eigen import eigen_decomposition


class PCA:
    """
    主成分分析（PCA）降维算法。

    Parameters
    ----------
    n_components : int or float
        保留的主成分数量。
        - 如果是 int：直接指定保留的主成分数量。
        - 如果是 float (0, 1]：保留解释方差比例 >= 该值的主成分数量。
    method : str
        特征值分解方法："qr" 或 "power"。

    Attributes
    ----------
    components_ : np.ndarray of shape (n_components, n_features)
        主成分方向（特征向量），每行是一个主成分。
    explained_variance_ : np.ndarray of shape (n_components,)
        每个主成分解释的方差（特征值）。
    explained_variance_ratio_ : np.ndarray of shape (n_components,)
        每个主成分解释的方差比例。
    mean_ : np.ndarray of shape (n_features,)
        训练数据各特征的均值。
    n_components_ : int
        实际保留的主成分数量。
    n_features_ : int
        输入数据的特征数量。
    n_samples_ : int
        训练样本数量。

    Examples
    --------
    >>> import numpy as np
    >>> from src.pca import PCA
    >>>
    >>> # 生成示例数据
    >>> np.random.seed(42)
    >>> X = np.random.randn(100, 5)
    >>>
    >>> # 降到2维
    >>> pca = PCA(n_components=2)
    >>> X_reduced = pca.fit_transform(X)
    >>> X_reduced.shape
    (100, 2)
    >>>
    >>> # 查看解释方差比例
    >>> pca.explained_variance_ratio_
    """

    def __init__(
        self,
        n_components: int | float = 2,
        method: str = "qr",
    ):
        self.n_components = n_components
        self.method = method

        # 这些属性在 fit 后才会被设置
        self.components_: NDArray[np.float64] | None = None
        self.explained_variance_: NDArray[np.float64] | None = None
        self.explained_variance_ratio_: NDArray[np.float64] | None = None
        self.mean_: NDArray[np.float64] | None = None
        self.n_components_: int = 0
        self.n_features_: int = 0
        self.n_samples_: int = 0
        self._is_fitted: bool = False

    def fit(self, X: NDArray[np.float64]) -> "PCA":
        """
        拟合 PCA 模型。

        计算协方差矩阵并进行特征值分解，确定主成分方向。

        Parameters
        ----------
        X : np.ndarray of shape (n_samples, n_features)
            训练数据。

        Returns
        -------
        self : PCA
            拟合后的模型实例。

        Raises
        ------
        ValueError
            如果数据维度不合法或 n_components 超出范围。
        """
        X = np.asarray(X, dtype=np.float64)

        if X.ndim != 2:
            raise ValueError(f"输入必须是2D矩阵，当前维度: {X.ndim}")

        self.n_samples_, self.n_features_ = X.shape

        # Step 1: 中心化
        X_centered, self.mean_ = center_data(X)

        # Step 2: 计算协方差矩阵
        cov_matrix = compute_covariance_matrix(X_centered)

        # Step 3: 特征值分解
        eigenvalues, eigenvectors = eigen_decomposition(
            cov_matrix,
            method=self.method,
        )

        # 确定实际保留的主成分数量
        self.n_components_ = self._resolve_n_components(eigenvalues)

        # Step 4: 选择前 k 个特征值和特征向量
        self.explained_variance_ = eigenvalues[: self.n_components_]
        # 特征向量的列 -> 转置为行（每行是一个主成分方向）
        self.components_ = eigenvectors[:, : self.n_components_].T

        # 计算解释方差比例
        total_variance = np.sum(eigenvalues)
        if total_variance > 0:
            self.explained_variance_ratio_ = self.explained_variance_ / total_variance
        else:
            self.explained_variance_ratio_ = np.zeros(self.n_components_)

        self._is_fitted = True
        return self

    def transform(self, X: NDArray[np.float64]) -> NDArray[np.float64]:
        """
        将数据投影到主成分空间。

        Parameters
        ----------
        X : np.ndarray of shape (n_samples, n_features)
            要投影的数据。

        Returns
        -------
        X_projected : np.ndarray of shape (n_samples, n_components)
            投影后的低维数据。

        Raises
        ------
        RuntimeError
            如果模型尚未拟合。
        ValueError
            如果输入数据的特征数与训练数据不匹配。
        """
        self._check_fitted()
        X = np.asarray(X, dtype=np.float64)

        if X.ndim != 2:
            raise ValueError(f"输入必须是2D矩阵，当前维度: {X.ndim}")

        if X.shape[1] != self.n_features_:
            raise ValueError(
                f"输入特征数 ({X.shape[1]}) 与训练数据特征数 ({self.n_features_}) 不匹配"
            )

        # 中心化（使用训练数据的均值）
        X_centered = X - self.mean_

        # 投影：X_projected = X_centered @ components_.T
        X_projected = X_centered @ self.components_.T

        return X_projected

    def fit_transform(self, X: NDArray[np.float64]) -> NDArray[np.float64]:
        """
        拟合模型并同时返回投影后的数据。

        这是 fit() 和 transform() 的便捷组合。

        Parameters
        ----------
        X : np.ndarray of shape (n_samples, n_features)
            训练数据。

        Returns
        -------
        X_projected : np.ndarray of shape (n_samples, n_components)
            投影后的低维数据。
        """
        self.fit(X)
        return self.transform(X)

    def inverse_transform(self, X_projected: NDArray[np.float64]) -> NDArray[np.float64]:
        """
        将低维数据反投影回原始空间。

        Parameters
        ----------
        X_projected : np.ndarray of shape (n_samples, n_components)
            低维投影数据。

        Returns
        -------
        X_reconstructed : np.ndarray of shape (n_samples, n_features)
            重建的高维数据（近似值）。

        Raises
        ------
        RuntimeError
            如果模型尚未拟合。
        """
        self._check_fitted()
        X_projected = np.asarray(X_projected, dtype=np.float64)

        # 反投影：X_reconstructed = X_projected @ components_ + mean
        X_reconstructed = X_projected @ self.components_ + self.mean_

        return X_reconstructed

    def _resolve_n_components(self, eigenvalues: NDArray[np.float64]) -> int:
        """
        根据 n_components 参数确定实际保留的主成分数量。

        Parameters
        ----------
        eigenvalues : np.ndarray
            所有特征值（从大到小排列）。

        Returns
        -------
        n_components : int
            实际保留的主成分数量。
        """
        n_features = len(eigenvalues)

        if isinstance(self.n_components, float):
            # 浮点数：按解释方差比例选择
            if not (0 < self.n_components <= 1.0):
                raise ValueError(
                    f"浮点数 n_components 必须在 (0, 1] 之间，当前: {self.n_components}"
                )

            total_variance = np.sum(eigenvalues)
            cumulative_ratio = np.cumsum(eigenvalues) / total_variance

            # 找到第一个累积比例 >= n_components 的位置
            n = np.searchsorted(cumulative_ratio, self.n_components) + 1
            return min(n, n_features)

        elif isinstance(self.n_components, int):
            # 整数：直接使用
            if self.n_components < 1:
                raise ValueError(f"n_components 必须 >= 1，当前: {self.n_components}")
            if self.n_components > n_features:
                raise ValueError(
                    f"n_components ({self.n_components}) 不能大于特征数 ({n_features})"
                )
            return self.n_components

        else:
            raise TypeError(f"n_components 必须是 int 或 float，当前: {type(self.n_components)}")

    def _check_fitted(self) -> None:
        """检查模型是否已经拟合。"""
        if not self._is_fitted:
            raise RuntimeError("模型尚未拟合，请先调用 fit() 方法")

    def reconstruction_error(self, X: NDArray[np.float64]) -> float:
        """
        计算重建误差（均方误差）。

        衡量降维后再重建的数据与原始数据的差异。

        Parameters
        ----------
        X : np.ndarray of shape (n_samples, n_features)
            原始数据。

        Returns
        -------
        mse : float
            均方重建误差。
        """
        X = np.asarray(X, dtype=np.float64)
        X_projected = self.transform(X)
        X_reconstructed = self.inverse_transform(X_projected)
        mse = np.mean((X - X_reconstructed) ** 2)
        return float(mse)

    def __repr__(self) -> str:
        if self._is_fitted:
            return (
                f"PCA(n_components={self.n_components_}, method='{self.method}', "
                f"n_features={self.n_features_})"
            )
        return f"PCA(n_components={self.n_components}, method='{self.method}', not fitted)"
