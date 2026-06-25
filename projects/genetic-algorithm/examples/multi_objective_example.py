"""
多目标优化示例

演示如何使用 NSGA-II 求解多目标优化问题
"""

import sys
import os
import random
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.multi_objective import MultiObjectiveProblem, NSGA2Engine


class ZDT1Problem(MultiObjectiveProblem):
    """
    ZDT1 测试问题

    f1 = x1
    f2 = g * (1 - sqrt(f1/g))
    g = 1 + 9/(n-1) * sum(x_i, i=2..n)

    Pareto 最优前沿：x1 in [0, 1], x_i = 0 for i > 1
    """

    def __init__(self, dimensions: int = 30):
        self.dimensions = dimensions

    def create_individual(self):
        return [random.uniform(0, 1) for _ in range(self.dimensions)]

    def objectives(self, chromosome):
        f1 = chromosome[0]
        g = 1 + 9 / (self.dimensions - 1) * sum(chromosome[1:])
        f2 = g * (1 - (f1 / g) ** 0.5)
        return [f1, f2]

    def display(self, chromosome):
        objs = self.objectives(chromosome)
        print(f"f1 = {objs[0]:.4f}, f2 = {objs[1]:.4f}")


class ZDT2Problem(MultiObjectiveProblem):
    """
    ZDT2 测试问题

    f1 = x1
    f2 = g * (1 - (f1/g)^2)
    g = 1 + 9/(n-1) * sum(x_i, i=2..n)

    Pareto 最优前沿：x1 in [0, 1], x_i = 0 for i > 1
    """

    def __init__(self, dimensions: int = 30):
        self.dimensions = dimensions

    def create_individual(self):
        return [random.uniform(0, 1) for _ in range(self.dimensions)]

    def objectives(self, chromosome):
        f1 = chromosome[0]
        g = 1 + 9 / (self.dimensions - 1) * sum(chromosome[1:])
        f2 = g * (1 - (f1 / g) ** 2)
        return [f1, f2]

    def display(self, chromosome):
        objs = self.objectives(chromosome)
        print(f"f1 = {objs[0]:.4f}, f2 = {objs[1]:.4f}")


def plot_pareto_front(pareto_front, title="Pareto Front"):
    """绘制 Pareto 前沿"""
    plt.figure(figsize=(10, 8))

    # 提取目标值
    f1_values = [ind.chromosome[0] for ind in pareto_front]
    f2_values = []

    for ind in pareto_front:
        if hasattr(ind, '_objectives'):
            f2_values.append(ind._objectives[1])
        else:
            # 重新计算
            problem = ZDT1Problem()
            objs = problem.objectives(ind.chromosome)
            f2_values.append(objs[1])

    plt.scatter(f1_values, f2_values, c='blue', s=50, alpha=0.7, label='Pareto Front')

    # 绘制理论 Pareto 前沿
    import numpy as np
    f1_theory = np.linspace(0, 1, 100)
    f2_theory = 1 - np.sqrt(f1_theory)
    plt.plot(f1_theory, f2_theory, 'r-', linewidth=2, label='Theoretical Pareto Front')

    plt.xlabel('f1', fontsize=12)
    plt.ylabel('f2', fontsize=12)
    plt.title(title, fontsize=14)
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('pareto_front.png', dpi=150, bbox_inches='tight')
    plt.show()


def main():
    print("=" * 60)
    print("NSGA-II 多目标优化示例")
    print("=" * 60)
    print()

    # 选择问题
    problem = ZDT1Problem(dimensions=10)
    print("Problem: ZDT1")
    print(f"Dimensions: {problem.dimensions}")
    print("Objectives: Minimize f1 and f2")
    print()

    # 创建 NSGA-II 引擎
    engine = NSGA2Engine(
        problem,
        population_size=100,
        crossover_rate=0.9,
        mutation_rate=0.1,
    )

    # 运行算法
    print("Running NSGA-II...")
    print("-" * 60)
    pareto_front = engine.run(generations=100, verbose=True)
    print("-" * 60)
    print()

    # 输出结果
    print(f"Pareto front size: {len(pareto_front)}")
    print()

    # 评估 Pareto 前沿质量
    objectives = [problem.objectives(ind.chromosome) for ind in pareto_front]

    f1_values = [obj[0] for obj in objectives]
    f2_values = [obj[1] for obj in objectives]

    print(f"f1 range: [{min(f1_values):.4f}, {max(f1_values):.4f}]")
    print(f"f2 range: [{min(f2_values):.4f}, {max(f2_values):.4f}]")
    print()

    # 显示部分 Pareto 最优解
    print("Sample Pareto optimal solutions:")
    print("-" * 40)
    for i in range(min(5, len(pareto_front))):
        ind = pareto_front[i]
        objs = objectives[i]
        print(f"Solution {i+1}: f1={objs[0]:.4f}, f2={objs[1]:.4f}")

    # 绘制 Pareto 前沿
    print()
    print("Plotting Pareto front...")
    plot_pareto_front(pareto_front, "ZDT1 Problem - Pareto Front")

    print()
    print("Visualization saved: pareto_front.png")


if __name__ == "__main__":
    main()
