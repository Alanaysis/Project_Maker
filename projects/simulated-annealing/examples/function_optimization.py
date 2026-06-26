#!/usr/bin/env python3
"""
函数优化示例 (Function Optimization Demo)

使用模拟退火算法优化连续函数。

测试函数：
1. Sphere: f(x) = sum(x_i^2) - 全局最小值在 (0, 0, ..., 0)
2. Rastrigin: 多峰函数，测试算法跳出局部最优的能力
3. Rosenbrock: 经典优化测试函数，有狭窄的抛物线形山谷
"""

import random
import math
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core import SimulatedAnnealing, SAResult
from src.temperature import ExponentialScheduler
from src.neighborhood import continuous_neighbor


class FunctionOptimizer:
    """连续函数优化器"""

    def __init__(self, dim: int = 2, bounds: tuple = (-5.12, 5.12), seed: int = 42):
        self.dim = dim
        self.bounds = bounds
        self.seed = seed
        random.seed(seed)

    def random_initial_solution(self):
        """生成随机初始解"""
        low, high = self.bounds
        return [random.uniform(low, high) for _ in range(self.dim)]

    def optimize(
        self,
        objective,
        name: str = "unknown",
        initial_temp: float = 1000.0,
        cooling_rate: float = 0.99,
        iterations_per_temp: int = 50,
        neighbor_magnitude: float = 1.0,
    ) -> SAResult:
        """
        优化目标函数

        Args:
            objective: 目标函数
            name: 函数名称
            initial_temp: 初始温度
            cooling_rate: 冷却率
            iterations_per_temp: 每个温度的迭代次数
            neighbor_magnitude: 邻域扰动幅度

        Returns:
            SAResult: 优化结果
        """
        initial_sol = self.random_initial_solution()

        sa = SimulatedAnnealing(
            initial_temp=initial_temp,
            min_temp=1e-10,
            cooling_rate=cooling_rate,
            iterations_per_temp=iterations_per_temp,
            seed=self.seed,
        )

        def neighbor_gen(sol):
            return continuous_neighbor(sol, magnitude=neighbor_magnitude)

        result = sa.optimize(
            objective=objective,
            initial_solution=initial_sol,
            neighbor_generator=neighbor_gen,
        )

        print(f"\n{'=' * 50}")
        print(f"优化函数: {name}")
        print(f"{'=' * 50}")
        print(f"维度: {self.dim}")
        print(f"搜索范围: [{self.bounds[0]}, {self.bounds[1]}]")
        print(f"最优解: {result.best_solution}")
        print(f"最优值: {result.best_energy:.8f}")
        print(f"迭代次数: {result.iteration_count}")
        print(f"运行时间: {result.runtime:.4f} 秒")

        return result


def sphere_function(x):
    """
    Sphere 函数

    f(x) = sum(x_i^2)

    全局最小值: f(0) = 0
    单峰函数，适合测试算法的基本收敛能力
    """
    return sum(xi ** 2 for xi in x)


def rastrigin_function(x):
    """
    Rastrigin 函数

    f(x) = 10*n + sum(x_i^2 - 10*cos(2*pi*x_i))

    全局最小值: f(0) = 0
    多峰函数，有大量的局部最优，适合测试算法的全局搜索能力

    典型测试函数，广泛用于测试优化算法性能
    """
    n = len(x)
    return 10 * n + sum(xi ** 2 - 10 * math.cos(2 * math.pi * xi) for xi in x)


def rosenbrock_function(x):
    """
    Rosenbrock 函数 (Banana function)

    f(x) = sum(100*(x_{i+1} - x_i^2)^2 + (1 - x_i)^2)

    全局最小值: f(1, 1, ..., 1) = 0
    非凸函数，有狭窄的抛物线形山谷，适合测试算法的精细搜索能力
    """
    return sum(100 * (x[i + 1] - x[i] ** 2) ** 2 + (1 - x[i]) ** 2 for i in range(len(x) - 1))


def ackley_function(x):
    """
    Ackley 函数

    多峰函数，适合测试全局优化算法

    全局最小值: f(0) = 0
    """
    n = len(x)
    sum_sq = sum(xi ** 2 for xi in x)
    sum_cos = sum(math.cos(2 * math.pi * xi) for xi in x)
    return -20 * math.exp(-0.2 * math.sqrt(sum_sq / n)) - math.exp(sum_cos / n) + 20 + math.e


def main():
    """主函数：演示函数优化"""
    print("=" * 60)
    print("模拟退火函数优化演示")
    print("=" * 60)

    optimizer = FunctionOptimizer(dim=5, bounds=(-5.12, 5.12))

    # 测试函数列表
    test_functions = [
        (sphere_function, "Sphere 函数", 1000.0, 0.99, 50, 2.0),
        (rastrigin_function, "Rastrigin 函数", 500.0, 0.995, 80, 1.0),
        (rosenbrock_function, "Rosenbrock 函数", 1000.0, 0.99, 100, 0.5),
        (ackley_function, "Ackley 函数", 500.0, 0.995, 80, 1.0),
    ]

    for func, name, temp, rate, iters, mag in test_functions:
        optimizer.optimize(
            objective=func,
            name=name,
            initial_temp=temp,
            cooling_rate=rate,
            iterations_per_temp=iters,
            neighbor_magnitude=mag,
        )

    # 比较不同冷却率对 Sphere 函数的影响
    print(f"\n{'=' * 60}")
    print("冷却率对比（Sphere 函数）")
    print(f"{'=' * 60}")

    cooling_rates = [0.90, 0.95, 0.98, 0.99, 0.995, 0.999]
    print(f"{'冷却率':>10} {'最优值':>15} {'迭代次数':>10} {'时间(秒)':>10}")
    print("-" * 50)

    for rate in cooling_rates:
        result = optimizer.optimize(
            objective=sphere_function,
            name="Sphere",
            initial_temp=1000.0,
            cooling_rate=rate,
            iterations_per_temp=200,
            neighbor_magnitude=3.0,
        )
        print(f"{rate:>10.3f} {result.best_energy:>15.8f} {result.iteration_count:>10} {result.runtime:>10.4f}")


if __name__ == "__main__":
    main()
