"""
线性规划库 (Linear Programming Library)

核心模块：
- linear_program: 线性规划问题表示
- simplex: 单纯形法（标准、大M法、两阶段法）
- duality: 对偶理论与对偶单纯形法
- sensitivity: 敏感性分析
- applications: 实际应用（生产计划、运输、指派）
"""

from .linear_program import LinearProgram
from .simplex import SimplexSolver
from .duality import DualSimplexSolver
from .sensitivity import SensitivityAnalyzer
from .applications import ProductionPlanner, TransportationSolver, AssignmentSolver

__version__ = "1.0.0"
__all__ = [
    "LinearProgram",
    "SimplexSolver",
    "DualSimplexSolver",
    "SensitivityAnalyzer",
    "ProductionPlanner",
    "TransportationSolver",
    "AssignmentSolver",
]
