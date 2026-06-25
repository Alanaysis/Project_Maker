"""
模拟退火算法包

提供模拟退火优化算法的完整实现，包括：
- 核心算法（温度调度、Metropolis准则）
- 邻域操作（交换、逆序、插入）
- TSP旅行商问题
- 函数优化
- 调度问题
- 可视化工具
"""

from .simulated_annealing import SimulatedAnnealing, SAConfig, CoolingSchedule
from .neighborhood import NeighborhoodOps
from .tsp import TSP, City
from .function_optimization import (
    TestFunctions,
    ContinuousNeighbor,
    get_function_specs,
    FunctionSpec
)
from .scheduling import (
    JobShopScheduling,
    FlowShopScheduling,
    SingleMachineScheduling,
    ObjectiveType
)
from .visualization import (
    plot_convergence,
    plot_tsp_path,
    plot_optimization_animation,
    plot_cooling_schedules
)

__version__ = "2.0.0"
__all__ = [
    # 核心算法
    'SimulatedAnnealing',
    'SAConfig',
    'CoolingSchedule',
    # 邻域操作
    'NeighborhoodOps',
    # TSP
    'TSP',
    'City',
    # 函数优化
    'TestFunctions',
    'ContinuousNeighbor',
    'get_function_specs',
    'FunctionSpec',
    # 调度问题
    'JobShopScheduling',
    'FlowShopScheduling',
    'SingleMachineScheduling',
    'ObjectiveType',
    # 可视化
    'plot_convergence',
    'plot_tsp_path',
    'plot_optimization_animation',
    'plot_cooling_schedules',
]
