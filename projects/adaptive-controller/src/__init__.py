"""
自适应控制器 - Adaptive Controller

实现模型参考自适应控制 (MRAC)、自校正控制 (STR) 算法，
支持参数自动调整，包含温度控制和电机控制实际应用示例。

主要模块：
- adaptive_controller: 自适应控制器核心实现 (MRAC + STR)
- reference_model: 参考模型
- parameter_estimator: 参数估计器
- plant_model: 被控对象模型
- simulation: 仿真环境
- analyzer: 性能分析工具
"""

from .adaptive_controller import MRACController, SelfTuningController
from .reference_model import ReferenceModel
from .parameter_estimator import ParameterEstimator
from .plant_model import PlantModel
from .simulation import SimulationEngine
from .analyzer import PerformanceAnalyzer

__version__ = "2.0.0"
__all__ = [
    "MRACController",
    "SelfTuningController",
    "ReferenceModel",
    "ParameterEstimator",
    "PlantModel",
    "SimulationEngine",
    "PerformanceAnalyzer",
]
