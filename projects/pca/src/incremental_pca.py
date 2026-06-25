"""
增量 PCA (Incremental PCA)

适用于大数据集，分批处理数据，避免将全部数据加载到内存。
"""

import numpy as np
from typing import Optional, Iterator


class IncrementalPCA:
    """
    增量主成分分析

    通过分批处理数据实现大规模 PCA，无需一次性加载全部数据。

    Parameters
    ----------
    n_components : int or None
        保留的主成分数量。None 表示保留所有成分。
    batch_size : int or None
        每批处理的样本数量。None 表示自动选择。
    """

    def __init__(self, n_components: Optional[int] = None, batch_size: Optional[int] = None):
        self.n_components = n_components
        self.batch_size = batch_size
        self.components_ = None
        self.mean_ = None
        self.var_ = None
        self.explained_variance_ = None
        self.explained_variance_ratio_ = None
        self.singular_values_ = None
        self.n_samples_seen_ = 0
        self.n_features_ = None
        # 存储批次数据的 SVD 结果
        self._batch_svd = []

    def fit(self, X: np.ndarray) -> 'IncrementalPCA':
        """
        拟合增量 PCA 模型

        Parameters
        ----------
        X : np.ndarray, shape (n_samples, n_features)

        Returns
        -------
        self
        """
        X = np.asarray(X, dtype=np.float64)
        n_samples, n_features = X.shape

        if self.n_components is None:
            self.n_components = min(n_samples, n_features)

        # 设置 batch_size
        if self.batch_size is None:
            self.batch_size = min(5 * self.n_components, n_samples)

        # 初始化
        self.n_features_ = n_features
        self.mean_ = np.zeros(n_features)
        self.var_ = np.zeros(n_features)
        self.n_samples_seen_ = 0
        self._batch_svd = []

        # 分批处理
        for batch in self._create_batches(X):
            self._partial_fit(batch)

        # 合并所有批次的 SVD 结果
        self._merge_svd()

        return self

    def partial_fit(self, X: np.ndarray) -> 'IncrementalPCA':
        """
        增量更新模型

        Parameters
        ----------
        X : np.ndarray, shape (n_samples, n_features)
            新的一批数据

        Returns
        -------
        self
        """
        X = np.asarray(X, dtype=np.float64)
        n_samples, n_features = X.shape

        if self.n_components is None:
            self.n_components = min(n_samples, n_features)

        if self.n_features_ is None:
            self.n_features_ = n_features
            self.mean_ = np.zeros(n_features)
            self.var_ = np.zeros(n_features)
            self._batch_svd = []

        self._partial_fit(X)
        self._merge_svd()

        return self

    def _create_batches(self, X: np.ndarray) -> Iterator[np.ndarray]:
        """创建数据批次"""
        n_samples = X.shape[0]
        for start in range(0, n_samples, self.batch_size):
            end = min(start + self.batch_size, n_samples)
            yield X[start:end]

    def _partial_fit(self, X: np.ndarray):
        """处理一批数据"""
        n_samples, n_features = X.shape

        # 更新均值（增量公式）
        col_mean = np.mean(X, axis=0)
        n_total = self.n_samples_seen_ + n_samples

        if self.n_samples_seen_ == 0:
            self.mean_ = col_mean
        else:
            delta = col_mean - self.mean_
            self.mean_ = self.mean_ + delta * n_samples / n_total

        # 中心化数据
        X_centered = X - col_mean

        # 对该批次进行 SVD
        U, S, Vt = np.linalg.svd(X_centered, full_matrices=False)

        # 存储批次结果
        self._batch_svd.append({
            'S': S,
            'Vt': Vt,
            'n_samples': n_samples,
            'mean': col_mean
        })

        # 更新方差
        col_var = np.var(X, axis=0, ddof=1) if n_samples > 1 else np.zeros(n_features)
        if self.n_samples_seen_ == 0:
            self.var_ = col_var
        else:
            delta = col_mean - self.mean_
            self.var_ = (
                (self.n_samples_seen_ * self.var_ + n_samples * col_var) / n_total +
                self.n_samples_seen_ * n_samples * (delta ** 2) / (n_total ** 2)
            )

        self.n_samples_seen_ = n_total

    def _merge_svd(self):
        """合并所有批次的 SVD 结果"""
        if not self._batch_svd:
            return

        n_features = self.n_features_
        n_total = self.n_samples_seen_

        # 构建组合矩阵用于 SVD
        # 方法：将所有批次的 S * Vt 堆叠，然后进行 SVD
        all_SVt = []
        for batch in self._batch_svd:
            S = batch['S']
            Vt = batch['Vt']
            # S * Vt 的形状是 (n_components, n_features)
            SVt = np.diag(S) @ Vt
            all_SVt.append(SVt)

        # 堆叠所有批次的结果
        combined = np.vstack(all_SVt)

        # 对组合矩阵进行 SVD
        U, S, Vt = np.linalg.svd(combined, full_matrices=False)

        # 选择前 n_components 个
        n_comp = min(self.n_components, len(S))
        self.components_ = Vt[:n_comp]
        self.singular_values_ = S[:n_comp]

        # 计算解释方差
        total_var = np.sum(self.var_)
        if total_var > 0:
            self.explained_variance_ = self.singular_values_ ** 2 / (n_total - 1)
            self.explained_variance_ratio_ = self.explained_variance_ / total_var

    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        将数据投影到主成分空间

        Parameters
        ----------
        X : np.ndarray, shape (n_samples, n_features)

        Returns
        -------
        X_new : np.ndarray, shape (n_samples, n_components)
        """
        X = np.asarray(X, dtype=np.float64)
        X_centered = X - self.mean_
        return X_centered @ self.components_.T

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        """拟合并转换数据"""
        self.fit(X)
        return self.transform(X)

    def inverse_transform(self, X_new: np.ndarray) -> np.ndarray:
        """将投影数据还原到原始空间"""
        X_new = np.asarray(X_new, dtype=np.float64)
        return X_new @ self.components_ + self.mean_

    def __repr__(self) -> str:
        return (f"IncrementalPCA(n_components={self.n_components}, "
                f"batch_size={self.batch_size})")
