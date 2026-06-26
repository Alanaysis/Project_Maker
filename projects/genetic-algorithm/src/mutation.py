"""
遗传算法 - 变异操作模块
Genetic Algorithm - Mutation Operators Module

变异（Mutation）模拟生物基因突变，是 GA 维持种群多样性的关键机制。

变异的作用：
    1. 维持种群多样性，防止早熟收敛
    2. 探索新的解空间区域
    3. 保证 GA 的全局收敛性（理论上）

变异概率（Pm）：
    通常取值：0.01 - 0.1
        - 过高：搜索退化为随机游走
        - 过低：多样性丧失，早熟收敛
"""

import random
import math
from typing import List, Tuple
from src.core.individual import Individual


class MutationOperator:
    """变异操作符基类"""
    name: str = "base"

    def mutate(self, individual: Individual) -> Individual:
        raise NotImplementedError

    @staticmethod
    def _make_individual(chromosome: list, fitness: float) -> Individual:
        """Helper: create Individual with given fitness"""
        ind = Individual(chromosome)
        ind.fitness = fitness
        return ind


class BitFlipMutation(MutationOperator):
    """
    位翻转变异 (Bit-Flip Mutation)

    适用于二进制编码。
    对每个基因位以概率 Pm 翻转（0→1 或 1→0）。

    示例：
        基因: [1 0 1 1 0]
        变异: [1 0 0 1 1]  (第3位和第5位翻转)
    """
    name = "bit_flip"

    def __init__(self, mutation_rate: float = 0.01):
        self.mutation_rate = mutation_rate

    def mutate(self, individual: Individual) -> Individual:
        gene = individual.chromosome.copy()

        for i in range(len(gene)):
            if random.random() < self.mutation_rate:
                gene[i] = 1 - gene[i]

        return self._make_individual(gene, individual.fitness)


class SwapMutation(MutationOperator):
    """
    交换变异 (Swap Mutation)

    适用于排列编码（如 TSP）。
    随机选择两个位置，交换它们的基因值。

    示例（TSP）：
        基因: [1 2 3 4 5]
        变异: [1 4 3 2 5]  (第2位和第4位交换)
    """
    name = "swap"

    def __init__(self, mutation_rate: float = 0.01):
        self.mutation_rate = mutation_rate

    def mutate(self, individual: Individual) -> Individual:
        gene = individual.chromosome.copy()
        n = len(gene)

        if n < 2:
            return self._make_individual(gene, individual.fitness)

        for i in range(n):
            if random.random() < self.mutation_rate:
                j = random.randint(0, n - 1)
                gene[i], gene[j] = gene[j], gene[i]

        return self._make_individual(gene, individual.fitness)


class InversionMutation(MutationOperator):
    """
    逆序变异 (Inversion Mutation)

    适用于排列编码。
    随机选择两个位置，将之间的基因段逆序。

    示例（TSP）：
        基因: [1 2 3 4 5 6 7]
        变异: [1 2 5 4 3 6 7]  (第3-5位逆序)
    """
    name = "inversion"

    def __init__(self, mutation_rate: float = 0.01):
        self.mutation_rate = mutation_rate

    def mutate(self, individual: Individual) -> Individual:
        gene = individual.chromosome.copy()
        n = len(gene)

        if n < 3:
            return self._make_individual(gene, individual.fitness)

        if random.random() < self.mutation_rate:
            point1, point2 = sorted(random.sample(range(n), 2))
            gene[point1:point2 + 1] = gene[point1:point2 + 1][::-1]

        return self._make_individual(gene, individual.fitness)


class GaussianMutation(MutationOperator):
    """
    高斯变异 (Gaussian Mutation)

    适用于实数编码。
    对每个基因值加上高斯分布的随机扰动。

    公式：
        gene[i] = gene[i] + N(0, sigma)
    """
    name = "gaussian"

    def __init__(self, mutation_rate: float = 0.01, sigma: float = 0.1):
        self.mutation_rate = mutation_rate
        self.sigma = sigma

    def mutate(self, individual: Individual) -> Individual:
        gene = individual.chromosome.copy()

        for i in range(len(gene)):
            if random.random() < self.mutation_rate:
                gene[i] += random.gauss(0, self.sigma)

        return self._make_individual(gene, individual.fitness)


class BoundaryMutation(MutationOperator):
    """
    边界变异 (Boundary Mutation)

    适用于实数编码。
    以一定概率将基因值变异到边界值。
    """
    name = "boundary"

    def __init__(self, lower_bound: float = -10.0, upper_bound: float = 10.0,
                 mutation_rate: float = 0.01, boundary_prob: float = 0.5):
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.mutation_rate = mutation_rate
        self.boundary_prob = boundary_prob

    def mutate(self, individual: Individual) -> Individual:
        gene = individual.chromosome.copy()

        for i in range(len(gene)):
            if random.random() < self.mutation_rate:
                if random.random() < self.boundary_prob:
                    gene[i] = self.lower_bound if random.random() < 0.5 else self.upper_bound
                else:
                    gene[i] = random.uniform(self.lower_bound, self.upper_bound)

        return self._make_individual(gene, individual.fitness)


class UniformMutation(MutationOperator):
    """
    均匀变异 (Uniform Mutation)

    适用于实数编码。
    以一定概率将基因值替换为区间内的均匀随机值。
    """
    name = "uniform"

    def __init__(self, lower_bound: float = -10.0, upper_bound: float = 10.0,
                 mutation_rate: float = 0.01):
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.mutation_rate = mutation_rate

    def mutate(self, individual: Individual) -> Individual:
        gene = individual.chromosome.copy()

        for i in range(len(gene)):
            if random.random() < self.mutation_rate:
                gene[i] = random.uniform(self.lower_bound, self.upper_bound)

        return self._make_individual(gene, individual.fitness)


def get_mutation_operator(name: str, **kwargs) -> MutationOperator:
    """
    工厂函数：根据名称获取变异操作符

    Args:
        name: 变异算子名称
            - 'bit_flip': 位翻转变异（二进制编码）
            - 'swap': 交换变异（排列编码）
            - 'inversion': 逆序变异（排列编码）
            - 'gaussian': 高斯变异（实数编码）
            - 'boundary': 边界变异（实数编码）
            - 'uniform': 均匀变异（实数编码）

    Returns:
        MutationOperator 实例
    """
    operators = {
        'bit_flip': BitFlipMutation,
        'swap': SwapMutation,
        'inversion': InversionMutation,
        'gaussian': GaussianMutation,
        'boundary': BoundaryMutation,
        'uniform': UniformMutation,
    }

    if name not in operators:
        raise ValueError(f"Unknown mutation operator: {name}. "
                         f"Available: {list(operators.keys())}")

    return operators[name](**kwargs)
