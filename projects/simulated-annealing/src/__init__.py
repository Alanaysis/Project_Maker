"""
模拟退火优化算法库 (Simulated Annealing Optimization Library)

模拟退火算法受金属退火过程启发：
1. 高温时粒子运动自由（探索空间大）
2. 降温时逐渐稳定（收敛到最优解）
3. 最终在低温时找到低能量状态（最优/近优解）

核心概念：
- 温度 T：控制接受差解的概率
- 能量 E：目标函数的值（越小越好）
- 邻域搜索：在当前解附近寻找新解
- Metropolis 准则：以概率 exp(-ΔE/T) 接受差解
- 冷却Schedule：控制温度下降的速度
"""

from .core import SimulatedAnnealing, SAResult
from .temperature import (
    TemperatureScheduler,
    ExponentialScheduler,
    LinearScheduler,
    LogarithmicScheduler,
    AdaptiveScheduler,
)
from .acceptance import metropolis_criterion, boltzmann_acceptance
from .neighborhood import (
    neighborhood_generator,
    swap_neighbor,
    insert_neighbor,
    reverse_neighbor,
    multi_switch_neighbor,
    continuous_neighbor,
    adaptive_neighborhood,
)
from .cooling import CoolingSchedule, ExponentialCooling, LinearCooling
from .convergence import ConvergenceDetector, EarlyStopDetector
from .restart import RestartManager, DiversificationRestart

__all__ = [
    "SimulatedAnnealing",
    "SAResult",
    "TemperatureScheduler",
    "ExponentialScheduler",
    "LinearScheduler",
    "LogarithmicScheduler",
    "AdaptiveScheduler",
    "metropolis_criterion",
    "boltzmann_acceptance",
    "neighborhood_generator",
    "swap_neighbor",
    "insert_neighbor",
    "reverse_neighbor",
    "multi_switch_neighbor",
    "continuous_neighbor",
    "adaptive_neighborhood",
    "CoolingSchedule",
    "ExponentialCooling",
    "LinearCooling",
    "ConvergenceDetector",
    "EarlyStopDetector",
    "RestartManager",
    "DiversificationRestart",
]
