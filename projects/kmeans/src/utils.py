"""
工具函数模块

提供 K-Means 聚类相关的辅助功能，包括评估指标和数据生成。
"""

import numpy as np
from .distance import pairwise_distances


def generate_clustered_data(n_samples=300, n_clusters=4, n_features=2,
                            cluster_std=1.0, random_state=None):
    """
    生成聚类测试数据

    参数:
        n_samples: 样本数量，默认为 300
        n_clusters: 簇数量，默认为 4
        n_features: 特征数量，默认为 2
        cluster_std: 簇的标准差，默认为 1.0
        random_state: 随机种子，默认为 None

    返回:
        X: 数据矩阵，形状 (n_samples, n_features)
        y: 真实标签，形状 (n_samples,)
    """
    rng = np.random.RandomState(random_state)

    # 每个簇的样本数
    samples_per_cluster = n_samples // n_clusters
    remainder = n_samples % n_clusters

    # 生成簇中心
    centers = rng.randn(n_clusters, n_features) * 10

    # 生成数据
    X = []
    y = []

    for i in range(n_clusters):
        # 当前簇的样本数
        n = samples_per_cluster + (1 if i < remainder else 0)

        # 生成当前簇的数据
        cluster_data = rng.randn(n, n_features) * cluster_std + centers[i]

        X.append(cluster_data)
        y.extend([i] * n)

    X = np.vstack(X)
    y = np.array(y)

    # 随机打乱数据
    indices = rng.permutation(n_samples)
    X = X[indices]
    y = y[indices]

    return X, y


def normalize_data(X):
    """
    数据标准化（Z-score）

    参数:
        X: 数据矩阵，形状 (n_samples, n_features)

    返回:
        X_normalized: 标准化后的数据
        mean: 均值
        std: 标准差
    """
    X = np.asarray(X, dtype=np.float64)

    mean = np.mean(X, axis=0)
    std = np.std(X, axis=0)

    # 避免除以零
    std[std == 0] = 1.0

    X_normalized = (X - mean) / std

    return X_normalized, mean, std


def compute_wcss(X, labels, centroids, distance_func=None):
    """
    计算簇内平方和 (Within-Cluster Sum of Squares)

    参数:
        X: 数据矩阵，形状 (n_samples, n_features)
        labels: 簇标签数组
        centroids: 簇中心矩阵，形状 (n_clusters, n_features)
        distance_func: 距离函数，默认为欧氏距离

    返回:
        wcss: 簇内平方和
    """
    X = np.asarray(X, dtype=np.float64)
    labels = np.asarray(labels)
    centroids = np.asarray(centroids, dtype=np.float64)

    if distance_func is None:
        distance_func = lambda x, y: np.sqrt(np.sum((x - y) ** 2, axis=1))

    wcss = 0.0
    n_clusters = len(centroids)

    for k in range(n_clusters):
        # 获取属于当前簇的数据点
        cluster_points = X[labels == k]

        if len(cluster_points) > 0:
            # 计算每个点到中心的距离平方
            distances = distance_func(cluster_points, centroids[k])
            wcss += np.sum(distances ** 2)

    return wcss


def compute_silhouette_score(X, labels, distance_func=None):
    """
    计算轮廓系数

    参数:
        X: 数据矩阵，形状 (n_samples, n_features)
        labels: 簇标签数组
        distance_func: 距离函数，默认为欧氏距离

    返回:
        silhouette_score: 平均轮廓系数
    """
    X = np.asarray(X, dtype=np.float64)
    labels = np.asarray(labels)
    n_samples = X.shape[0]

    if distance_func is None:
        distance_func = lambda x, y: np.sqrt(np.sum((x - y) ** 2))

    unique_labels = np.unique(labels)
    n_clusters = len(unique_labels)

    if n_clusters <= 1:
        return 0.0

    # 计算每个样本的轮廓系数
    silhouette_values = np.zeros(n_samples)

    for i in range(n_samples):
        # 当前样本所属的簇
        current_label = labels[i]

        # 计算 a(i): 同簇内其他样本的平均距离
        same_cluster_mask = (labels == current_label)
        same_cluster_mask[i] = False  # 排除自身

        if np.any(same_cluster_mask):
            a_i = np.mean([distance_func(X[i], X[j]) for j in np.where(same_cluster_mask)[0]])
        else:
            a_i = 0.0

        # 计算 b(i): 最近簇中所有样本的平均距离
        b_i = np.inf

        for label in unique_labels:
            if label == current_label:
                continue

            other_cluster_mask = (labels == label)
            if np.any(other_cluster_mask):
                avg_distance = np.mean([distance_func(X[i], X[j])
                                        for j in np.where(other_cluster_mask)[0]])
                b_i = min(b_i, avg_distance)

        # 计算轮廓系数
        if max(a_i, b_i) > 0:
            silhouette_values[i] = (b_i - a_i) / max(a_i, b_i)
        else:
            silhouette_values[i] = 0.0

    return np.mean(silhouette_values)


