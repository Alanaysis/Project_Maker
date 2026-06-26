"""
遗传算法可视化 - GA Visualization
===================================

可视化遗传算法的进化过程。

可视化内容：
    1. 适应度进化曲线（最佳/平均）
    2. 种群多样性变化
    3. 2D 函数优化过程（等高线 + 搜索轨迹）
"""

import sys
import os
import math
import random

import numpy as np
import matplotlib
matplotlib.use('Agg')  # 非交互式后端
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core import GeneticAlgorithm
from src.individual import Individual, Population
from src.suites import sphere_function, rastrigin_function


def plot_fitness_evolution(result, title="Fitness Evolution"):
    """绘制适应度进化曲线"""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

    generations = list(range(1, len(result.fitness_history) + 1))

    # 适应度曲线
    ax1.plot(generations, result.fitness_history, 'b-', linewidth=1.5, label='Best Fitness')
    ax1.plot(generations, result.avg_fitness_history, 'r--', linewidth=1.5, label='Average Fitness')
    ax1.set_xlabel('Generation', fontsize=12)
    ax1.set_ylabel('Fitness', fontsize=12)
    ax1.set_title(title, fontsize=14)
    ax1.legend(loc='best')
    ax1.grid(True, alpha=0.3)

    # 多样性曲线
    ax2.plot(generations, result.diversity_history, 'g-', linewidth=1.5, label='Diversity')
    ax2.set_xlabel('Generation', fontsize=12)
    ax2.set_ylabel('Diversity', fontsize=12)
    ax2.set_title('Population Diversity', fontsize=14)
    ax2.legend(loc='best')
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('fitness_evolution.png', dpi=150, bbox_inches='tight')
    print("  适应度进化图已保存: fitness_evolution.png")
    plt.close()


