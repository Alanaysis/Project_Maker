"""
K-Means 聚类算法实现

从零实现 K-Means 聚类算法，支持多种距离度量和初始化方法。
包括标准 K-Means 和 Mini-Batch K-Means。
"""

from .kmeans import KMeans, MiniBatchKMeans
from .distance import euclidean_distance, manhattan_distance, cosine_distance, pairwise_distances
from .visualization import plot_clusters, plot_elbow, plot_2d_clusters, plot_3d_clusters
from .utils import (
    generate_clustered_data,
    normalize_data,
    compute_wcss,
    compute_silhouette_score,
    compute_silhouette_score_fast,
    compute_calinski_harabasz,
    evaluate_clustering,
    find_optimal_k_elbow,
    cluster_statistics
)

__version__ = "2.0.0"
__author__ = "Learning Project"

__all__ = [
    # 核心算法
    'KMeans',
    'MiniBatchKMeans',
    # 距离函数
    'euclidean_distance',
    'manhattan_distance',
    'cosine_distance',
    'pairwise_distances',
    # 可视化
    'plot_clusters',
    'plot_elbow',
    'plot_2d_clusters',
    'plot_3d_clusters',
    # 工具函数
    'generate_clustered_data',
    'normalize_data',
    'compute_wcss',
    'compute_silhouette_score',
    'compute_silhouette_score_fast',
    'compute_calinski_harabasz',
    'evaluate_clustering',
    'find_optimal_k_elbow',
    'cluster_statistics'
]