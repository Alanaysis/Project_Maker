"""
函数优化演示 - Function Optimization Demo
==========================================

演示如何使用遗传算法优化连续函数。
使用实数编码和算术交叉、高斯变异。

测试函数：
    1. Sphere: 单峰，基准测试
    2. Rosenbrock: 峡谷地形，经典测试
    3. Rastrigin: 多峰，全局搜索测试
    4. Ackley: 多峰，精细搜索测试
"""

import sys
import os
import math
import random
import numpy as np

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core import GeneticAlgorithm
from src.individual import Individual, Population
from src.suites import (
    sphere_function, rosenbrock_function,
    rastrigin_function, ackley_function
)


def create_real_population(dimension: int, lower: float, upper: float, size: int):
    """创建实数编码的初始种群"""
    individuals = []
    for _ in range(size):
        gene = [random.uniform(lower, upper) for _ in range(dimension)]
        individuals.append(Individual(gene=gene, fitness=0.0))
    return Population(size=size, individuals=individuals)


def optimize_sphere(dimension=10):
    """优化 Sphere 函数"""
    print(f"\n{'='*60}")
    print(f"优化 Sphere 函数 (维度={dimension})")
    print(f"  全局最优: [0, 0, ..., 0], f=0")
    print(f"{'='*60}")

    def fitness(gene):
        return -sphere_function(gene)  # 最大化负值 = 最小化原函数

    ga = GeneticAlgorithm(
        population_size=100,
        fitness_func=fitness,
        max_generations=300,
        selection_method='tournament',
        tournament_size=3,
        crossover_operator='arithmetic',
        mutation_operator='gaussian',
        crossover_rate=0.8,
        mutation_rate=0.05,
        elite_count=2,
        seed=42,
        verbose=True,
    )

    # 传入初始种群
    init_pop = create_real_population(dimension, -5.12, 5.12, 100)
    result = ga.optimize(fitness_func=fitness, initial_population=init_pop)

    print(f"\n  结果:")
    print(f"    最佳适应度: {result.best_fitness:.6f}")
    print(f"    最佳基因: {[round(x, 4) for x in result.best_individual.gene]}")
    print(f"    代数: {result.total_generations}")
    print(f"    耗时: {result.elapsed_time:.2f}s")
    return result


def optimize_rosenbrock(dimension=5):
    """优化 Rosenbrock 函数"""
    print(f"\n{'='*60}")
    print(f"优化 Rosenbrock 函数 (维度={dimension})")
    print(f"  全局最优: [1, 1, ..., 1], f=0")
    print(f"{'='*60}")

    def fitness(gene):
        return -rosenbrock_function(gene)

    ga = GeneticAlgorithm(
        population_size=150,
        fitness_func=fitness,
        max_generations=500,
        selection_method='tournament',
        tournament_size=5,  # 更大的锦标赛提高选择压力
        crossover_operator='arithmetic',
        mutation_operator='gaussian',
        crossover_rate=0.8,
        mutation_rate=0.05,
        elite_count=3,
        seed=42,
        verbose=True,
    )

    init_pop = create_real_population(dimension, -5, 10, 150)
    result = ga.optimize(fitness_func=fitness, initial_population=init_pop)

    print(f"\n  结果:")
    print(f"    最佳适应度: {result.best_fitness:.6f}")
    print(f"    最佳基因: {[round(x, 4) for x in result.best_individual.gene]}")
    return result


def optimize_rastrigin(dimension=5):
    """优化 Rastrigin 函数"""
    print(f"\n{'='*60}")
    print(f"优化 Rastrigin 函数 (维度={dimension})")
    print(f"  全局最优: [0, 0, ..., 0], f=0")
    print(f"{'='*60}")

    def fitness(gene):
        return -rastrigin_function(gene)

    ga = GeneticAlgorithm(
        population_size=200,  # 大种群应对多峰
        fitness_func=fitness,
        max_generations=500,
        selection_method='tournament',
        tournament_size=3,
        crossover_operator='arithmetic',
        mutation_operator='gaussian',
        crossover_rate=0.9,  # 高交叉率
        mutation_rate=0.1,  # 高变异率维持多样性
        elite_count=2,
        seed=42,
        verbose=True,
    )

    init_pop = create_real_population(dimension, -5.12, 5.12, 200)
    result = ga.optimize(fitness_func=fitness, initial_population=init_pop)

    print(f"\n  结果:")
    print(f"    最佳适应度: {result.best_fitness:.6f}")
    print(f"    最佳基因: {[round(x, 4) for x in result.best_individual.gene]}")
    return result


def optimize_ackley(dimension=5):
    """优化 Ackley 函数"""
    print(f"\n{'='*60}")
    print(f"优化 Ackley 函数 (维度={dimension})")
    print(f"  全局最优: [0, 0, ..., 0], f=0")
    print(f"{'='*60}")

    def fitness(gene):
        return -ackley_function(gene)

    ga = GeneticAlgorithm(
        population_size=150,
        fitness_func=fitness,
        max_generations=500,
        selection_method='tournament',
        tournament_size=3,
        crossover_operator='blend',
        mutation_operator='gaussian',
        crossover_rate=0.8,
        mutation_rate=0.05,
        elite_count=2,
        seed=42,
        verbose=True,
    )

    init_pop = create_real_population(dimension, -32, 32, 150)
    result = ga.optimize(fitness_func=fitness, initial_population=init_pop)

    print(f"\n  结果:")
    print(f"    最佳适应度: {result.best_fitness:.6f}")
    print(f"    最佳基因: {[round(x, 4) for x in result.best_individual.gene]}")
    return result


if __name__ == "__main__":
    print("=" * 60)
    print("遗传算法 - 函数优化演示")
    print("Genetic Algorithm - Function Optimization Demo")
    print("=" * 60)

    # 优化 Sphere 函数
    optimize_sphere(dimension=10)

    # 优化 Rosenbrock 函数
    optimize_rosenbrock(dimension=5)

    # 优化 Rastrigin 函数
    optimize_rastrigin(dimension=5)

    # 优化 Ackley 函数
    optimize_ackley(dimension=5)

    print("\n" + "=" * 60)
    print("所有优化完成!")
    print("=" * 60)
