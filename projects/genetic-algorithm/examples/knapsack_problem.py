"""
背包问题 - Knapsack Problem
============================

使用遗传算法求解 0/1 背包问题。

问题描述：
    给定 N 个物品，每个物品有重量和价值，
    在总重量不超过容量的前提下，选择物品使总价值最大。

编码方式：二进制编码
    gene = [1, 0, 1, 1, 0] 表示选择第 1、3、4 个物品

遗传算子：
    选择：锦标赛选择
    交叉：单点交叉
    变异：位翻转变异
"""

import sys
import os
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core import GeneticAlgorithm
from src.individual import Individual, Population


def generate_knapsack_data(n_items=20, max_weight=100, max_value=100, seed=42):
    """生成背包问题数据"""
    random.seed(seed)
    weights = [random.randint(1, max_weight // 2) for _ in range(n_items)]
    values = [random.randint(1, max_value) for _ in range(n_items)]
    capacity = int(sum(weights) * 0.6)  # 容量为总重量的 60%
    return weights, values, capacity


def knapsack_fitness(gene, weights, values, capacity):
    """
    背包问题适应度函数

    使用罚函数法处理约束：
        - 如果超重：fitness = total_value - penalty * (total_weight - capacity)
        - 如果不超重：fitness = total_value
    """
    total_weight = sum(g for g, w in zip(gene, weights) if g == 1)
    total_value = sum(v for g, v in zip(gene, values) if g == 1)

    if total_weight > capacity:
        # 罚函数：超重惩罚
        penalty = 10 * (total_weight - capacity)
        return total_value - penalty
    else:
        return total_value


def optimize_knapsack(n_items=20, max_generations=300, population_size=100):
    """求解背包问题"""
    print(f"\n{'='*60}")
    print(f"求解背包问题 (物品数={n_items})")
    print(f"{'='*60}")

    # 生成数据
    weights, values, capacity = generate_knapsack_data(n_items)

    print(f"\n物品数据:")
    print(f"  容量: {capacity}")
    print(f"  {'物品':>6} | {'重量':>6} | {'价值':>6} | {'价值/重量':>10}")
    for i, (w, v) in enumerate(zip(weights, values)):
        print(f"  {i+1:>6} | {w:>6} | {v:>6} | {v/w:>10.2f}")

    def fitness(gene):
        return knapsack_fitness(gene, weights, values, capacity)

    # 创建初始种群
    def init_population():
        individuals = []
        for _ in range(population_size):
            gene = [random.randint(0, 1) for _ in range(n_items)]
            individuals.append(Individual(gene=gene, fitness=0.0))
        return Population(size=population_size, individuals=individuals)

    ga = GeneticAlgorithm(
        population_size=population_size,
        fitness_func=fitness,
        max_generations=max_generations,
        selection_method='tournament',
        tournament_size=3,
        crossover_operator='single_point',
        mutation_operator='bit_flip',
        crossover_rate=0.8,
        mutation_rate=0.02,
        elite_count=2,
        seed=42,
        verbose=True,
    )

    result = ga.optimize(fitness_func=fitness, initial_population=init_population())

    best_gene = result.best_individual.gene
    best_value = sum(v for g, v in zip(best_gene, values) if g == 1)
    best_weight = sum(w for g, w in zip(best_gene, weights) if g == 1)

    print(f"\n  结果:")
    print(f"    选择物品: {[i+1 for i, g in enumerate(best_gene) if g == 1]}")
    print(f"    总价值: {best_value}")
    print(f"    总重量: {best_weight}/{capacity}")
    print(f"    代数: {result.total_generations}")
    print(f"    耗时: {result.elapsed_time:.2f}s")

    return best_gene, best_value, best_weight


if __name__ == "__main__":
    print("=" * 60)
    print("遗传算法 - 背包问题")
    print("Genetic Algorithm - Knapsack Problem")
    print("=" * 60)

    # 小背包问题
    gene, value, weight = optimize_knapsack(n_items=20, max_generations=300, population_size=100)

    # 大背包问题
    gene, value, weight = optimize_knapsack(n_items=50, max_generations=500, population_size=200)

    print("\n" + "=" * 60)
    print("背包问题求解完成!")
    print("=" * 60)
