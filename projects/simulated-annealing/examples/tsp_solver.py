#!/usr/bin/env python3
"""
TSP 求解器示例 (Traveling Salesman Problem Solver)

使用模拟退火算法求解旅行商问题。

旅行商问题 (TSP): 给定 n 个城市，找到访问每个城市恰好一次并返回起点的最短路径。

邻域操作：
- swap: 交换两个城市的位置
- insert: 将一个城市插入到另一个位置
- reverse: 反转一段路径 (2-opt)

TSP 距离计算：欧几里得距离
"""

import random
import math
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core import SimulatedAnnealing, SAResult
from src.temperature import ExponentialScheduler, LinearScheduler, AdaptiveScheduler
from src.neighborhood import swap_neighbor, insert_neighbor, reverse_neighbor
from src.cooling import ExponentialCooling, LinearCooling, create_cooling_schedule


class TSPSolver:
    """TSP 模拟退火求解器"""

    def __init__(self, cities: list, seed: int = 42):
        """
        Args:
            cities: 城市坐标列表，每个城市为 (x, y) 元组
            seed: 随机种子
        """
        self.cities = cities
        self.n = len(cities)
        random.seed(seed)

        # 预计算距离矩阵
        self.distance_matrix = self._compute_distance_matrix()

    def _compute_distance_matrix(self) -> list:
        """预计算所有城市间的欧几里得距离"""
        n = self.n
        dist = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(i + 1, n):
                d = math.sqrt(
                    (self.cities[i][0] - self.cities[j][0]) ** 2
                    + (self.cities[i][1] - self.cities[j][1]) ** 2
                )
                dist[i][j] = dist[j][i] = d
        return dist

    def path_length(self, path: list) -> float:
        """计算路径的总长度"""
        total = 0.0
        for i in range(len(path) - 1):
            total += self.distance_matrix[path[i]][path[i + 1]]
        # 返回起点
        total += self.distance_matrix[path[-1]][path[0]]
        return total

    def neighbor_generator(self, path: list) -> list:
        """邻域生成：随机选择两种操作之一"""
        operation = random.choice(["swap", "insert", "reverse"])
        if operation == "swap":
            return swap_neighbor(path)
        elif operation == "insert":
            return insert_neighbor(path)
        else:
            return reverse_neighbor(path)

    def solve(
        self,
        initial_temp: float = 10000.0,
        cooling_rate: float = 0.995,
        iterations_per_temp: int = 100,
        strategy: str = "swap",
        seed: int = 42,
    ) -> SAResult:
        """
        求解 TSP

        Args:
            initial_temp: 初始温度
            cooling_rate: 冷却率
            iterations_per_temp: 每个温度的迭代次数
            strategy: 邻域策略 ("swap", "insert", "reverse")
            seed: 随机种子

        Returns:
            SAResult: 优化结果
        """
        # 初始化
        random.seed(seed)
        initial_path = list(range(self.n))
        random.shuffle(initial_path)

        sa = SimulatedAnnealing(
            initial_temp=initial_temp,
            min_temp=1e-8,
            cooling_rate=cooling_rate,
            iterations_per_temp=iterations_per_temp,
            seed=seed,
        )

        def objective(path):
            return self.path_length(path)

        if strategy == "swap":
            gen = swap_neighbor
        elif strategy == "insert":
            gen = insert_neighbor
        elif strategy == "reverse":
            gen = reverse_neighbor
        else:
            gen = self.neighbor_generator

        result = sa.optimize(
            objective=objective,
            initial_solution=initial_path,
            neighbor_generator=gen,
        )

        return result


def generate_random_cities(n: int, bounds: tuple = (0, 100)) -> list:
    """生成随机城市坐标"""
    low, high = bounds
    return [(random.uniform(low, high), random.uniform(low, high)) for _ in range(n)]


def main():
    """主函数：演示 TSP 求解"""
    print("=" * 60)
    print("模拟退火求解旅行商问题 (TSP)")
    print("=" * 60)

    # 生成测试数据
    n_cities = 30
    cities = generate_random_cities(n_cities)

    # 打印城市信息
    print(f"\n城市数量: {n_cities}")
    print(f"坐标范围: (0, 100) x (0, 100)")

    # 求解
    solver = TSPSolver(cities)

    strategies = ["swap", "insert", "reverse", "mixed"]
    results = {}

    for strategy in strategies:
        print(f"\n--- 策略: {strategy} ---")

        if strategy == "mixed":
            result = solver.solve(
                initial_temp=10000.0,
                cooling_rate=0.995,
                iterations_per_temp=100,
                strategy="swap",
            )
        else:
            result = solver.solve(
                initial_temp=10000.0,
                cooling_rate=0.995,
                iterations_per_temp=100,
                strategy=strategy,
            )

        print(result.summary())
        print(f"最优路径: {result.best_solution[:10]}...")
        print(f"路径长度: {result.best_energy:.4f}")

        results[strategy] = result

    # 比较不同策略
    print("\n" + "=" * 60)
    print("策略比较")
    print("=" * 60)
    print(f"{'策略':<15} {'路径长度':>12} {'迭代次数':>10} {'时间(秒)':>10}")
    print("-" * 50)
    for name, res in results.items():
        print(f"{name:<15} {res.best_energy:>12.4f} {res.iteration_count:>10} {res.runtime:>10.4f}")

    best_strategy = min(results, key=lambda k: results[k].best_energy)
    print(f"\n最佳策略: {best_strategy} (路径长度: {results[best_strategy].best_energy:.4f})")


if __name__ == "__main__":
    main()
