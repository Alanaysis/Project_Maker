"""
距离度量模块

提供多种距离计算方法，用于 K-Means 聚类算法。
"""

import numpy as np


def euclidean_distance(x, y):
    """
    计算欧氏距离

    参数:
        x: 第一个向量或矩阵
        y: 第二个向量或矩阵

    返回:
        欧氏距离值或距离数组
    """
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)

    # 处理单个向量
    if x.ndim == 1 and y.ndim == 1:
        return np.sqrt(np.sum((x - y) ** 2))

    # 处理矩阵（批量计算）
    if x.ndim == 2 and y.ndim == 1:
        return np.sqrt(np.sum((x - y) ** 2, axis=1))

    if x.ndim == 1 and y.ndim == 2:
        return np.sqrt(np.sum((x - y) ** 2, axis=1))

    if x.ndim == 2 and y.ndim == 2:
        return np.sqrt(np.sum((x[:, np.newaxis, :] - y[np.newaxis, :, :]) ** 2, axis=2))

    raise ValueError("输入维度不匹配")


def manhattan_distance(x, y):
    """
    计算曼哈顿距离

    参数:
        x: 第一个向量或矩阵
        y: 第二个向量或矩阵

    返回:
        曼哈顿距离值或距离数组
    """
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)

    # 处理单个向量
    if x.ndim == 1 and y.ndim == 1:
        return np.sum(np.abs(x - y))

    # 处理矩阵（批量计算）
    if x.ndim == 2 and y.ndim == 1:
        return np.sum(np.abs(x - y), axis=1)

    if x.ndim == 1 and y.ndim == 2:
        return np.sum(np.abs(x - y), axis=1)

    if x.ndim == 2 and y.ndim == 2:
        return np.sum(np.abs(x[:, np.newaxis, :] - y[np.newaxis, :, :]), axis=2)

    raise ValueError("输入维度不匹配")


def cosine_distance(x, y):
    """
    计算余弦距离

    参数:
        x: 第一个向量或矩阵
        y: 第二个向量或矩阵

    返回:
        余弦距离值或距离数组（1 - 余弦相似度）
    """
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)

    def _cosine_sim(a, b):
        """计算两个向量的余弦相似度"""
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    # 处理单个向量
    if x.ndim == 1 and y.ndim == 1:
        return 1 - _cosine_sim(x, y)

    # 处理矩阵（批量计算）
    if x.ndim == 2 and y.ndim == 1:
        return np.array([1 - _cosine_sim(xi, y) for xi in x])

    if x.ndim == 1 and y.ndim == 2:
        return np.array([1 - _cosine_sim(x, yi) for yi in y])

    if x.ndim == 2 and y.ndim == 2:
        result = np.zeros((x.shape[0], y.shape[0]))
        for i in range(x.shape[0]):
            for j in range(y.shape[0]):
                result[i, j] = 1 - _cosine_sim(x[i], y[j])
        return result

    raise ValueError("输入维度不匹配")


# 距离函数映射
DISTANCE_FUNCTIONS = {
    'euclidean': euclidean_distance,
    'manhattan': manhattan_distance,
    'cosine': cosine_distance
}


def get_distance_function(name):
    """
    根据名称获取距离函数

    参数:
        name: 距离函数名称 ('euclidean', 'manhattan', 'cosine')

    返回:
        距离函数
    """
    if name not in DISTANCE_FUNCTIONS:
        raise ValueError(f"不支持的距离函数: {name}。支持的函数: {list(DISTANCE_FUNCTIONS.keys())}")

    return DISTANCE_FUNCTIONS[name]


def pairwise_distances(X, Y=None, metric='euclidean'):
    """
    计算两组数据之间的成对距离

    参数:
        X: 第一组数据，形状 (n_samples_x, n_features)
        Y: 第二组数据，形状 (n_samples_y, n_features)，默认为 X
        metric: 距离度量方式

    返回:
        距离矩阵，形状 (n_samples_x, n_samples_y)
    """
    if Y is None:
        Y = X

    distance_func = get_distance_function(metric)

    if metric == 'euclidean':
        # 使用高效的向量化计算
        X = np.asarray(X, dtype=np.float64)
        Y = np.asarray(Y, dtype=np.float64)

        # 计算 ||x - y||^2 = ||x||^2 + ||y||^2 - 2 * x·y
        XX = np.sum(X ** 2, axis=1)[:, np.newaxis]
        YY = np.sum(Y ** 2, axis=1)[np.newaxis, :]
        distances = np.sqrt(np.maximum(XX + YY - 2 * np.dot(X, Y.T), 0))

        return distances

    return distance_func(X, Y)