"""
KNN 分类器模块

实现 K-Nearest Neighbors 分类算法。
"""

import numpy as np
from typing import Optional, Union, List, Tuple
from .distance_metrics import DistanceMetrics


class KNNClassifier:
    """
    KNN 分类器

    K-Nearest Neighbors (KNN) 是一种基于实例的监督学习算法。
    通过计算待分类样本与训练样本之间的距离，选择最近的 K 个邻居
    进行投票来决定分类结果。

    Attributes:
        k: 近邻数量
        metric: 距离度量方式
        X_train: 训练特征矩阵
        y_train: 训练标签
        classes_: 所有类别

    Examples:
        >>> import numpy as np
        >>> from src.knn_classifier import KNNClassifier
        >>>
        >>> # 创建训练数据
        >>> X_train = np.array([[1, 2], [3, 4], [5, 6]])
        >>> y_train = np.array([0, 1, 0])
        >>>
        >>> # 创建分类器
        >>> knn = KNNClassifier(k=2, metric='euclidean')
        >>> knn.fit(X_train, y_train)
        >>>
        >>> # 预测
        >>> predictions = knn.predict(np.array([[2, 3]]))
    """

    def __init__(self, k: int = 3, metric: str = 'euclidean'):
        """
        初始化 KNN 分类器

        Args:
            k: 近邻数量 (默认: 3)
            metric: 距离度量方式 (默认: 'euclidean')
                支持: 'euclidean', 'manhattan', 'minkowski', 'cosine'

        Raises:
            ValueError: K 值不是正整数
            ValueError: 不支持的距离度量
        """
        # 验证 K 值
        if not isinstance(k, int) or k <= 0:
            raise ValueError("k must be a positive integer")

        # 验证距离度量
        valid_metrics = ['euclidean', 'manhattan', 'minkowski', 'cosine']
        if metric not in valid_metrics:
            raise ValueError(
                f"Unsupported metric: {metric}. "
                f"Supported metrics: {valid_metrics}"
            )

        self.k = k
        self.metric = metric
        self.X_train = None
        self.y_train = None
        self.classes_ = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> 'KNNClassifier':
        """
        训练模型（存储训练数据）

        Args:
            X: 训练特征矩阵 (n_samples, n_features)
            y: 训练标签 (n_samples,)

        Returns:
            self: 返回自身，支持链式调用

        Raises:
            ValueError: 输入数据格式不正确
            ValueError: K 值大于训练样本数量
        """
        # 转换为 NumPy 数组
        X = np.asarray(X, dtype=float)
        y = np.asarray(y)

        # 输入验证
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

        # 存储训练数据
        self.X_train = X.copy()
        self.y_train = y.copy()
        self.classes_ = np.unique(y)

        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        预测新样本

        Args:
            X: 测试特征矩阵 (n_samples, n_features)

        Returns:
            predictions: 预测标签 (n_samples,)

        Raises:
            RuntimeError: 模型未训练
            ValueError: 输入数据格式不正确
        """
        # 检查是否已训练
        if self.X_train is None:
            raise RuntimeError("Model must be fitted before prediction")

        # 转换为 NumPy 数组
        X = np.asarray(X, dtype=float)

        # 处理单个样本
        if X.ndim == 1:
            X = X.reshape(1, -1)

        # 验证特征数量
        if X.shape[1] != self.X_train.shape[1]:
            raise ValueError(
                f"Number of features must match training data. "
                f"Expected {self.X_train.shape[1]}, got {X.shape[1]}"
            )

        # 批量预测
        predictions = np.array([self._predict_single(x) for x in X])

        return predictions

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        预测概率

        Args:
            X: 测试特征矩阵 (n_samples, n_features)

        Returns:
            probabilities: 各类别的概率 (n_samples, n_classes)

        Raises:
            RuntimeError: 模型未训练
            ValueError: 输入数据格式不正确
        """
        # 检查是否已训练
        if self.X_train is None:
            raise RuntimeError("Model must be fitted before prediction")

        # 转换为 NumPy 数组
        X = np.asarray(X, dtype=float)

        # 处理单个样本
        if X.ndim == 1:
            X = X.reshape(1, -1)

        # 验证特征数量
        if X.shape[1] != self.X_train.shape[1]:
            raise ValueError(
                f"Number of features must match training data. "
                f"Expected {self.X_train.shape[1]}, got {X.shape[1]}"
            )

        # 计算概率
        probabilities = []
        for x in X:
            proba = self._predict_proba_single(x)
            probabilities.append(proba)

        return np.array(probabilities)

    def _predict_single(self, x: np.ndarray) -> int:
        """
        预测单个样本

        Args:
            x: 单个样本 (n_features,)

        Returns:
            prediction: 预测标签
        """
        # 计算距离
        distances = self._compute_distances(x)

        # 选择 K 个近邻
        k_nearest_indices = np.argsort(distances)[:self.k]
        k_nearest_labels = self.y_train[k_nearest_indices]

        # 投票分类
        prediction = self._vote(k_nearest_labels)

        return prediction

    def _predict_proba_single(self, x: np.ndarray) -> np.ndarray:
        """
        预测单个样本的概率

        Args:
            x: 单个样本 (n_features,)

        Returns:
            probabilities: 各类别的概率 (n_classes,)
        """
        # 计算距离
        distances = self._compute_distances(x)

        # 选择 K 个近邻
        k_nearest_indices = np.argsort(distances)[:self.k]
        k_nearest_labels = self.y_train[k_nearest_indices]

        # 计算各类别概率
        probabilities = np.zeros(len(self.classes_))
        for i, cls in enumerate(self.classes_):
            probabilities[i] = np.sum(k_nearest_labels == cls) / self.k

        return probabilities

    def _compute_distances(self, x: np.ndarray) -> np.ndarray:
        """
        计算与所有训练样本的距离

        Args:
            x: 单个样本 (n_features,)

        Returns:
            distances: 距离数组 (n_samples,)
        """
        # 获取距离函数
        distance_func = DistanceMetrics.get_metric(self.metric)

        # 向量化计算
        if self.metric == 'minkowski':
            # 闵可夫斯基距离需要额外参数
            distances = np.array([
                distance_func(x, x_train, p=2)
                for x_train in self.X_train
            ])
        elif self.metric == 'euclidean':
            # 优化：使用向量化计算欧氏距离
            distances = np.sqrt(np.sum((self.X_train - x) ** 2, axis=1))
        elif self.metric == 'manhattan':
            # 优化：使用向量化计算曼哈顿距离
            distances = np.sum(np.abs(self.X_train - x), axis=1)
        else:
            # 其他距离度量
            distances = np.array([
                distance_func(x, x_train)
                for x_train in self.X_train
            ])

        return distances

    def _vote(self, neighbor_labels: np.ndarray) -> int:
        """
        投票机制（多数投票）

        Args:
            neighbor_labels: 近邻标签列表

        Returns:
            最终预测类别
        """
        # 统计各类别出现次数
        unique_labels, counts = np.unique(neighbor_labels, return_counts=True)

        # 返回出现次数最多的类别
        return unique_labels[np.argmax(counts)]

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """
        计算分类准确率

        Args:
            X: 测试特征矩阵 (n_samples, n_features)
            y: 真实标签 (n_samples,)

        Returns:
            accuracy: 分类准确率 (0 到 1)
        """
        predictions = self.predict(X)
        accuracy = np.mean(predictions == y)
        return float(accuracy)

    def get_params(self) -> dict:
        """
        获取分类器参数

        Returns:
            params: 参数字典
        """
        return {
            'k': self.k,
            'metric': self.metric
        }

    def set_params(self, **params) -> 'KNNClassifier':
        """
        设置分类器参数

        Args:
            **params: 参数字典

        Returns:
            self: 返回自身
        """
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
            else:
                raise ValueError(f"Unknown parameter: {key}")

        return self

    def __repr__(self) -> str:
        """返回分类器的字符串表示"""
        return f"KNNClassifier(k={self.k}, metric='{self.metric}')"