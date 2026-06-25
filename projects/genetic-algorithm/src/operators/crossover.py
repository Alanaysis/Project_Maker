"""
交叉算子：两个父代交换遗传信息产生子代
"""

from abc import ABC, abstractmethod
from typing import List, Tuple
import random

import numpy as np

from ..core.individual import Individual


class CrossoverOperator(ABC):
    """交叉算子基类"""

    @abstractmethod
    def crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        """
        执行交叉操作

        Args:
            parent1: 父代1
            parent2: 父代2

        Returns:
            两个子代个体
        """
        pass


class UniformCrossover(CrossoverOperator):
    """
    均匀交叉：每个基因以相同概率从两个父代中随机选择

    适用于二进制编码和实数编码，比单点/两点交叉具有更强的探索能力。
    """

    def __init__(self, crossover_rate: float = 0.8, swap_probability: float = 0.5):
        """
        初始化均匀交叉

        Args:
            crossover_rate: 交叉概率
            swap_probability: 每个基因位交换的概率（默认 0.5）
        """
        self.crossover_rate = crossover_rate
        self.swap_probability = swap_probability

    def crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        if random.random() > self.crossover_rate:
            return parent1.copy(), parent2.copy()

        size = len(parent1.chromosome)
        child1_chromosome = []
        child2_chromosome = []

        for i in range(size):
            if random.random() < self.swap_probability:
                child1_chromosome.append(parent2.chromosome[i])
                child2_chromosome.append(parent1.chromosome[i])
            else:
                child1_chromosome.append(parent1.chromosome[i])
                child2_chromosome.append(parent2.chromosome[i])

        return Individual(child1_chromosome), Individual(child2_chromosome)


class ArithmeticCrossover(CrossoverOperator):
    """
    算术交叉：对实数编码的父代进行线性组合

    child1 = alpha * parent1 + (1 - alpha) * parent2
    child2 = (1 - alpha) * parent1 + alpha * parent2

    适用于实数编码的连续优化问题。
    """

    def __init__(self, crossover_rate: float = 0.8, alpha: float = 0.5):
        """
        初始化算术交叉

        Args:
            crossover_rate: 交叉概率
            alpha: 混合系数（0 到 1 之间）
        """
        self.crossover_rate = crossover_rate
        self.alpha = alpha

    def crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        if random.random() > self.crossover_rate:
            return parent1.copy(), parent2.copy()

        alpha = random.random() if self.alpha is None else self.alpha

        child1_chromosome = [
            alpha * p1 + (1 - alpha) * p2
            for p1, p2 in zip(parent1.chromosome, parent2.chromosome)
        ]
        child2_chromosome = [
            (1 - alpha) * p1 + alpha * p2
            for p1, p2 in zip(parent1.chromosome, parent2.chromosome)
        ]

        return Individual(child1_chromosome), Individual(child2_chromosome)


class SinglePointCrossover(CrossoverOperator):
    """
    单点交叉：随机选择一个切点，交换两父代的后半部分

    适用于二进制编码和实数编码
    """

    def __init__(self, crossover_rate: float = 0.8):
        """
        初始化单点交叉

        Args:
            crossover_rate: 交叉概率
        """
        self.crossover_rate = crossover_rate

    def crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        if random.random() > self.crossover_rate:
            return parent1.copy(), parent2.copy()

        size = len(parent1.chromosome)
        point = random.randint(1, size - 1)

        child1_chromosome = parent1.chromosome[:point] + parent2.chromosome[point:]
        child2_chromosome = parent2.chromosome[:point] + parent1.chromosome[point:]

        return Individual(child1_chromosome), Individual(child2_chromosome)


class TwoPointCrossover(CrossoverOperator):
    """
    两点交叉：随机选择两个切点，交换两父代中间部分

    适用于二进制编码和实数编码
    """

    def __init__(self, crossover_rate: float = 0.8):
        """
        初始化两点交叉

        Args:
            crossover_rate: 交叉概率
        """
        self.crossover_rate = crossover_rate

    def crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        if random.random() > self.crossover_rate:
            return parent1.copy(), parent2.copy()

        size = len(parent1.chromosome)
        point1 = random.randint(0, size - 2)
        point2 = random.randint(point1 + 1, size - 1)

        child1_chromosome = (
            parent1.chromosome[:point1] +
            parent2.chromosome[point1:point2] +
            parent1.chromosome[point2:]
        )
        child2_chromosome = (
            parent2.chromosome[:point1] +
            parent1.chromosome[point1:point2] +
            parent2.chromosome[point2:]
        )

        return Individual(child1_chromosome), Individual(child2_chromosome)


class OrderCrossover(CrossoverOperator):
    """
    顺序交叉 (OX)：保持城市访问的相对顺序

    专用于 TSP 等排列编码问题
    """

    def __init__(self, crossover_rate: float = 0.8):
        """
        初始化顺序交叉

        Args:
            crossover_rate: 交叉概率
        """
        self.crossover_rate = crossover_rate

    def crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        if random.random() > self.crossover_rate:
            return parent1.copy(), parent2.copy()

        size = len(parent1.chromosome)

        # 随机选择两个切点
        start = random.randint(0, size - 2)
        end = random.randint(start + 1, size - 1)

        # 生成子代1
        child1 = [None] * size
        child1[start:end + 1] = parent1.chromosome[start:end + 1]

        # 从 parent2 填充剩余位置
        remaining = [x for x in parent2.chromosome if x not in child1[start:end + 1]]
        idx = 0
        for i in range(size):
            if child1[i] is None:
                child1[i] = remaining[idx]
                idx += 1

        # 生成子代2（对称操作）
        child2 = [None] * size
        child2[start:end + 1] = parent2.chromosome[start:end + 1]

        remaining = [x for x in parent1.chromosome if x not in child2[start:end + 1]]
        idx = 0
        for i in range(size):
            if child2[i] is None:
                child2[i] = remaining[idx]
                idx += 1

        return Individual(child1), Individual(child2)
