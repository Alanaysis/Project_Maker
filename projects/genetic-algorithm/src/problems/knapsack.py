"""
背包问题：0/1 背包问题实现
"""

from typing import Any, List, Tuple
import random

from .base import Problem


class KnapsackProblem(Problem):
    """
    0/1 背包问题

    给定 n 个物品，每个物品有重量和价值。在背包容量限制下，
    选择物品使得总价值最大，且总重量不超过背包容量。

    编码方式：二进制编码，1 表示选择该物品，0 表示不选择
    """

    def __init__(self, items: List[Tuple[float, float]], capacity: float):
        """
        初始化背包问题

        Args:
            items: 物品列表，每个物品为 (weight, value) 元组
            capacity: 背包容量
        """
        self.items = items
        self.n_items = len(items)
        self.capacity = capacity

    def create_individual(self) -> List[int]:
        """
        创建随机个体（二进制编码）

        Returns:
            随机的物品选择方案
        """
        return [random.randint(0, 1) for _ in range(self.n_items)]

    def fitness(self, chromosome: List[int]) -> float:
        """
        计算适应度

        如果总重量超过容量，施加惩罚

        Args:
            chromosome: 物品选择方案（0/1 列表）

        Returns:
            适应度值
        """
        total_weight = sum(w * g for (w, _), g in zip(self.items, chromosome))
        total_value = sum(v * g for (_, v), g in zip(self.items, chromosome))

        # 超重惩罚
        if total_weight > self.capacity:
            penalty = (total_weight - self.capacity) / self.capacity
            return max(0.01, total_value * (1 - penalty))

        return total_value

    def calculate_total_weight(self, chromosome: List[int]) -> float:
        """计算总重量"""
        return sum(w * g for (w, _), g in zip(self.items, chromosome))

    def calculate_total_value(self, chromosome: List[int]) -> float:
        """计算总价值"""
        return sum(v * g for (_, v), g in zip(self.items, chromosome))

    def is_valid(self, chromosome: List[int]) -> bool:
        """检查解是否有效（不超重）"""
        return self.calculate_total_weight(chromosome) <= self.capacity

    def display(self, chromosome: List[int]) -> None:
        """
        显示解

        Args:
            chromosome: 物品选择方案
        """
        total_weight = self.calculate_total_weight(chromosome)
        total_value = self.calculate_total_value(chromosome)
        selected = [i for i, g in enumerate(chromosome) if g == 1]

        print(f"Selected items: {selected}")
        print(f"Total weight: {total_weight:.2f} / {self.capacity:.2f}")
        print(f"Total value: {total_value:.2f}")
        print(f"Valid: {self.is_valid(chromosome)}")

    @staticmethod
    def generate_random_problem(n_items: int, max_weight: float = 50.0, max_value: float = 100.0, capacity_ratio: float = 0.5) -> 'KnapsackProblem':
        """
        生成随机背包问题

        Args:
            n_items: 物品数量
            max_weight: 最大重量
            max_value: 最大价值
            capacity_ratio: 容量与总重量的比率

        Returns:
            随机生成的背包问题实例
        """
        items = [(random.uniform(1, max_weight), random.uniform(1, max_value)) for _ in range(n_items)]
        total_weight = sum(w for w, _ in items)
        capacity = total_weight * capacity_ratio
        return KnapsackProblem(items, capacity)


class MultiKnapsackProblem(Problem):
    """
    多重背包问题

    给定 n 个物品和 m 个背包，每个物品有重量和价值，每个背包有容量限制。
    目标是将物品分配到背包中，使得总价值最大。

    编码方式：整数编码，chromosome[i] 表示物品 i 分配到的背包编号（0 表示不选择）
    """

    def __init__(self, items: List[Tuple[float, float]], capacities: List[float]):
        """
        初始化多重背包问题

        Args:
            items: 物品列表，每个物品为 (weight, value) 元组
            capacities: 各背包的容量列表
        """
        self.items = items
        self.n_items = len(items)
        self.capacities = capacities
        self.n_knapsacks = len(capacities)

    def create_individual(self) -> List[int]:
        """
        创建随机个体

        Returns:
            物品分配方案，0 表示不选择，1~m 表示分配到对应背包
        """
        return [random.randint(0, self.n_knapsacks) for _ in range(self.n_items)]

    def fitness(self, chromosome: List[int]) -> float:
        """
        计算适应度

        Args:
            chromosome: 物品分配方案

        Returns:
            适应度值（考虑约束违反的惩罚）
        """
        # 计算每个背包的总重量
        knapsack_weights = [0.0] * self.n_knapsacks
        total_value = 0.0

        for i, assignment in enumerate(chromosome):
            if assignment > 0:
                weight, value = self.items[i]
                knapsack_weights[assignment - 1] += weight
                total_value += value

        # 计算惩罚
        penalty = 0.0
        for j in range(self.n_knapsacks):
            if knapsack_weights[j] > self.capacities[j]:
                excess = knapsack_weights[j] - self.capacities[j]
                penalty += excess / self.capacities[j]

        if penalty > 0:
            return max(0.01, total_value * (1 - penalty))

        return total_value

    def is_valid(self, chromosome: List[int]) -> bool:
        """检查解是否有效"""
        knapsack_weights = [0.0] * self.n_knapsacks

        for i, assignment in enumerate(chromosome):
            if assignment > 0:
                weight, _ = self.items[i]
                knapsack_weights[assignment - 1] += weight

        return all(knapsack_weights[j] <= self.capacities[j] for j in range(self.n_knapsacks))

    def display(self, chromosome: List[int]) -> None:
        """显示解"""
        total_value = sum(
            self.items[i][1] for i in range(self.n_items) if chromosome[i] > 0
        )

        print(f"Total value: {total_value:.2f}")
        for j in range(self.n_knapsacks):
            items_in_knapsack = [
                i for i in range(self.n_items) if chromosome[i] == j + 1
            ]
            weight = sum(self.items[i][0] for i in items_in_knapsack)
            print(f"  Knapsack {j + 1}: items={items_in_knapsack}, weight={weight:.2f}/{self.capacities[j]:.2f}")

    @staticmethod
    def generate_random_problem(n_items: int, n_knapsacks: int = 3, max_weight: float = 30.0, max_value: float = 100.0) -> 'MultiKnapsackProblem':
        """
        生成随机多重背包问题

        Args:
            n_items: 物品数量
            n_knapsacks: 背包数量
            max_weight: 最大重量
            max_value: 最大价值

        Returns:
            随机生成的多重背包问题实例
        """
        items = [(random.uniform(1, max_weight), random.uniform(1, max_value)) for _ in range(n_items)]
        total_weight = sum(w for w, _ in items)
        # 每个背包的容量约为总重量 / 背包数 * 1.2
        avg_capacity = total_weight / n_knapsacks * 1.2
        capacities = [random.uniform(avg_capacity * 0.8, avg_capacity * 1.2) for _ in range(n_knapsacks)]
        return MultiKnapsackProblem(items, capacities)