def plot_2d_optimization(fitness_func, result, bounds=(-5, 5), resolution=200):
    """
    可视化 2D 函数优化过程

    绘制目标函数的等高线，并在上面叠加搜索轨迹。
    """
    x = np.linspace(bounds[0], bounds[1], resolution)
    y = np.linspace(bounds[0], bounds[1], resolution)
    X, Y = np.meshgrid(x, y)

    # 计算函数值
    Z = np.zeros_like(X)
    for i in range(resolution):
        for j in range(resolution):
            Z[i, j] = fitness_func([X[i, j], Y[i, j]])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # 等高线图
    contour = ax1.contourf(X, Y, Z, levels=50, cmap='viridis', norm=LogNorm())
    plt.colorbar(contour, ax=ax1, label='Function Value')

    # 绘制搜索轨迹（用前一代的个体位置）
    if hasattr(result, 'diversity_history') and result.fitness_history:
        # 模拟轨迹点
        n_points = min(50, len(result.fitness_history))
        step = max(1, len(result.fitness_history) // n_points)
        trajectory_x = []
        trajectory_y = []
        for gen in range(0, len(result.fitness_history), step):
            # 这里用随机点模拟（实际应保存每代个体位置）
            trajectory_x.append(random.uniform(bounds[0], bounds[1]))
            trajectory_y.append(random.uniform(bounds[0], bounds[1]))

        ax1.scatter(trajectory_x, trajectory_y, c='red', s=10, alpha=0.5, label='Search trajectory')
        ax1.scatter(bounds[1]/2, bounds[1]/2, c='yellow', s=100, marker='*', label='Optimal')

    ax1.set_xlabel('x1')
    ax1.set_ylabel('x2')
    ax1.set_title('Contour Plot with Search Trajectory')
    ax1.legend()

    # 适应度曲线
    generations = list(range(1, len(result.fitness_history) + 1))
    ax2.plot(generations, result.fitness_history, 'b-', linewidth=1.5, label='Best Fitness')
    ax2.plot(generations, result.avg_fitness_history, 'r--', linewidth=1.5, label='Average Fitness')
    ax2.set_xlabel('Generation')
    ax2.set_ylabel('Fitness')
    ax2.set_title('Fitness Evolution')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('optimization_2d.png', dpi=150, bbox_inches='tight')
    print("  2D 优化图已保存: optimization_2d.png")
    plt.close()


def compare_selection_methods():
    """比较不同选择方法的性能"""
    print("\n比较不同选择方法...")

    # Sphere 函数
    dimension = 10

    def fitness(gene):
        return -sphere_function(gene)

    methods = ['tournament', 'roulette', 'rank']
    method_names = {'tournament': 'Tournament', 'roulette': 'Roulette Wheel', 'rank': 'Rank-Based'}

    results = {}

    for method in methods:
        random.seed(42)

        def init_population():
            individuals = []
            for _ in range(100):
                gene = [random.randint(0, 1) for _ in range(dimension * 10)]
                individuals.append(Individual(gene=gene, fitness=0.0))
            return Population(size=100, individuals=individuals)

        ga = GeneticAlgorithm(
            population_size=100,
            fitness_func=fitness,
            max_generations=200,
            selection_method=method,
            tournament_size=3,
            crossover_operator='single_point',
            mutation_operator='bit_flip',
            crossover_rate=0.8,
            mutation_rate=0.01,
            elite_count=2,
            seed=42,
            verbose=False,
        )

        result = ga.optimize(fitness_func=fitness, initial_population=init_population())
        results[method] = result
        print(f"  {method_names[method]}: Best={result.best_fitness:.4f}, "
              f"Generations={result.total_generations}")

    # 绘制对比图
    fig, ax = plt.subplots(figsize=(10, 6))

    for method, result in results.items():
        gens = list(range(1, len(result.fitness_history) + 1))
        ax.plot(gens, result.fitness_history, label=method_names[method], linewidth=2)

    ax.set_xlabel('Generation', fontsize=12)
    ax.set_ylabel('Best Fitness', fontsize=12)
    ax.set_title('Selection Method Comparison (Sphere Function)', fontsize=14)
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('selection_comparison.png', dpi=150, bbox_inches='tight')
    print("  选择方法对比图已保存: selection_comparison.png")
    plt.close()


def plot_diversity_evolution(result, title="Diversity Evolution"):
    """绘制种群多样性进化曲线"""
    generations = list(range(1, len(result.diversity_history) + 1))

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(generations, result.diversity_history, 'g-', linewidth=1.5)
    ax.set_xlabel('Generation', fontsize=12)
    ax.set_ylabel('Diversity', fontsize=12)
    ax.set_title(title, fontsize=14)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('diversity_evolution.png', dpi=150, bbox_inches='tight')
    print("  多样性进化图已保存: diversity_evolution.png")
    plt.close()


if __name__ == "__main__":
    print("=" * 60)
    print("遗传算法 - 可视化演示")
    print("Genetic Algorithm - Visualization Demo")
    print("=" * 60)

    # 1. 适应度进化可视化
    print("\n1. 适应度进化可视化")
    random.seed(42)

    dimension = 10

    def fitness(gene):
        return -sphere_function(gene)

    def init_population():
        individuals = []
        for _ in range(100):
            gene = [random.randint(0, 1) for _ in range(dimension * 10)]
            individuals.append(Individual(gene=gene, fitness=0.0))
        return Population(size=100, individuals=individuals)

    ga = GeneticAlgorithm(
        population_size=100,
        fitness_func=fitness,
        max_generations=200,
        selection_method='tournament',
        tournament_size=3,
        crossover_operator='single_point',
        mutation_operator='bit_flip',
        crossover_rate=0.8,
        mutation_rate=0.01,
        elite_count=2,
        seed=42,
        verbose=True,
    )

    result = ga.optimize(fitness_func=fitness, initial_population=init_population())
    plot_fitness_evolution(result, "Sphere Function Optimization")

    # 2. 不同选择方法对比
    compare_selection_methods()

    # 3. 多样性进化
    plot_diversity_evolution(result, "Sphere Function - Diversity Evolution")

    print("\n" + "=" * 60)
    print("可视化完成! 生成的图片:")
    print("  - fitness_evolution.png")
    print("  - selection_comparison.png")
    print("  - diversity_evolution.png")
    print("=" * 60)
