"""线性回归模块

从零实现线性回归，涵盖基础回归、正则化、优化算法、特征工程等核心技术。
"""

from .model import LinearRegression, RidgeRegression, LassoRegression, ElasticNet
from .losses import MSELoss, MAELoss, RMSELoss
from .optimizers import (
    BatchGradientDescent,
    StochasticGradientDescent,
    MiniBatchGradientDescent,
    LearningRateScheduler,
)
from .feature_engineering import (
    StandardScaler,
    MinMaxScaler,
    PolynomialFeatures,
    FeatureSelector,
    cross_validation,
)
from .evaluation import (
    mean_squared_error,
    root_mean_squared_error,
    mean_absolute_error,
    r2_score,
)
from .utils import (
    generate_linear_data,
    train_test_split,
    plot_loss_curve,
    plot_regression_line,
    plot_training_process,
)

__version__ = "0.2.0"
__all__ = [
    # Models
    "LinearRegression",
    "RidgeRegression",
    "LassoRegression",
    "ElasticNet",
    # Losses
    "MSELoss",
    "MAELoss",
    "RMSELoss",
    # Optimizers
    "BatchGradientDescent",
    "StochasticGradientDescent",
    "MiniBatchGradientDescent",
    "LearningRateScheduler",
    # Feature Engineering
    "StandardScaler",
    "MinMaxScaler",
    "PolynomialFeatures",
    "FeatureSelector",
    "cross_validation",
    # Evaluation
    "mean_squared_error",
    "root_mean_squared_error",
    "mean_absolute_error",
    "r2_score",
    # Utils
    "generate_linear_data",
    "train_test_split",
    "plot_loss_curve",
    "plot_regression_line",
    "plot_training_process",
]
