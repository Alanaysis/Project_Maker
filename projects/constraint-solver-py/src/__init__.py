"""
约束求解器 (Constraint Solver)
==============================

一个功能完整的约束满足问题 (CSP) 求解器，支持:
- 弧相容 (AC-3) 和路径相容
- 回溯搜索 + MRV + 度启发式
- AllDifferent、线性约束、表约束
- 数独、排课、N皇后等实际应用
"""

from .variable import Variable
from .domain import Domain
from .constraint import (
    Constraint,
    AllDifferentConstraint,
    LinearConstraint,
    TableConstraint,
)
from .propagation import AC3, PathConsistency
from .search import BacktrackingSearch
from .solver import CSPSolver

__version__ = "1.0.0"
__all__ = [
    "Variable",
    "Domain",
    "Constraint",
    "AllDifferentConstraint",
    "LinearConstraint",
    "TableConstraint",
    "AC3",
    "PathConsistency",
    "BacktrackingSearch",
    "CSPSolver",
]
