"""
自适应遗传算法示例

演示自适应变异率和精英保留策略的效果
"""

import sys
import os
import random
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.ga_engine import GAEngine
from src.problems.function_opt import RastriginProblem
from src.operators.selection import TournamentSelection
from src.operators.crossover import ArithmeticCrossover
from src.operators.mutation import AdaptiveMutation, GaussianMutation


def run_comparison():
    """比较固定变异率和自适应变异率的效果"""
    print("=" * 60)
    print("自适应遗传算法 vs 固定变异率")
    print("=" * 60)
    print()

    # 创建问题
    problem = RastriginProblem(dimensions=5, range_min=-5.12, range_max=5.12)
    print("Problem: Rastrigin Function")
    print(f"Dimensions: {problem.dimensions}")
    print("Global optimum: x = [0, 0, ..., 0], f(x) = 0")
    print()

    # 运行固定变异率的 GA
    print("Running GA with fixed mutation rate...")
    print("-" * 40)

    engine_fixed = GAEngine(
        problem,
        population_size=100,
        selection=TournamentSelection(tournament_size=3),
        crossover=ArithmeticCrossover(crossover_rate=0.8),
        mutation=GaussianMutation(mutation_rate=0.1, sigma=1.0),
        elitism_count=5,
    )

    best_fixed = engine_fixed.run(generations=200, verbose=False)
    history_fixed = engine_fixed.get_convergence_data()

    print(f"Final best fitness: {history_fixed['best_fitness'][-1]:.6f}")
    print(f"Final best objective: {problem.objective(best_fixed.chromosome):.6f}")
    print()

    # 运行自适应变异率的 GA
    print("Running GA with adaptive mutation rate...")
    print("-" * 40)

    adaptive_mutation = AdaptiveMutation(
        initial_mutation_rate=0.1,
        min_mutation_rate=0.01,
        max_mutation_rate=0.5,
        sigma=1.0,
        stagnation_threshold=10,
        increase_factor=1.5,
        decrease_factor=0.8,
    )

    engine_adaptive = GAEngine(
        problem,
        population_size=100,
        selection=TournamentSelection(tournament_size=3),
        crossover=ArithmeticCrossover(crossover_rate=0.8),
        mutation=adaptive_mutation,
        elitism_count=5,
    )

    best_adaptive = engine_adaptive.run(generations=200, verbose=False)
    history_adaptive = engine_adaptive.get_convergence_data()

    print(f"Final best fitness: {history_adaptive['best_fitness'][-1]:.6f}")
    print(f"Final best objective: {problem.objective(best_adaptive.chromosome):.6f}")
    print()

    # 比较结果
    print("=" * 60)
    print("Comparison Results")
    print("=" * 60)
    print()

    print(f"Fixed mutation - Best objective: {problem.objective(best_fixed.chromosome):.6f}")
    print(f"Adaptive mutation - Best objective: {problem.objective(best_adaptive.chromosome):.6f}")
    print()

    # 绘制收敛曲线
    plt.figure(figsize=(12, 8))

    plt.subplot(2, 1, 1)
    plt.plot(history_fixed['best_fitness'], label='Fixed Mutation Rate', linewidth=2)
    plt.plot(history_adaptive['best_fitness'], label='Adaptive Mutation Rate', linewidth=2)
    plt.xlabel('Generation')
    plt.ylabel('Best Fitness')
    plt.title('Convergence Comparison')
    plt.legend()
    plt.grid(True, alpha=0.3)

    # 绘制自适应变异率变化
    plt.subplot(2, 1, 2)
    if 'mutation_rate' in history_adaptive and history_adaptive['mutation_rate']:
        plt.plot(history_adaptive['mutation_rate'], label='Adaptive Mutation Rate', linewidth=2)
        plt.xlabel('Generation')
        plt.ylabel('Mutation Rate')
        plt.title('Adaptive Mutation Rate Over Time')
        plt.legend()
        plt.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('adaptive_ga_comparison.png', dpi=150, bbox_inches='tight')
    plt.show()

    print("Visualization saved: adaptive_ga_comparison.png")


def demonstrate_elitism():
    """演示精英保留策略的效果"""
    print()
    print("=" * 60)
    print("精英保留策略演示")
    print("=" * 60)
    print()

    problem = RastriginProblem(dimensions=3, range_min=-5.12, range_max=5.12)

    # 不使用精英保留
    print("Running GA without elitism...")
    engine_no_elitism = GAEngine(
        problem,
        population_size=50,
        selection=TournamentSelection(tournament_size=3),
        crossover=ArithmeticCrossover(crossover_rate=0.8),
        mutation=GaussianMutation(mutation_rate=0.1, sigma=1.0),
        elitism_count=0,
    )

    best_no_elitism = engine_no_elitism.run(generations=100, verbose=False)
    history_no_elitism = engine_no_elitism.get_convergence_data()

    # 使用精英保留
    print("Running GA with elitism (top 5)...")
    engine_elitism = GAEngine(
        problem,
        population_size=50,
        selection=TournamentSelection(tournament_size=3),
        crossover=ArithmeticCrossover(crossover_rate=0.8),
        mutation=GaussianMutation(mutation_rate=0.1, sigma=1.0),
        elitism_count=5,
    )

    best_elitism = engine_elitism.run(generations=100, verbose=False)
    history_elitism = engine_elitism.get_convergence_data()

    print()
    print(f"Without elitism - Best objective: {problem.objective(best_no_elitism.chromosome):.6f}")
    print(f"With elitism - Best objective: {problem.objective(best_elitism.chromosome):.6f}")
    print()

    # 绘制收敛曲线
    plt.figure(figsize=(10, 6))

    plt.plot(history_no_elitism['best_fitness'], label='Without Elitism', linewidth=2)
    plt.plot(history_elitism['best_fitness'], label='With Elitism (top 5)', linewidth=2)
    plt.xlabel('Generation')
    plt.ylabel('Best Fitness')
    plt.title('Elitism Strategy Comparison')
    plt.legend()
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('elitism_comparison.png', dpi=150, bbox_inches='tight')
    plt.show()

    print("Visualization saved: elitism_comparison.png")


def main():
    run_comparison()
    demonstrate_elitism()


if __name__ == "__main__":
    main()