def find_optimal_k_elbow(X, k_range=None, max_k=10, distance='euclidean', random_state=None):
    """
    使用肘部法则寻找最优 K 值

    参数:
        X: 数据矩阵
        k_range: K 值范围，默认为 range(1, max_k+1)
        max_k: 最大 K 值，默认为 10
        distance: 距离度量方式
        random_state: 随机种子

    返回:
        optimal_k: 最优 K 值
        wcss_list: 不同 K 值对应的 WCSS
    """
    from .kmeans import KMeans

    X = np.asarray(X, dtype=np.float64)

    if k_range is None:
        max_k = min(max_k, X.shape[0])
        k_range = range(1, max_k + 1)

    wcss_list = []

    for k in k_range:
        if k == 0:
            wcss_list.append(0)
            continue

        kmeans = KMeans(n_clusters=k, distance=distance, random_state=random_state)
        kmeans.fit(X)
        wcss_list.append(kmeans.inertia_)

    # 使用肘部法则寻找最优 K
    # 计算二阶差分
    if len(wcss_list) >= 3:
        # 计算一阶差分
        first_diff = np.diff(wcss_list)
        # 计算二阶差分
        second_diff = np.diff(first_diff)

        # 最优 K 是二阶差分最大的点
        optimal_idx = np.argmax(second_diff) + 2  # +2 因为 diff 减少了两个索引
        optimal_k = k_range[optimal_idx]
    else:
        optimal_k = k_range[0]

    return optimal_k, list(k_range), wcss_list


def cluster_statistics(X, labels, centroids):
    """
    计算聚类统计信息

    参数:
        X: 数据矩阵
        labels: 簇标签数组
        centroids: 簇中心矩阵

    返回:
        stats: 统计信息字典
    """
    X = np.asarray(X, dtype=np.float64)
    labels = np.asarray(labels)
    centroids = np.asarray(centroids, dtype=np.float64)

    unique_labels = np.unique(labels)
    n_clusters = len(unique_labels)

    stats = {
        'n_clusters': n_clusters,
        'n_samples': X.shape[0],
        'n_features': X.shape[1],
        'cluster_sizes': {},
        'cluster_centers': centroids,
        'cluster_densities': {},
        'total_wcss': 0.0
    }

    for k in unique_labels:
        cluster_points = X[labels == k]
        stats['cluster_sizes'][int(k)] = len(cluster_points)

        # 计算簇密度（平均距离）
        if len(cluster_points) > 0:
            distances = np.sqrt(np.sum((cluster_points - centroids[k]) ** 2, axis=1))
            stats['cluster_densities'][int(k)] = float(np.mean(distances))
            stats['total_wcss'] += float(np.sum(distances ** 2))

    return stats


