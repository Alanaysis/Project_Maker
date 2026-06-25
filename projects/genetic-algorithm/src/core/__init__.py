"""
核心模块：包含个体、种群、GA 引擎和多目标优化
"""

from .individual import Individual
from .population import Population
from .ga_engine import GAEngine
from .multi_objective import MultiObjectiveProblem, NSGA2Engine

__all__ = ["Individual", "Population", "GAEngine", "MultiObjectiveProblem", "NSGA2Engine"]
