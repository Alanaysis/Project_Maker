"""
模糊控制器 (Fuzzy Controller) 包

实现模糊逻辑控制系统，包括：
- 模糊集合和隶属函数 (三角/梯形/高斯/钟形)
- 模糊化和去模糊化 (重心法/最大隶属度法)
- 模糊规则引擎 (IF-THEN 规则库)
- 推理引擎 (Mamdani / Sugeno)
- 实际应用 (温度控制 / 速度控制)
"""

from .fuzzy_set import (
    FuzzySet,
    MembershipFunction,
    TriangularMF,
    TrapezoidalMF,
    GaussianMF,
    BellShapedMF,
)
from .fuzzifier import Fuzzifier
from .rule_engine import RuleEngine, FuzzyRule
from .defuzzifier import Defuzzifier
from .controller import FuzzyController
from .applications import TemperatureController, SpeedController

__version__ = "1.0.0"
__all__ = [
    "FuzzySet",
    "MembershipFunction",
    "TriangularMF",
    "TrapezoidalMF",
    "GaussianMF",
    "BellShapedMF",
    "Fuzzifier",
    "RuleEngine",
    "FuzzyRule",
    "Defuzzifier",
    "FuzzyController",
    "TemperatureController",
    "SpeedController",
]