def compute_calinski_harabasz(X, labels):
    """
    计算 Calinski-Harabasz 指数（方差比准则）

    该指标衡量簇间分散度与簇内分散度的比值，值越大表示聚类效果越好。

    公式:
        CH = (B(k) / (k-1)) / (W(k) / (n-k))

    其中:
        B(k) = 簇间离散度（between-cluster dispersion）
        W(k) = 簇内离散度（within-cluster dispersion）
        k = 簇的数量
        n = 样本数量

    参数:
        X: 数据矩阵，形状 (n_samples, n_features)
        labels: 簇标签数组

    返回:
        ch_score: Calinski-Harabasz 指数值（越大越好）
    """
    X = np.asarray(X, dtype=np.float64)
    labels = np.asarray(labels)

    n_samples = X.shape[0]
    n_features = X.shape[1]
    unique_labels = np.unique(labels)
    n_clusters = len(unique_labels)

    # 边界情况
    if n_clusters <= 1 or n_clusters >= n_samples:
        return 0.0

    # 计算全局中心
    global_center = np.mean(X, axis=0)

    # 计算簇间离散度 (Between-Cluster Dispersion)
    between_dispersion = 0.0
    for k in unique_labels:
        cluster_points = X[labels == k]
        n_k = len(cluster_points)
        if n_k > 0:
            cluster_center = np.mean(cluster_points, axis=0)
            # 簇中心到全局中心的距离平方乘以簇大小
            between_dispersion += n_k * np.sum((cluster_center - global_center) ** 2)

    # 计算簇内离散度 (Within-Cluster Dispersion)
    within_dispersion = 0.0
    for k in unique_labels:
        cluster_points = X[labels == k]
        if len(cluster_points) > 0:
            cluster_center = np.mean(cluster_points, axis=0)
            # 簇内各点到簇中心的距离平方和
            within_dispersion += np.sum((cluster_points - cluster_center) ** 2)

    # 计算 Calinski-Harabasz 指数
    if within_dispersion == 0:
        return 0.0

    ch_score = (between_dispersion / (n_clusters - 1)) / (within_dispersion / (n_samples - n_clusters))

    return ch_score


def compute_silhouette_score_fast(X, labels):
    """
    计算轮廓系数（优化版本）

    轮廓系数衡量样本与自身簇和其他簇的相似度，值范围 [-1, 1]，
    值越大表示聚类效果越好。

    参数:
        X: 数据矩阵，形状 (n_samples, n_features)
        labels: 簇标签数组

    返回:
        silhouette_score: 平均轮廓系数
    """
    X = np.asarray(X, dtype=np.float64)
    labels = np.asarray(labels)
    n_samples = X.shape[0]

    unique_labels = np.unique(labels)
    n_clusters = len(unique_labels)

    if n_clusters <= 1 or n_clusters >= n_samples:
        return 0.0

    # 预计算距离矩阵
    distances = pairwise_distances(X, metric='euclidean')

    silhouette_values = np.zeros(n_samples)

    for i in range(n_samples):
        current_label = labels[i]

        # 计算 a(i): 同簇内其他样本的平均距离
        same_cluster_mask = (labels == current_label)
        same_cluster_mask[i] = False

        if np.any(same_cluster_mask):
            a_i = np.mean(distances[i, same_cluster_mask])
        else:
            a_i = 0.0

        # 计算 b(i): 最近簇中所有样本的平均距离
        b_i = np.inf

        for label in unique_labels:
            if label == current_label:
                continue

            other_cluster_mask = (labels == label)
            if np.any(other_cluster_mask):
                avg_distance = np.mean(distances[i, other_cluster_mask])
                b_i = min(b_i, avg_distance)

        # 计算轮廓系数
        if max(a_i, b_i) > 0:
            silhouette_values[i] = (b_i - a_i) / max(a_i, b_i)
        else:
            silhouette_values[i] = 0.0

    return np.mean(silhouette_values)


def evaluate_clustering(X, labels, method='all'):
    """
    综合评估聚类结果

    参数:
        X: 数据矩阵
        labels: 簇标签数组
        method: 评估方法，'all', 'silhouette', 'calinski_harabasz'

    返回:
        metrics: 评估指标字典
    """
    X = np.asarray(X, dtype=np.float64)
    labels = np.asarray(labels)

    metrics = {}

    if method in ['all', 'silhouette']:
        metrics['silhouette_score'] = compute_silhouette_score_fast(X, labels)

    if method in ['all', 'calinski_harabasz']:
        metrics['calinski_harabasz'] = compute_calinski_harabasz(X, labels)

    if method == 'all':
        metrics['n_clusters'] = len(np.unique(labels))
        metrics['n_samples'] = X.shape[0]

    return metrics