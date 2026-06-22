"""
K-Means 聚类算法实现

从零实现 K-Means 聚类算法，支持多种距离度量和初始化方法。
"""

import numpy as np
import warnings
from .distance import get_distance_function, pairwise_distances


class KMeans:
    """
    K-Means 聚类算法

    参数:
        n_clusters: 簇的数量，默认为 3
        max_iter: 最大迭代次数，默认为 100
        tol: 收敛阈值，默认为 1e-4
        distance: 距离度量方式，默认为 'euclidean'
        init: 初始化方法，'random' 或 'kmeans++'，默认为 'random'
        random_state: 随机种子，默认为 None
    """

    def __init__(self, n_clusters=3, max_iter=100, tol=1e-4, distance='euclidean',
                 init='random', random_state=None):
        self.n_clusters = n_clusters
        self.max_iter = max_iter
        self.tol = tol
        self.distance = distance
        self.init = init
        self.random_state = random_state

        # 结果属性
        self.cluster_centers_ = None
        self.labels_ = None
        self.inertia_ = None
        self.n_iter_ = 0

        # 距离函数
        self._distance_func = get_distance_function(distance)

    def _validate_input(self, X):
        """验证输入数据"""
        X = np.asarray(X, dtype=np.float64)

        if X.ndim == 1:
            X = X.reshape(-1, 1)

        if X.ndim != 2:
            raise ValueError("输入数据必须是 2D 数组")

        if np.any(np.isnan(X)):
            raise ValueError("输入数据包含 NaN")

        if np.any(np.isinf(X)):
            raise ValueError("输入数据包含 Inf")

        return X

    def _init_centroids_random(self, X):
        """随机初始化簇中心"""
        n_samples = X.shape[0]
        rng = np.random.RandomState(self.random_state)
        indices = rng.choice(n_samples, self.n_clusters, replace=False)
        return X[indices].copy()

    def _init_centroids_kmeans_plus_plus(self, X):
        """
        K-Means++ 初始化

        算法步骤:
        1. 随机选择第一个中心点
        2. 对于每个后续中心点，选择距离现有中心最远的点
        3. 使用概率分布选择，距离越远概率越大
        """
        n_samples, n_features = X.shape
        rng = np.random.RandomState(self.random_state)

        # 初始化中心数组
        centroids = np.empty((self.n_clusters, n_features))

        # 1. 随机选择第一个中心点
        first_idx = rng.randint(0, n_samples)
        centroids[0] = X[first_idx]

        # 2. 选择剩余中心点
        for k in range(1, self.n_clusters):
            # 计算每个点到最近中心的距离
            distances = np.min([self._distance_func(X, centroids[i])
                               for i in range(k)], axis=0)

            # 计算概率分布（距离越大，概率越大）
            probabilities = distances ** 2
            probabilities /= probabilities.sum()

            # 根据概率分布选择下一个中心点
            next_idx = rng.choice(n_samples, p=probabilities)
            centroids[k] = X[next_idx]

        return centroids

    def _init_centroids(self, X):
        """初始化簇中心"""
        if self.init == 'random':
            return self._init_centroids_random(X)
        elif self.init == 'kmeans++':
            return self._init_centroids_kmeans_plus_plus(X)
        else:
            raise ValueError(f"不支持的初始化方法: {self.init}")

    def _assign_clusters(self, X, centroids):
        """
        分配簇

        将每个数据点分配到距离最近的簇中心

        参数:
            X: 数据矩阵
            centroids: 簇中心矩阵

        返回:
            簇标签数组
        """
        # 计算每个点到每个中心的距离
        if self.distance == 'euclidean':
            # 使用高效的向量化计算
            distances = pairwise_distances(X, centroids, metric='euclidean')
        else:
            distances = self._distance_func(X, centroids)

        # 分配到最近的中心
        labels = np.argmin(distances, axis=1)

        return labels

    def _update_centroids(self, X, labels):
        """
        更新簇中心

        计算每个簇的均值作为新的中心点

        参数:
            X: 数据矩阵
            labels: 簇标签数组

        返回:
            新的簇中心矩阵
        """
        n_features = X.shape[1]
        centroids = np.empty((self.n_clusters, n_features))

        for k in range(self.n_clusters):
            # 获取属于当前簇的数据点
            cluster_points = X[labels == k]

            if len(cluster_points) > 0:
                # 计算均值作为新中心
                centroids[k] = np.mean(cluster_points, axis=0)
            else:
                # 如果簇为空，随机选择一个点作为中心
                rng = np.random.RandomState(self.random_state)
                centroids[k] = X[rng.randint(0, X.shape[0])]
                warnings.warn(f"簇 {k} 为空，随机重新初始化中心")

        return centroids

    def _compute_wcss(self, X, labels, centroids):
        """
        计算簇内平方和 (Within-Cluster Sum of Squares)

        参数:
            X: 数据矩阵
            labels: 簇标签数组
            centroids: 簇中心矩阵

        返回:
            WCSS 值
        """
        wcss = 0.0

        for k in range(self.n_clusters):
            # 获取属于当前簇的数据点
            cluster_points = X[labels == k]

            if len(cluster_points) > 0:
                # 计算每个点到中心的距离平方
                distances = self._distance_func(cluster_points, centroids[k])
                wcss += np.sum(distances ** 2)

        return wcss

    def fit(self, X):
        """
        训练模型

        参数:
            X: 训练数据，形状 (n_samples, n_features)

        返回:
            self
        """
        # 验证输入
        X = self._validate_input(X)
        n_samples = X.shape[0]

        # 验证 K 值
        if self.n_clusters <= 0:
            raise ValueError("n_clusters 必须大于 0")
        if self.n_clusters > n_samples:
            raise ValueError(f"n_clusters ({self.n_clusters}) 不能大于样本数 ({n_samples})")

        # 初始化簇中心
        centroids = self._init_centroids(X)

        # 迭代优化
        for iteration in range(self.max_iter):
            # 保存旧的中心点用于收敛判断
            old_centroids = centroids.copy()

            # 分配簇
            labels = self._assign_clusters(X, centroids)

            # 更新中心
            centroids = self._update_centroids(X, labels)

            # 收敛判断
            centroid_shift = np.max(np.linalg.norm(centroids - old_centroids, axis=1))

            if centroid_shift < self.tol:
                self.n_iter_ = iteration + 1
                break
        else:
            self.n_iter_ = self.max_iter
            warnings.warn(f"算法未在 {self.max_iter} 次迭代内收敛")

        # 保存结果
        self.cluster_centers_ = centroids
        self.labels_ = labels
        self.inertia_ = self._compute_wcss(X, labels, centroids)

        return self

    def predict(self, X):
        """
        预测簇标签

        参数:
            X: 数据矩阵，形状 (n_samples, n_features)

        返回:
            簇标签数组
        """
        if self.cluster_centers_ is None:
            raise ValueError("模型尚未训练，请先调用 fit() 方法")

        X = self._validate_input(X)

        return self._assign_clusters(X, self.cluster_centers_)

    def fit_predict(self, X):
        """
        训练并预测

        参数:
            X: 数据矩阵，形状 (n_samples, n_features)

        返回:
            簇标签数组
        """
        self.fit(X)
        return self.labels_

    def score(self, X):
        """
        计算模型得分（负的 WCSS）

        参数:
            X: 数据矩阵

        返回:
            得分值（负数，越大越好）
        """
        if self.cluster_centers_ is None:
            raise ValueError("模型尚未训练，请先调用 fit() 方法")

        X = self._validate_input(X)
        labels = self.predict(X)

        return -self._compute_wcss(X, labels, self.cluster_centers_)

    def get_params(self):
        """获取模型参数"""
        return {
            'n_clusters': self.n_clusters,
            'max_iter': self.max_iter,
            'tol': self.tol,
            'distance': self.distance,
            'init': self.init,
            'random_state': self.random_state
        }

    def set_params(self, **params):
        """设置模型参数"""
        for key, value in params.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise ValueError(f"无效参数: {key}")

        # 更新距离函数
        if 'distance' in params:
            self._distance_func = get_distance_function(params['distance'])

        return self