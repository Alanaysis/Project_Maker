"""
TSP 旅行商问题 - Traveling Salesman Problem
============================================

使用遗传算法求解 TSP 问题。

问题描述：
    给定 N 个城市和它们之间的距离，找到一条经过每个城市恰好一次
    并回到起点的最短路径。

编码方式：排列编码（Permutation Encoding）
    gene = [3, 1, 4, 0, 2] 表示路径 3→1→4→0→2→3

遗传算子：
    选择：锦标赛选择
    交叉：顺序交叉（OX）
    变异：逆序变异
"""

import sys
import os
import math
import random
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core import GeneticAlgorithm
from src.individual import Individual, Population
from src.suites import create_binary_ga


def generate_cities(n_cities: int, seed: int = 42):
    """生成随机城市坐标"""
    random.seed(seed)
    cities = [(random.uniform(0, 100), random.uniform(0, 100)) for _ in range(n_cities)]
    return cities


def calculate_distance(city1, city2):
    """计算两个城市之间的欧氏距离"""
    return math.sqrt((city1[0] - city2[0]) ** 2 + (city1[1] - city2[1]) ** 2)


def calculate_tsp_distance(path, cities):
    """
    计算 TSP 路径的总距离

    路径: [c1, c2, c3, ..., cn]
    总距离: dist(c1,c2) + dist(c2,c3) + ... + dist(cn,c1)
    """
    total = 0.0
    n = len(path)
    for i in range(n):
        total += calculate_distance(cities[path[i]], cities[path[(i + 1) % n]])
    return total


def tsp_fitness(path, cities, max_distance):
    """
    TSP 适应度函数

    适应度 = max_distance - path_distance
    路径越短，适应度越高
    """
    distance = calculate_tsp_distance(path, cities)
    return max_distance - distance + 1  # +1 确保适应度为正


def optimize_tsp(n_cities=20, max_generations=500, population_size=100):
    """求解 TSP 问题"""
    print(f"\n{'='*60}")
    print(f"求解 TSP 问题 (城市数={n_cities})")
    print(f"{'='*60}")

    # 生成城市
    cities = generate_cities(n_cities, seed=42)

    # 计算最大可能距离（上界）
    max_distance = math.sqrt(100**2 + 100**2) * n_cities

    # 打印城市坐标
    print(f"\n城市坐标:")
    for i, (x, y) in enumerate(cities):
        print(f"  城市 {i}: ({x:.2f}, {y:.2f})")

    # 计算最优解（小问题可以暴力求解验证）
    if n_cities <= 10:
        from itertools import permutations
        min_dist = float('inf')
        for perm in permutations(range(1, n_cities)):
            path = [0] + list(perm)
            dist = calculate_tsp_distance(path, cities)
            if dist < min_dist:
                min_dist = dist
        print(f"\n最优解距离 (暴力): {min_dist:.4f}")

    def fitness(gene):
        return tsp_fitness(gene, cities, max_distance)

    # 创建初始种群（随机排列）
    def init_population():
        individuals = []
        for _ in range(population_size):
            gene = list(range(n_cities))
            random.shuffle(gene)
            individuals.append(Individual(gene=gene, fitness=0.0))
        return Population(size=population_size, individuals=individuals)

    ga = GeneticAlgorithm(
        population_size=population_size,
        fitness_func=fitness,
        max_generations=max_generations,
        selection_method='tournament',
        tournament_size=3,
        crossover_operator='order',  # 顺序交叉（OX）
        mutation_operator='inversion',  # 逆序变异
        crossover_rate=0.8,
        mutation_rate=0.02,
        elite_count=2,
        seed=42,
        verbose=True,
    )

    result = ga.optimize(fitness_func=fitness, initial_population=init_population())

    best_path = result.best_individual.gene
    best_distance = calculate_tsp_distance(best_path, cities)

    print(f"\n  结果:")
    print(f"    最佳路径: {best_path}")
    print(f"    最佳距离: {best_distance:.4f}")
    print(f"    代数: {result.total_generations}")
    print(f"    耗时: {result.elapsed_time:.2f}s")

    return best_path, best_distance


if __name__ == "__main__":
    print("=" * 60)
    print("遗传算法 - TSP 旅行商问题")
    print("Genetic Algorithm - Traveling Salesman Problem")
    print("=" * 60)

    # 小问题（20 个城市）
    path, distance = optimize_tsp(n_cities=20, max_generations=500, population_size=100)

    # 中等问题（50 个城市）
    path, distance = optimize_tsp(n_cities=50, max_generations=1000, population_size=200)

    print("\n" + "=" * 60)
    print("TSP 求解完成!")
    print("=" * 60)
