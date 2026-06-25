"""
逻辑回归实现包

包含以下模块：
- logistic_regression: 基础逻辑回归
- multiclass: 多分类实现
- regularization: 正则化实现
- metrics: 评估指标
- feature_engineering: 特征工程
- optimizers: 优化算法
"""

from .logistic_regression import LogisticRegression
from .multiclass import OneVsRestClassifier, OneVsOneClassifier, SoftmaxRegression
from .regularization import LogisticRegressionL1, LogisticRegressionL2, ElasticNet
from .metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
    roc_curve,
    auc_score,
    precision_recall_curve,
    average_precision_score
)
from .feature_engineering import (
    StandardScaler,
    MinMaxScaler,
    VarianceThreshold,
    CorrelationThreshold,
    cross_validate,
    train_test_split
)
from .optimizers import (
    BatchGradientDescent,
    StochasticGradientDescent,
    MiniBatchGradientDescent,
    LearningRateScheduler,
    MomentumOptimizer,
    AdamOptimizer
)

__all__ = [
    # 基础逻辑回归
    'LogisticRegression',

    # 多分类
    'OneVsRestClassifier',
    'OneVsOneClassifier',
    'SoftmaxRegression',

    # 正则化
    'LogisticRegressionL1',
    'LogisticRegressionL2',
    'ElasticNet',

    # 评估指标
    'accuracy_score',
    'precision_score',
    'recall_score',
    'f1_score',
    'confusion_matrix',
    'classification_report',
    'roc_curve',
    'auc_score',
    'precision_recall_curve',
    'average_precision_score',

    # 特征工程
    'StandardScaler',
    'MinMaxScaler',
    'VarianceThreshold',
    'CorrelationThreshold',
    'cross_validate',
    'train_test_split',

    # 优化算法
    'BatchGradientDescent',
    'StochasticGradientDescent',
    'MiniBatchGradientDescent',
    'LearningRateScheduler',
    'MomentumOptimizer',
    'AdamOptimizer'
]
