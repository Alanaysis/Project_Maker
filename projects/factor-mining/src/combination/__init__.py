"""因子组合模块 - 提供等权、IC加权、最优化、机器学习组合方法。"""

from src.combination.equal_weight import EqualWeightCombination
from src.combination.ic_weight import ICWeightCombination
from src.combination.optimized import OptimizedCombination
from src.combination.ml_combination import MLCombination

__all__ = ["EqualWeightCombination", "ICWeightCombination",
           "OptimizedCombination", "MLCombination"]
