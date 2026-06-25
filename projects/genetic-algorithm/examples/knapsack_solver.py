"""
背包问题求解示例

演示如何使用遗传算法求解 0/1 背包问题
"""

import sys
import os
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.ga_engine import GAEngine
from src.problems.knapsack import KnapsackProblem
from src.operators.selection import TournamentSelection
from src.operators.crossover import UniformCrossover
from src.operators.mutation import BitFlipMutation


def main():
    print("=" * 60)
    print("遗传算法 - 0/1 背包问题求解")
    print("=" * 60)
    print()

    # 创建背包问题
    # 物品: (重量, 价值)
    items = [
        (23, 500), (31, 600), (29, 400), (44, 700),
        (53, 800), (38, 550), (63, 900), (85, 1100),
        (25, 450), (12, 200), (18, 350), (27, 650),
        (35, 500), (41, 750), (52, 850), (60, 950),
    ]
    capacity = 400

    problem = KnapsackProblem(items, capacity)

    print(f"Number of items: {len(items)}")
    print(f"Knapsack capacity: {capacity}")
    print()

    # 创建 GA 引擎
    engine = GAEngine(
        problem,
        population_size=100,
        selection=TournamentSelection(tournament_size=3),
        crossover=UniformCrossover(crossover_rate=0.8),
        mutation=BitFlipMutation(mutation_rate=0.05),
        elitism_count=5,
    )

    # 运行算法
    print("Running Genetic Algorithm...")
    print("-" * 60)
    best = engine.run(generations=200, verbose=True)
    print("-" * 60)
    print()

    # 输出结果
    print("Best solution found:")
    problem.display(best.chromosome)
    print()

    # 计算改进
    history = engine.get_convergence_data()
    print(f"Initial best fitness: {history['best_fitness'][0]:.2f}")
    print(f"Final best fitness: {history['best_fitness'][-1]:.2f}")
    print(f"Improvement: {(history['best_fitness'][-1] - history['best_fitness'][0]) / history['best_fitness'][0] * 100:.2f}%")

    # 多次运行找更好解
    print()
    print("=" * 60)
    print("Multiple runs to find better solution")
    print("=" * 60)
    print()

    best_overall_value = 0
    best_overall_solution = None

    for run in range(5):
        engine = GAEngine(
            problem,
            population_size=100,
            selection=TournamentSelection(tournament_size=3),
            crossover=UniformCrossover(crossover_rate=0.8),
            mutation=BitFlipMutation(mutation_rate=0.05),
            elitism_count=5,
        )

        best = engine.run(generations=150, verbose=False)
        value = problem.calculate_total_value(best.chromosome)

        print(f"Run {run + 1}: Value = {value:.2f}")

        if value > best_overall_value:
            best_overall_value = value
            best_overall_solution = best.chromosome

    print()
    print("Best overall solution:")
    problem.display(best_overall_solution)


if __name__ == "__main__":
    main()
