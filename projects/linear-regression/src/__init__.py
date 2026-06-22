"""线性回归模块

从零实现线性回归，理解梯度下降。
"""

from .model import LinearRegression
from .losses import MSELoss, MAELoss
from .utils import (
    generate_linear_data,
    train_test_split,
    compute_r2_score,
    plot_loss_curve,
    plot_regression_line,
    plot_training_process,
)

__version__ = "0.1.0"
__all__ = [
    "LinearRegression",
    "MSELoss",
    "MAELoss",
    "generate_linear_data",
    "train_test_split",
    "compute_r2_score",
    "plot_loss_curve",
    "plot_regression_line",
    "plot_training_process",
]
