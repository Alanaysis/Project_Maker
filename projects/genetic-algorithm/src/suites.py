"""
遗传算法 - 标准库模块
Genetic Algorithm - Standard Library Module

提供常用测试函数和便捷工厂函数。
"""

import math
from typing import Callable, Tuple


# ============================================================
# 标准测试函数
# ============================================================
# 这些函数常用于测试和优化算法的性能评估。
# 每种函数都有不同的特点（多峰、可分离、旋转等），
# 用于评估算法在不同挑战下的表现。


def sphere_function(x: list) -> float:
    """
    Sphere 函数（单峰、可分离）

    f(x) = sum(x_i^2), x_i in [-5.12, 5.12]
    全局最优: x* = [0, 0, ..., 0], f(x*) = 0

    特点：
        - 单峰函数，无局部最优
        - 可分离（各维度独立）
        - 适合测试算法的收敛速度
    """
    return sum(xi ** 2 for xi in x)


def rosenbrock_function(x: list) -> float:
    """
    Rosenbrock 函数（单峰、不可分离、峡谷地形）

    f(x) = sum(100*(x_{i+1} - x_i^2)^2 + (1 - x_i)^2), x_i in [-5, 10]
    全局最优: x* = [1, 1, ..., 1], f(x*) = 0

    特点：
        - 非线性、非凸
        - 狭窄的抛物线形山谷
        - 全局最优在平坦区域，难以定位
        - 经典的算法测试函数
    """
    result = 0.0
    for i in range(len(x) - 1):
        result += 100 * (x[i + 1] - x[i] ** 2) ** 2 + (1 - x[i]) ** 2
    return result


def rastrigin_function(x: list) -> float:
    """
    Rastrigin 函数（多峰、可分离）

    f(x) = 10*n + sum(x_i^2 - 10*cos(2*pi*x_i)), x_i in [-5.12, 5.12]
    全局最优: x* = [0, 0, ..., 0], f(x*) = 0

    特点：
        - 大量局部最优（指数级增长）
        - 适合测试算法的全局搜索能力
        - 峰值间距均匀
    """
    n = len(x)
    return 10 * n + sum(xi ** 2 - 10 * math.cos(2 * math.pi * xi) for xi in x)


def ackley_function(x: list) -> float:
    """
    Ackley 函数（多峰、接近单峰的全局最优）

    f(x) = -20*exp(-0.2*sqrt(1/n*sum(x_i^2))) - exp(1/n*sum(cos(2*pi*x_i))) + e + 20
    x_i in [-32, 32]
    全局最优: x* = [0, 0, ..., 0], f(x*) = 0

    特点：
        - 大量局部最优
        - 全局最优区域平坦
        - 适合测试算法的精细搜索能力
    """
    n = len(x)
    sum_sq = sum(xi ** 2 for xi in x)
    sum_cos = sum(math.cos(2 * math.pi * xi) for xi in x)
    return -20 * math.exp(-0.2 * math.sqrt(sum_sq / n)) - math.exp(sum_cos / n) + math.e + 20


def griewank_function(x: list) -> float:
    """
    Griewank 函数（多峰、大搜索空间）

    f(x) = 1 + 1/4000*sum(x_i^2) - prod(cos(x_i/sqrt(i))), x_i in [-600, 600]
    全局最优: x* = [0, 0, ..., 0], f(x*) = 0

    特点：
        - 大量局部最优
        - 全局最优附近非常平坦
        - 各维度耦合项（乘积项）
    """
    n = len(x)
    sum_sq = sum(xi ** 2 for xi in x)
    prod_cos = 1.0
    for i, xi in enumerate(x, 1):
        prod_cos *= math.cos(xi / math.sqrt(i))
    return 1 + sum_sq / 4000 - prod_cos


# ============================================================
# 最大化问题的适应度函数
# ============================================================
# 对于最大化问题，需要取负值转换为最小化问题，
# 或者直接用正值作为适应度。


def max_sphere_fitness(x: list) -> float:
    """Sphere 函数的最大版本（适应度 = -f(x) + 常数）"""
    return -sphere_function(x) + 1000


def max_ackley_fitness(x: list) -> float:
    """Ackley 函数的最大版本"""
    return -ackley_function(x) + 30


# ============================================================
# 便捷工厂函数
# ============================================================


def create_binary_ga(gene_length: int, fitness_func: Callable,
                     max_generations: int = 500,
                     population_size: int = 100,
                     **kwargs):
    """
    创建二进制编码的遗传算法实例

    Args:
        gene_length: 基因长度（编码位数）
        fitness_func: 适应度函数
        max_generations: 最大代数
        population_size: 种群大小
        **kwargs: 其他参数

    Returns:
        GeneticAlgorithm 实例
    """
    from .core import GeneticAlgorithm

    return GeneticAlgorithm(
        population_size=population_size,
        gene_length=gene_length,
        fitness_func=fitness_func,
        max_generations=max_generations,
        selection_method=kwargs.get('selection_method', 'tournament'),
        tournament_size=kwargs.get('tournament_size', 3),
        crossover_operator=kwargs.get('crossover_operator', 'single_point'),
        mutation_operator=kwargs.get('mutation_operator', 'bit_flip'),
        crossover_rate=kwargs.get('crossover_rate', 0.8),
        mutation_rate=kwargs.get('mutation_rate', 0.01),
        elite_count=kwargs.get('elite_count', 2),
        seed=kwargs.get('seed', None),
        verbose=kwargs.get('verbose', True),
    )


def create_real_ga(dimension: int, fitness_func: Callable,
                   lower_bound: float = -5.12, upper_bound: float = 5.12,
                   max_generations: int = 500,
                   population_size: int = 100,
                   **kwargs):
    """
    创建实数编码的遗传算法实例

    Args:
        dimension: 问题维度
        fitness_func: 适应度函数
        lower_bound: 变量下界
        upper_bound: 变量上界
        max_generations: 最大代数
        population_size: 种群大小
        **kwargs: 其他参数

    Returns:
        GeneticAlgorithm 实例
    """
    from .core import GeneticAlgorithm
    import random

    def init_population():
        from .individual import Individual, Population
        individuals = []
        for _ in range(population_size):
            gene = [random.uniform(lower_bound, upper_bound) for _ in range(dimension)]
            individuals.append(Individual(gene=gene, fitness=0.0))
        return Population(size=population_size, individuals=individuals)

    return GeneticAlgorithm(
        population_size=population_size,
        fitness_func=fitness_func,
        max_generations=max_generations,
        selection_method=kwargs.get('selection_method', 'tournament'),
        tournament_size=kwargs.get('tournament_size', 3),
        crossover_operator=kwargs.get('crossover_operator', 'arithmetic'),
        mutation_operator=kwargs.get('mutation_operator', 'gaussian'),
        crossover_rate=kwargs.get('crossover_rate', 0.8),
        mutation_rate=kwargs.get('mutation_rate', 0.01),
        elite_count=kwargs.get('elite_count', 2),
        seed=kwargs.get('seed', None),
        verbose=kwargs.get('verbose', True),
        _init_func=init_population,
    )
