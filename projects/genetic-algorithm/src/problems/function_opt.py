"""
函数优化问题：经典测试函数实现
"""

from typing import Any, List, Optional, Tuple
import random
import math

from .base import Problem


class SphereProblem(Problem):
    """
    Sphere 函数优化问题

    f(x) = sum(x_i^2)
    全局最优：x = [0, 0, ..., 0], f(x) = 0
    搜索范围：[-100, 100]^n
    """

    def __init__(self, dimensions: int = 3, range_min: float = -100.0, range_max: float = 100.0):
        self.dimensions = dimensions
        self.range_min = range_min
        self.range_max = range_max

    def create_individual(self) -> List[float]:
        return [random.uniform(self.range_min, self.range_max) for _ in range(self.dimensions)]

    def fitness(self, chromosome: List[float]) -> float:
        value = sum(x ** 2 for x in chromosome)
        return 1.0 / (1.0 + value)

    def objective(self, chromosome: List[float]) -> float:
        """目标函数值（最小化）"""
        return sum(x ** 2 for x in chromosome)

    def display(self, chromosome: List[float]) -> None:
        value = self.objective(chromosome)
        print(f"Solution: {[f'{x:.4f}' for x in chromosome]}")
        print(f"Objective value: {value:.6f}")


class RastriginProblem(Problem):
    """
    Rastrigin 函数优化问题

    f(x) = 10n + sum(x_i^2 - 10*cos(2*pi*x_i))
    全局最优：x = [0, 0, ..., 0], f(x) = 0
    搜索范围：[-5.12, 5.12]^n

    特点：具有大量局部最优，是典型的多模态测试函数
    """

    def __init__(self, dimensions: int = 3, range_min: float = -5.12, range_max: float = 5.12):
        self.dimensions = dimensions
        self.range_min = range_min
        self.range_max = range_max

    def create_individual(self) -> List[float]:
        return [random.uniform(self.range_min, self.range_max) for _ in range(self.dimensions)]

    def fitness(self, chromosome: List[float]) -> float:
        value = self.objective(chromosome)
        # Rastrigin 函数值 >= 0，使用倒数映射
        return 1.0 / (1.0 + value)

    def objective(self, chromosome: List[float]) -> float:
        """目标函数值（最小化）"""
        n = len(chromosome)
        return 10 * n + sum(x ** 2 - 10 * math.cos(2 * math.pi * x) for x in chromosome)

    def display(self, chromosome: List[float]) -> None:
        value = self.objective(chromosome)
        print(f"Solution: {[f'{x:.4f}' for x in chromosome]}")
        print(f"Objective value: {value:.6f}")


class RosenbrockProblem(Problem):
    """
    Rosenbrock 函数优化问题（香蕉函数）

    f(x) = sum(100 * (x_{i+1} - x_i^2)^2 + (1 - x_i)^2)
    全局最优：x = [1, 1, ..., 1], f(x) = 0
    搜索范围：[-5, 10]^n

    特点：全局最优位于一个狭长的抛物线形山谷中，难以收敛
    """

    def __init__(self, dimensions: int = 3, range_min: float = -5.0, range_max: float = 10.0):
        self.dimensions = dimensions
        self.range_min = range_min
        self.range_max = range_max

    def create_individual(self) -> List[float]:
        return [random.uniform(self.range_min, self.range_max) for _ in range(self.dimensions)]

    def fitness(self, chromosome: List[float]) -> float:
        value = self.objective(chromosome)
        return 1.0 / (1.0 + value)

    def objective(self, chromosome: List[float]) -> float:
        """目标函数值（最小化）"""
        total = 0.0
        for i in range(len(chromosome) - 1):
            total += 100 * (chromosome[i + 1] - chromosome[i] ** 2) ** 2 + (1 - chromosome[i]) ** 2
        return total

    def display(self, chromosome: List[float]) -> None:
        value = self.objective(chromosome)
        print(f"Solution: {[f'{x:.4f}' for x in chromosome]}")
        print(f"Objective value: {value:.6f}")


class AckleyProblem(Problem):
    """
    Ackley 函数优化问题

    f(x) = -20*exp(-0.2*sqrt(1/n * sum(x_i^2))) - exp(1/n * sum(cos(2*pi*x_i))) + 20 + e
    全局最优：x = [0, 0, ..., 0], f(x) = 0
    搜索范围：[-32.768, 32.768]^n

    特点：具有大量局部最优的多模态函数，搜索空间外部几乎平坦
    """

    def __init__(self, dimensions: int = 3, range_min: float = -32.768, range_max: float = 32.768):
        self.dimensions = dimensions
        self.range_min = range_min
        self.range_max = range_max

    def create_individual(self) -> List[float]:
        return [random.uniform(self.range_min, self.range_max) for _ in range(self.dimensions)]

    def fitness(self, chromosome: List[float]) -> float:
        value = self.objective(chromosome)
        return 1.0 / (1.0 + value)

    def objective(self, chromosome: List[float]) -> float:
        """目标函数值（最小化）"""
        n = len(chromosome)
        sum_sq = sum(x ** 2 for x in chromosome)
        sum_cos = sum(math.cos(2 * math.pi * x) for x in chromosome)

        return (
            -20 * math.exp(-0.2 * math.sqrt(sum_sq / n))
            - math.exp(sum_cos / n)
            + 20
            + math.e
        )

    def display(self, chromosome: List[float]) -> None:
        value = self.objective(chromosome)
        print(f"Solution: {[f'{x:.4f}' for x in chromosome]}")
        print(f"Objective value: {value:.6f}")


class GriewankProblem(Problem):
    """
    Griewank 函数优化问题

    f(x) = 1 + sum(x_i^2 / 4000) - prod(cos(x_i / sqrt(i)))
    全局最优：x = [0, 0, ..., 0], f(x) = 0
    搜索范围：[-600, 600]^n

    特点：具有大量局部最优，但随着维度增加，局部最优数量减少
    """

    def __init__(self, dimensions: int = 3, range_min: float = -600.0, range_max: float = 600.0):
        self.dimensions = dimensions
        self.range_min = range_min
        self.range_max = range_max

    def create_individual(self) -> List[float]:
        return [random.uniform(self.range_min, self.range_max) for _ in range(self.dimensions)]

    def fitness(self, chromosome: List[float]) -> float:
        value = self.objective(chromosome)
        return 1.0 / (1.0 + value)

    def objective(self, chromosome: List[float]) -> float:
        """目标函数值（最小化）"""
        sum_sq = sum(x ** 2 / 4000 for x in chromosome)
        prod_cos = 1.0
        for i, x in enumerate(chromosome):
            prod_cos *= math.cos(x / math.sqrt(i + 1))
        return 1 + sum_sq - prod_cos

    def display(self, chromosome: List[float]) -> None:
        value = self.objective(chromosome)
        print(f"Solution: {[f'{x:.4f}' for x in chromosome]}")
        print(f"Objective value: {value:.6f}")
