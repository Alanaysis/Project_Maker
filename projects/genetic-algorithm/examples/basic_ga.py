"""
遗传算法基础示例

演示如何使用遗传算法求解简单的函数优化问题
"""

import sys
import os
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.ga_engine import GAEngine
from src.problems.base import Problem
from src.operators.selection import TournamentSelection
from src.operators.crossover import SinglePointCrossover
from src.operators.mutation import BitFlipMutation


class SphereProblem(Problem):
    """
    Sphere 函数优化问题

    目标：最小化 f(x) = sum(x_i^2)
    最优解：x = [0, 0, ..., 0]，f(x) = 0
    """

    def __init__(self, dimensions: int = 3, range_min: float = -10.0, range_max: float = 10.0):
        self.dimensions = dimensions
        self.range_min = range_min
        self.range_max = range_max

    def create_individual(self):
        return [random.uniform(self.range_min, self.range_max) for _ in range(self.dimensions)]

    def fitness(self, chromosome):
        # 最小化问题：适应度 = 1 / (1 + 目标函数值)
        value = sum(x ** 2 for x in chromosome)
        return 1.0 / (1.0 + value)

    def display(self, chromosome):
        value = sum(x ** 2 for x in chromosome)
        print(f"Solution: {[f'{x:.4f}' for x in chromosome]}")
        print(f"Objective value: {value:.6f}")


def main():
    print("=" * 60)
    print("遗传算法基础示例 - Sphere 函数优化")
    print("=" * 60)
    print()

    # 创建问题
    problem = SphereProblem(dimensions=3)
    print("Problem: Minimize f(x) = x1^2 + x2^2 + x3^2")
    print("Optimal solution: x = [0, 0, 0], f(x) = 0")
    print()

    # 创建 GA 引擎
    engine = GAEngine(
        problem,
        population_size=50,
        selection=TournamentSelection(tournament_size=3),
        crossover=SinglePointCrossover(crossover_rate=0.8),
        mutation=BitFlipMutation(mutation_rate=0.1)
    )

    # 运行算法
    print("Running Genetic Algorithm...")
    print("-" * 60)
    best = engine.run(generations=100, verbose=True)
    print("-" * 60)
    print()

    # 输出结果
    print("Best solution found:")
    problem.display(best.chromosome)
    print(f"Fitness: {best.fitness:.6f}")
    print()

    # 显示收敛过程
    history = engine.get_convergence_data()
    print(f"Initial best fitness: {history['best_fitness'][0]:.6f}")
    print(f"Final best fitness: {history['best_fitness'][-1]:.6f}")
    print(f"Improvement: {(history['best_fitness'][-1] - history['best_fitness'][0]) / history['best_fitness'][0] * 100:.2f}%")


if __name__ == "__main__":
    main()
