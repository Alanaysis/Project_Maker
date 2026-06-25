"""
KNN 回归器模块

实现 K-Nearest Neighbors 回归算法，支持平均值和距离加权平均。
"""

import numpy as np
from typing import Optional, Union
from .distance_metrics import DistanceMetrics


class KNNRegressor:
    """
    KNN 回归器

    K-Nearest Neighbors 回归算法，通过 K 个最近邻的目标值
    进行预测，支持简单平均和距离加权平均。

    Attributes:
        k: 近邻数量
        metric: 距离度量方式
        weights: 权重策略 ('uniform' 或 'distance')
        X_train: 训练特征矩阵
        y_train: 训练目标值

    Examples:
        >>> import numpy as np
        >>> from src.knn_regressor import KNNRegressor
        >>>
        >>> X_train = np.array([[1], [2], [3], [4], [5]])
        >>> y_train = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        >>>
        >>> reg = KNNRegressor(k=3, weights='distance')
        >>> reg.fit(X_train, y_train)
        >>> prediction = reg.predict(np.array([[3.5]]))
    """

    def __init__(self, k: int = 5, metric: str = 'euclidean',
                 weights: str = 'uniform'):
        """
        初始化 KNN 回归器

        Args:
            k: 近邻数量 (默认: 5)
            metric: 距离度量方式 (默认: 'euclidean')
            weights: 权重策略 (默认: 'uniform')
                - 'uniform': 等权平均
                - 'distance': 距离加权平均

        Raises:
            ValueError: K 值不是正整数
            ValueError: 不支持的距离度量或权重策略
        """
        if not isinstance(k, int) or k <= 0:
            raise ValueError("k must be a positive integer")

        valid_metrics = ['euclidean', 'manhattan', 'minkowski', 'cosine']
        if metric not in valid_metrics:
            raise ValueError(
                f"Unsupported metric: {metric}. "
                f"Supported metrics: {valid_metrics}"
            )

        valid_weights = ['uniform', 'distance']
        if weights not in valid_weights:
            raise ValueError(
                f"Unsupported weights: {weights}. "
                f"Supported weights: {valid_weights}"
            )

        self.k = k
        self.metric = metric
        self.weights = weights
        self.X_train = None
        self.y_train = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> 'KNNRegressor':
        """
        训练模型（存储训练数据）

        Args:
            X: 训练特征矩阵 (n_samples, n_features)
            y: 训练目标值 (n_samples,)

        Returns:
            self: 返回自身，支持链式调用

        Raises:
            ValueError: 输入数据格式不正确
        """
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float)

        if X.ndim != 2:
            raise ValueError("X must be a 2D array")

        if y.ndim != 1:
            raise ValueError("y must be a 1D array")

        if X.shape[0] != y.shape[0]:
            raise ValueError(
                "X and y must have the same number of samples. "
                f"Got X: {X.shape[0]}, y: {y.shape[0]}"
            )

        if X.shape[0] == 0:
            raise ValueError("Training data cannot be empty")

        if self.k > X.shape[0]:
            raise ValueError(
                f"k ({self.k}) must be less than or equal to "
                f"number of training samples ({X.shape[0]})"
            )

        self.X_train = X.copy()
        self.y_train = y.copy()

        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        预测新样本

        Args:
            X: 测试特征矩阵 (n_samples, n_features)

        Returns:
            predictions: 预测目标值 (n_samples,)

        Raises:
            RuntimeError: 模型未训练
            ValueError: 输入数据格式不正确
        """
        if self.X_train is None:
            raise RuntimeError("Model must be fitted before prediction")

        X = np.asarray(X, dtype=float)

        if X.ndim == 1:
            X = X.reshape(1, -1)

        if X.shape[1] != self.X_train.shape[1]:
            raise ValueError(
                f"Number of features must match training data. "
                f"Expected {self.X_train.shape[1]}, got {X.shape[1]}"
            )

        predictions = np.array([self._predict_single(x) for x in X])

        return predictions

    def _predict_single(self, x: np.ndarray) -> float:
        """
        预测单个样本

        Args:
            x: 单个样本 (n_features,)

        Returns:
            prediction: 预测目标值
        """
        distances = self._compute_distances(x)

        k_nearest_indices = np.argsort(distances)[:self.k]
        k_nearest_distances = distances[k_nearest_indices]
        k_nearest_values = self.y_train[k_nearest_indices]

        if self.weights == 'distance':
            return self._weighted_average(k_nearest_values, k_nearest_distances)
        else:
            return self._simple_average(k_nearest_values)

    def _simple_average(self, values: np.ndarray) -> float:
        """
        简单平均

        Args:
            values: 近邻目标值

        Returns:
            平均值
        """
        return float(np.mean(values))

    def _weighted_average(self, values: np.ndarray,
                          distances: np.ndarray) -> float:
        """
        距离加权平均

        权重 = 1 / distance，距离越近权重越大。

        Args:
            values: 近邻目标值
            distances: 近邻距离

        Returns:
            加权平均值
        """
        # 避免除零（距离为 0 时使用极大权重）
        safe_distances = np.where(distances == 0, 1e-10, distances)
        weights = 1.0 / safe_distances

        weighted_sum = np.sum(weights * values)
        weight_total = np.sum(weights)

        return float(weighted_sum / weight_total)

    def _compute_distances(self, x: np.ndarray) -> np.ndarray:
        """
        计算与所有训练样本的距离

        Args:
            x: 单个样本 (n_features,)

        Returns:
            distances: 距离数组 (n_samples,)
        """
        if self.metric == 'euclidean':
            distances = np.sqrt(np.sum((self.X_train - x) ** 2, axis=1))
        elif self.metric == 'manhattan':
            distances = np.sum(np.abs(self.X_train - x), axis=1)
        elif self.metric == 'minkowski':
            distance_func = DistanceMetrics.get_metric('minkowski')
            distances = np.array([
                distance_func(x, x_train, p=2)
                for x_train in self.X_train
            ])
        else:
            distance_func = DistanceMetrics.get_metric(self.metric)
            distances = np.array([
                distance_func(x, x_train)
                for x_train in self.X_train
            ])

        return distances

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """
        计算 R^2 决定系数

        Args:
            X: 测试特征矩阵 (n_samples, n_features)
            y: 真实目标值 (n_samples,)

        Returns:
            r2: R^2 决定系数
        """
        predictions = self.predict(X)

        ss_res = np.sum((y - predictions) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)

        if ss_tot == 0:
            return 0.0

        return float(1 - ss_res / ss_tot)

    def get_params(self) -> dict:
        """获取回归器参数"""
        return {
            'k': self.k,
            'metric': self.metric,
            'weights': self.weights
        }

    def set_params(self, **params) -> 'KNNRegressor':
        """设置回归器参数"""
        for key, value in params.items():
            if key == 'k':
                if not isinstance(value, int) or value <= 0:
                    raise ValueError("k must be a positive integer")
                self.k = value
            elif key == 'metric':
                valid_metrics = ['euclidean', 'manhattan', 'minkowski', 'cosine']
                if value not in valid_metrics:
                    raise ValueError(
                        f"Unsupported metric: {value}. "
                        f"Supported metrics: {valid_metrics}"
                    )
                self.metric = value
            elif key == 'weights':
                valid_weights = ['uniform', 'distance']
                if value not in valid_weights:
                    raise ValueError(
                        f"Unsupported weights: {value}. "
                        f"Supported weights: {valid_weights}"
                    )
                self.weights = value
            else:
                raise ValueError(f"Unknown parameter: {key}")

        return self

    def __repr__(self) -> str:
        return (
            f"KNNRegressor(k={self.k}, metric='{self.metric}', "
            f"weights='{self.weights}')"
        )
