"""梯度下降家族 - 各种梯度下降优化算法实现"""

__version__ = "0.2.0"

from .optimizers import (
    BGD, MiniBatchBGD, SGD, Momentum, NesterovMomentum,
    AdaGrad, RMSProp, Adam, AdamW, Nadam
)
from .schedulers import StepLR, ExponentialLR, CosineAnnealingLR, WarmupScheduler
from .functions import QuadraticFunction, RosenbrockFunction, HimmelblauFunction
from .visualizer import ContourPlotter, TrajectoryPlotter

__all__ = [
    'BGD', 'MiniBatchBGD', 'SGD', 'Momentum', 'NesterovMomentum',
    'AdaGrad', 'RMSProp', 'Adam', 'AdamW', 'Nadam',
    'StepLR', 'ExponentialLR', 'CosineAnnealingLR', 'WarmupScheduler',
    'QuadraticFunction', 'RosenbrockFunction', 'HimmelblauFunction',
    'ContourPlotter', 'TrajectoryPlotter'
]
