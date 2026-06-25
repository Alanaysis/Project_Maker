"""
KNN 近邻模块

实现 K-Nearest Neighbors 分类和回归算法，支持多种距离度量和加速结构。
"""

from .distance_metrics import DistanceMetrics
from .knn_classifier import KNNClassifier
from .knn_regressor import KNNRegressor
from .kd_tree import KDTree
from .ball_tree import BallTree
from .model_selection import (
    KFold,
    CrossValidator,
    train_test_split,
    accuracy_score,
    mean_squared_error,
    r2_score
)

__all__ = [
    'DistanceMetrics',
    'KNNClassifier',
    'KNNRegressor',
    'KDTree',
    'BallTree',
    'KFold',
    'CrossValidator',
    'train_test_split',
    'accuracy_score',
    'mean_squared_error',
    'r2_score'
]
