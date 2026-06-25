"""
遗传算法可视化示例

演示如何可视化遗传算法的进化过程和 TSP 路径
"""

import sys
import os
import random
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.ga_engine import GAEngine
from src.problems.tsp import TSPProblem
from src.operators.selection import TournamentSelection
from src.operators.crossover import OrderCrossover
from src.operators.mutation import SwapMutation


def plot_evolution(history, title="Evolution Progress"):
    """绘制进化过程"""
    plt.figure(figsize=(10, 6))

    generations = range(len(history['best_fitness']))
    plt.plot(generations, history['best_fitness'], label='Best Fitness', linewidth=2)
    plt.plot(generations, history['average_fitness'], label='Average Fitness', linewidth=2, alpha=0.7)

    plt.xlabel('Generation', fontsize=12)
    plt.ylabel('Fitness', fontsize=12)
    plt.title(title, fontsize=14)
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('evolution_progress.png', dpi=150, bbox_inches='tight')
    plt.show()


def plot_tsp_route(cities, route, title="TSP Route"):
    """绘制 TSP 路径"""
    plt.figure(figsize=(10, 10))

    # 绘制城市
    for i, (x, y) in enumerate(cities):
        plt.scatter(x, y, c='red', s=100, zorder=5)
        plt.annotate(f'{i}', (x, y), textcoords="offset points", xytext=(0, 10),
                     ha='center', fontsize=10, fontweight='bold')

    # 绘制路径
    route_coords = [cities[i] for i in route] + [cities[route[0]]]
    xs = [c[0] for c in route_coords]
    ys = [c[1] for c in route_coords]
    plt.plot(xs, ys, 'b-', linewidth=2, alpha=0.7)

    # 计算距离
    problem = TSPProblem(cities)
    distance = problem.calculate_distance(route)

    plt.title(f'{title}\nTotal Distance: {distance:.2f}', fontsize=14)
    plt.xlabel('X', fontsize=12)
    plt.ylabel('Y', fontsize=12)
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('tsp_route.png', dpi=150, bbox_inches='tight')
    plt.show()


def plot_multiple_routes(cities, routes, titles):
    """绘制多个路径对比"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 14))
    axes = axes.flatten()

    problem = TSPProblem(cities)

    for idx, (route, title) in enumerate(zip(routes, titles)):
        ax = axes[idx]

        # 绘制城市
        for i, (x, y) in enumerate(cities):
            ax.scatter(x, y, c='red', s=80, zorder=5)
            ax.annotate(f'{i}', (x, y), textcoords="offset points", xytext=(0, 8),
                        ha='center', fontsize=8)

        # 绘制路径
        route_coords = [cities[i] for i in route] + [cities[route[0]]]
        xs = [c[0] for c in route_coords]
        ys = [c[1] for c in route_coords]
        ax.plot(xs, ys, 'b-', linewidth=1.5, alpha=0.7)

        distance = problem.calculate_distance(route)
        ax.set_title(f'{title}\nDistance: {distance:.2f}', fontsize=11)
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('multiple_routes.png', dpi=150, bbox_inches='tight')
    plt.show()


def main():
    print("=" * 60)
    print("遗传算法可视化示例")
    print("=" * 60)
    print()

    # 生成城市
    n_cities = 12
    cities = TSPProblem.generate_circle_cities(n_cities, radius=50)
    print(f"Generated {n_cities} cities in circular pattern")
    print()

    # 创建问题
    problem = TSPProblem(cities)

    # 运行 GA 并收集不同阶段的路径
    engine = GAEngine(
        problem,
        population_size=80,
        selection=TournamentSelection(tournament_size=3),
        crossover=OrderCrossover(crossover_rate=0.8),
        mutation=SwapMutation(mutation_rate=0.2)
    )

    # 收集不同代的最优解
    routes = []
    titles = []

    print("Running GA and collecting solutions...")
    for gen in range(200):
        engine.evolve_one_generation()

        # 每 50 代记录一次
        if gen % 50 == 0:
            best = engine.get_best_solution()
            routes.append(best.chromosome)
            titles.append(f"Generation {gen}")

    # 添加最终解
    best = engine.get_best_solution()
    routes.append(best.chromosome)
    titles.append("Final Solution")

    # 绘制进化过程
    print("Plotting evolution progress...")
    plot_evolution(engine.get_convergence_data(), "TSP Evolution Progress")

    # 绘制最终路径
    print("Plotting final route...")
    plot_tsp_route(cities, best.chromosome, "Best TSP Route Found")

    # 绘制多个阶段的路径
    print("Plotting multiple routes...")
    plot_multiple_routes(cities, routes[:4], titles[:4])

    print()
    print("Visualizations saved:")
    print("  - evolution_progress.png")
    print("  - tsp_route.png")
    print("  - multiple_routes.png")


if __name__ == "__main__":
    main()
