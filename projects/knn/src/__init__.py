"""
KNN 近邻分类器模块

实现 K-Nearest Neighbors 分类算法，支持多种距离度量。
"""

from .distance_metrics import DistanceMetrics
from .knn_classifier import KNNClassifier

__all__ = ['DistanceMetrics', 'KNNClassifier']