"""
状态空间模型库

实现状态空间表示、状态估计、可控性/可观性分析
"""

from .state_space_model import StateSpaceModel, ContinuousStateSpace
from .kalman_filter import KalmanFilter
from .analysis import (
    controllability_matrix,
    observability_matrix,
    is_controllable,
    is_observable,
    check_stability_continuous,
    check_stability_discrete,
    stability_margin,
    controllability_index,
    observability_index,
    gramian_controllability,
    gramian_observability,
    decompose_controllable,
)
from .controller import StateFeedbackController, LQRController, LQGController
from .observer import FullOrderObserver, ReducedOrderObserver, LuenbergerObserver
from .applications import InvertedPendulum, DCmotor

__version__ = "2.0.0"
__all__ = [
    # 状态空间模型
    "StateSpaceModel",
    "ContinuousStateSpace",
    # 卡尔曼滤波
    "KalmanFilter",
    # 系统分析
    "controllability_matrix",
    "observability_matrix",
    "is_controllable",
    "is_observable",
    "check_stability_continuous",
    "check_stability_discrete",
    "stability_margin",
    "controllability_index",
    "observability_index",
    "gramian_controllability",
    "gramian_observability",
    "decompose_controllable",
    # 控制器
    "StateFeedbackController",
    "LQRController",
    "LQGController",
    # 观测器
    "FullOrderObserver",
    "ReducedOrderObserver",
    "LuenbergerObserver",
    # 实际应用
    "InvertedPendulum",
    "DCmotor",
]
