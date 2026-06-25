"""
MPC Controller - 模型预测控制算法实现

核心模块:
    - plant_model: 被控对象模型（状态空间、非线性系统）
    - models: 预测模型（状态空间模型、脉冲响应模型）
    - mpc_controller: MPC 控制器核心
    - optimizer: 优化求解器
    - qp_solver: QP 求解器（Hildreth、活动集）
    - feedback_correction: 反馈校正（误差预测、模型校正）
    - applications: 实际应用（温度控制、轨迹跟踪）
    - simulation: 仿真环境
"""

from .mpc_controller import MPCController, IncrementalMPCController, AdaptiveMPCController
from .plant_model import LinearPlantModel, NonlinearPlantModel
from .models import StateSpaceModel, ImpulseResponseModel
from .optimizer import MPCOptimizer
from .qp_solver import QPSolver, QPSolverType
from .feedback_correction import (
    FeedbackCorrection,
    CorrectionMethod,
    ErrorFeedbackCorrection,
    ModelAdaptiveCorrection,
    ExtendedStateCorrection,
    DisturbanceObserverCorrection,
)
from .applications import (
    TemperatureController,
    TrajectoryTracker,
    ThermalPlant,
    DubinsCar,
)
from .simulation import MPCSimulation

__all__ = [
    # 控制器
    "MPCController",
    "IncrementalMPCController",
    "AdaptiveMPCController",
    # 模型
    "LinearPlantModel",
    "NonlinearPlantModel",
    "StateSpaceModel",
    "ImpulseResponseModel",
    # 优化
    "MPCOptimizer",
    "QPSolver",
    "QPSolverType",
    # 反馈校正
    "FeedbackCorrection",
    "CorrectionMethod",
    "ErrorFeedbackCorrection",
    "ModelAdaptiveCorrection",
    "ExtendedStateCorrection",
    "DisturbanceObserverCorrection",
    # 应用
    "TemperatureController",
    "TrajectoryTracker",
    "ThermalPlant",
    "DubinsCar",
    # 仿真
    "MPCSimulation",
]
