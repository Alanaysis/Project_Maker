"""
遗传算法框架
"""

from .core import Individual, Population, GAEngine, MultiObjectiveProblem, NSGA2Engine
from .operators import (
    SelectionOperator,
    RouletteWheelSelection,
    TournamentSelection,
    ElitismSelection,
    CrossoverOperator,
    SinglePointCrossover,
    TwoPointCrossover,
    OrderCrossover,
    UniformCrossover,
    ArithmeticCrossover,
    MutationOperator,
    BitFlipMutation,
    SwapMutation,
    InversionMutation,
    GaussianMutation,
    AdaptiveMutation,
)
from .problems import (
    Problem,
    TSPProblem,
    SphereProblem,
    RastriginProblem,
    RosenbrockProblem,
    AckleyProblem,
    GriewankProblem,
    KnapsackProblem,
    MultiKnapsackProblem,
)

__version__ = "2.0.0"
__all__ = [
    # Core
    "Individual",
    "Population",
    "GAEngine",
    "MultiObjectiveProblem",
    "NSGA2Engine",
    # Selection
    "SelectionOperator",
    "RouletteWheelSelection",
    "TournamentSelection",
    "ElitismSelection",
    # Crossover
    "CrossoverOperator",
    "SinglePointCrossover",
    "TwoPointCrossover",
    "OrderCrossover",
    "UniformCrossover",
    "ArithmeticCrossover",
    # Mutation
    "MutationOperator",
    "BitFlipMutation",
    "SwapMutation",
    "InversionMutation",
    "GaussianMutation",
    "AdaptiveMutation",
    # Problems
    "Problem",
    "TSPProblem",
    "SphereProblem",
    "RastriginProblem",
    "RosenbrockProblem",
    "AckleyProblem",
    "GriewankProblem",
    "KnapsackProblem",
    "MultiKnapsackProblem",
]
