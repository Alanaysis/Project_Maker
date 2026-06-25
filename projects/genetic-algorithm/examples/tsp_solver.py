"""
TSP 问题求解示例

演示如何使用遗传算法求解旅行商问题
"""

import sys
import os
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.ga_engine import GAEngine
from src.problems.tsp import TSPProblem
from src.operators.selection import TournamentSelection, ElitismSelection
from src.operators.crossover import OrderCrossover
from src.operators.mutation import SwapMutation, InversionMutation


def main():
    print("=" * 60)
    print("遗传算法 TSP 求解示例")
    print("=" * 60)
    print()

    # 生成城市
    n_cities = 15
    cities = TSPProblem.generate_random_cities(n_cities, width=100, height=100)
    print(f"Generated {n_cities} random cities")
    print()

    # 创建 TSP 问题
    problem = TSPProblem(cities)

    # 计算初始随机路径的距离
    random_route = problem.create_individual()
    random_distance = problem.calculate_distance(random_route)
    print(f"Random route distance: {random_distance:.2f}")
    print()

    # 创建 GA 引擎
    engine = GAEngine(
        problem,
        population_size=100,
        selection=TournamentSelection(tournament_size=3),
        crossover=OrderCrossover(crossover_rate=0.8),
        mutation=SwapMutation(mutation_rate=0.2)
    )

    # 运行算法
    print("Running Genetic Algorithm...")
    print("-" * 60)
    best = engine.run(generations=200, verbose=True)
    print("-" * 60)
    print()

    # 输出结果
    best_distance = problem.calculate_distance(best.chromosome)
    print("Best solution found:")
    print(f"Route: {best.chromosome}")
    print(f"Total distance: {best_distance:.2f}")
    print()

    # 计算改进
    improvement = (random_distance - best_distance) / random_distance * 100
    print(f"Improvement over random: {improvement:.2f}%")
    print()

    # 显示收敛过程
    history = engine.get_convergence_data()
    initial_fitness = history['best_fitness'][0]
    final_fitness = history['best_fitness'][-1]
    print(f"Initial best fitness: {initial_fitness:.6f}")
    print(f"Final best fitness: {final_fitness:.6f}")
    print(f"Fitness improvement: {(final_fitness - initial_fitness) / initial_fitness * 100:.2f}%")

    # 尝试多次运行找到更好的解
    print()
    print("=" * 60)
    print("Multiple runs to find better solution")
    print("=" * 60)
    print()

    best_overall_distance = float('inf')
    best_overall_route = None

    for run in range(5):
        engine = GAEngine(
            problem,
            population_size=100,
            selection=TournamentSelection(tournament_size=3),
            crossover=OrderCrossover(crossover_rate=0.8),
            mutation=SwapMutation(mutation_rate=0.2)
        )

        best = engine.run(generations=150, verbose=False)
        distance = problem.calculate_distance(best.chromosome)

        print(f"Run {run + 1}: Distance = {distance:.2f}")

        if distance < best_overall_distance:
            best_overall_distance = distance
            best_overall_route = best.chromosome

    print()
    print(f"Best overall distance: {best_overall_distance:.2f}")
    print(f"Best route: {best_overall_route}")


if __name__ == "__main__":
    main()
