"""
距离度量模块

实现各种距离计算方法，用于 KNN 分类算法。
"""

import numpy as np
from typing import Union, Callable


class DistanceMetrics:
    """
    距离度量工具类

    提供多种距离计算方法，包括：
    - 欧氏距离 (Euclidean)
    - 曼哈顿距离 (Manhattan)
    - 闵可夫斯基距离 (Minkowski)
    - 余弦相似度 (Cosine)

    所有方法都是静态方法，无需实例化即可使用。
    """

    @staticmethod
    def euclidean(x1: np.ndarray, x2: np.ndarray) -> float:
        """
        计算欧氏距离

        公式: d(x, y) = sqrt(Σ(xi - yi)²)

        Args:
            x1: 第一个向量
            x2: 第二个向量

        Returns:
            欧氏距离值

        Examples:
            >>> DistanceMetrics.euclidean([0, 0], [3, 4])
            5.0
            >>> DistanceMetrics.euclidean([1, 2, 3], [4, 5, 6])
            5.196152422706632
        """
        x1 = np.asarray(x1, dtype=float)
        x2 = np.asarray(x2, dtype=float)

        # 验证输入维度
        if x1.shape != x2.shape:
            raise ValueError("Input vectors must have the same shape")

        return float(np.sqrt(np.sum((x1 - x2) ** 2)))

    @staticmethod
    def manhattan(x1: np.ndarray, x2: np.ndarray) -> float:
        """
        计算曼哈顿距离

        公式: d(x, y) = Σ|xi - yi|

        Args:
            x1: 第一个向量
            x2: 第二个向量

        Returns:
            曼哈顿距离值

        Examples:
            >>> DistanceMetrics.manhattan([0, 0], [3, 4])
            7
            >>> DistanceMetrics.manhattan([1, 2, 3], [4, 5, 6])
            9
        """
        x1 = np.asarray(x1, dtype=float)
        x2 = np.asarray(x2, dtype=float)

        # 验证输入维度
        if x1.shape != x2.shape:
            raise ValueError("Input vectors must have the same shape")

        return float(np.sum(np.abs(x1 - x2)))

    @staticmethod
    def minkowski(x1: np.ndarray, x2: np.ndarray, p: int = 2) -> float:
        """
        计算闵可夫斯基距离

        公式: d(x, y) = (Σ|xi - yi|^p)^(1/p)

        Args:
            x1: 第一个向量
            x2: 第二个向量
            p: 距离参数 (p=1: 曼哈顿, p=2: 欧氏)

        Returns:
            闵可夫斯基距离值

        Examples:
            >>> DistanceMetrics.minkowski([0, 0], [3, 4], p=1)
            7.0
            >>> DistanceMetrics.minkowski([0, 0], [3, 4], p=2)
            5.0
        """
        x1 = np.asarray(x1, dtype=float)
        x2 = np.asarray(x2, dtype=float)

        # 验证输入维度
        if x1.shape != x2.shape:
            raise ValueError("Input vectors must have the same shape")

        # 验证 p 值
        if p <= 0:
            raise ValueError("p must be positive")

        # 处理 p=inf 的情况（切比雪夫距离）
        if p == float('inf'):
            return float(np.max(np.abs(x1 - x2)))

        return float(np.sum(np.abs(x1 - x2) ** p) ** (1 / p))

    @staticmethod
    def cosine(x1: np.ndarray, x2: np.ndarray) -> float:
        """
        计算余弦相似度

        公式: similarity = (x·y) / (||x|| * ||y||)

        注意：返回的是相似度（0到1），不是距离。
        相似度越高，距离越近。

        Args:
            x1: 第一个向量
            x2: 第二个向量

        Returns:
            余弦相似度值 (0 到 1)

        Examples:
            >>> DistanceMetrics.cosine([1, 0], [1, 0])
            1.0
            >>> DistanceMetrics.cosine([1, 0], [0, 1])
            0.0
            >>> DistanceMetrics.cosine([1, 0], [-1, 0])
            -1.0
        """
        x1 = np.asarray(x1, dtype=float)
        x2 = np.asarray(x2, dtype=float)

        # 验证输入维度
        if x1.shape != x2.shape:
            raise ValueError("Input vectors must have the same shape")

        # 计算点积
        dot_product = np.dot(x1, x2)

        # 计算范数
        norm_x1 = np.linalg.norm(x1)
        norm_x2 = np.linalg.norm(x2)

        # 处理零向量
        if norm_x1 == 0 or norm_x2 == 0:
            return 0.0

        return float(dot_product / (norm_x1 * norm_x2))

    @staticmethod
    def cosine_distance(x1: np.ndarray, x2: np.ndarray) -> float:
        """
        计算余弦距离

        公式: distance = 1 - cosine_similarity

        Args:
            x1: 第一个向量
            x2: 第二个向量

        Returns:
            余弦距离值 (0 到 2)

        Examples:
            >>> DistanceMetrics.cosine_distance([1, 0], [1, 0])
            0.0
            >>> DistanceMetrics.cosine_distance([1, 0], [0, 1])
            1.0
        """
        return 1 - DistanceMetrics.cosine(x1, x2)

    @staticmethod
    def get_metric(name: str) -> Callable:
        """
        根据名称获取距离函数

        Args:
            name: 距离度量名称
                - 'euclidean': 欧氏距离
                - 'manhattan': 曼哈顿距离
                - 'minkowski': 闵可夫斯基距离
                - 'cosine': 余弦相似度（转换为距离）

        Returns:
            距离计算函数

        Raises:
            ValueError: 不支持的距离度量

        Examples:
            >>> metric_func = DistanceMetrics.get_metric('euclidean')
            >>> metric_func([0, 0], [3, 4])
            5.0
        """
        metrics = {
            'euclidean': DistanceMetrics.euclidean,
            'manhattan': DistanceMetrics.manhattan,
            'minkowski': DistanceMetrics.minkowski,
            'cosine': DistanceMetrics.cosine_distance,
        }

        if name not in metrics:
            raise ValueError(
                f"Unsupported metric: {name}. "
                f"Supported metrics: {list(metrics.keys())}"
            )

        return metrics[name]

    @staticmethod
    def compute_distance(x1: np.ndarray, x2: np.ndarray,
                         metric: str = 'euclidean', **kwargs) -> float:
        """
        计算两个向量之间的距离

        Args:
            x1: 第一个向量
            x2: 第二个向量
            metric: 距离度量方式
            **kwargs: 额外参数（如 minkowski 的 p 参数）

        Returns:
            距离值

        Examples:
            >>> DistanceMetrics.compute_distance([0, 0], [3, 4], 'euclidean')
            5.0
            >>> DistanceMetrics.compute_distance([0, 0], [3, 4], 'minkowski', p=1)
            7.0
        """
        metric_func = DistanceMetrics.get_metric(metric)

        # 处理需要额外参数的度量
        if metric == 'minkowski':
            p = kwargs.get('p', 2)
            return metric_func(x1, x2, p=p)
        else:
            return metric_func(x1, x2)


# 便捷函数
def euclidean_distance(x1, x2):
    """计算欧氏距离的便捷函数"""
    return DistanceMetrics.euclidean(x1, x2)


def manhattan_distance(x1, x2):
    """计算曼哈顿距离的便捷函数"""
    return DistanceMetrics.manhattan(x1, x2)


def minkowski_distance(x1, x2, p=2):
    """计算闵可夫斯基距离的便捷函数"""
    return DistanceMetrics.minkowski(x1, x2, p)


def cosine_similarity(x1, x2):
    """计算余弦相似度的便捷函数"""
    return DistanceMetrics.cosine(x1, x2)


def cosine_dist(x1, x2):
    """计算余弦距离的便捷函数"""
    return DistanceMetrics.cosine_distance(x1, x2)