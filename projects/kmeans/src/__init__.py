"""
K-Means 聚类算法实现

从零实现 K-Means 聚类算法，支持多种距离度量和初始化方法。
"""

from .kmeans import KMeans
from .distance import euclidean_distance, manhattan_distance, cosine_distance
from .visualization import plot_clusters, plot_elbow, plot_2d_clusters, plot_3d_clusters
from .utils import generate_clustered_data, normalize_data, compute_wcss

__version__ = "1.0.0"
__author__ = "Learning Project"

__all__ = [
    'KMeans',
    'euclidean_distance',
    'manhattan_distance',
    'cosine_distance',
    'plot_clusters',
    'plot_elbow',
    'plot_2d_clusters',
    'plot_3d_clusters',
    'generate_clustered_data',
    'normalize_data',
    'compute_wcss'
]