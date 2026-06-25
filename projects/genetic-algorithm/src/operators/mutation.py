"""
变异算子：随机改变个体的某些基因
"""

from abc import ABC, abstractmethod
from typing import Optional
import random
import math

from ..core.individual import Individual


class MutationOperator(ABC):
    """变异算子基类"""

    @abstractmethod
    def mutate(self, individual: Individual) -> Individual:
        """
        执行变异操作

        Args:
            individual: 待变异的个体

        Returns:
            变异后的个体
        """
        pass


class BitFlipMutation(MutationOperator):
    """
    位翻转变异：随机翻转染色体上的位

    适用于二进制编码
    """

    def __init__(self, mutation_rate: float = 0.01):
        """
        初始化位翻转变异

        Args:
            mutation_rate: 变异概率
        """
        self.mutation_rate = mutation_rate

    def mutate(self, individual: Individual) -> Individual:
        mutated = individual.copy()
        for i in range(len(mutated.chromosome)):
            if random.random() < self.mutation_rate:
                mutated.chromosome[i] = 1 - mutated.chromosome[i]
        return mutated


class SwapMutation(MutationOperator):
    """
    交换变异：随机交换两个位置的值

    适用于排列编码（如 TSP）
    """

    def __init__(self, mutation_rate: float = 0.1):
        """
        初始化交换变异

        Args:
            mutation_rate: 变异概率
        """
        self.mutation_rate = mutation_rate

    def mutate(self, individual: Individual) -> Individual:
        mutated = individual.copy()
        if random.random() < self.mutation_rate:
            size = len(mutated.chromosome)
            i, j = random.sample(range(size), 2)
            mutated.chromosome[i], mutated.chromosome[j] = mutated.chromosome[j], mutated.chromosome[i]
        return mutated


class InversionMutation(MutationOperator):
    """
    逆序变异：随机选择一段子序列并反转

    适用于排列编码（如 TSP）
    """

    def __init__(self, mutation_rate: float = 0.1):
        """
        初始化逆序变异

        Args:
            mutation_rate: 变异概率
        """
        self.mutation_rate = mutation_rate

    def mutate(self, individual: Individual) -> Individual:
        mutated = individual.copy()
        if random.random() < self.mutation_rate:
            size = len(mutated.chromosome)
            start = random.randint(0, size - 2)
            end = random.randint(start + 1, size - 1)
            mutated.chromosome[start:end + 1] = reversed(mutated.chromosome[start:end + 1])
        return mutated


class GaussianMutation(MutationOperator):
    """
    高斯变异：对实数编码的基因添加高斯噪声

    x' = x + N(0, sigma)

    适用于实数编码的连续优化问题，是实数编码中最常用的变异方式。
    """

    def __init__(self, mutation_rate: float = 0.1, sigma: float = 1.0, min_value: Optional[float] = None, max_value: Optional[float] = None):
        """
        初始化高斯变异

        Args:
            mutation_rate: 每个基因的变异概率
            sigma: 高斯分布的标准差
            min_value: 基因的最小值（可选，用于边界约束）
            max_value: 基因的最大值（可选，用于边界约束）
        """
        self.mutation_rate = mutation_rate
        self.sigma = sigma
        self.min_value = min_value
        self.max_value = max_value

    def mutate(self, individual: Individual) -> Individual:
        mutated = individual.copy()
        for i in range(len(mutated.chromosome)):
            if random.random() < self.mutation_rate:
                # Box-Muller 变换生成高斯随机数
                noise = random.gauss(0, self.sigma)
                mutated.chromosome[i] += noise

                # 边界约束
                if self.min_value is not None:
                    mutated.chromosome[i] = max(mutated.chromosome[i], self.min_value)
                if self.max_value is not None:
                    mutated.chromosome[i] = min(mutated.chromosome[i], self.max_value)
        return mutated


class AdaptiveMutation(MutationOperator):
    """
    自适应变异：根据种群适应度自动调整变异率

    当种群多样性高时降低变异率（利用），当种群多样性低时提高变异率（探索）。

    策略：
    - 如果最优适应度停滞不前，增加变异率
    - 如果适应度持续改善，降低变异率
    """

    def __init__(
        self,
        initial_mutation_rate: float = 0.1,
        min_mutation_rate: float = 0.01,
        max_mutation_rate: float = 0.5,
        sigma: float = 1.0,
        stagnation_threshold: int = 10,
        increase_factor: float = 1.5,
        decrease_factor: float = 0.8,
    ):
        """
        初始化自适应变异

        Args:
            initial_mutation_rate: 初始变异率
            min_mutation_rate: 最小变异率
            max_mutation_rate: 最大变异率
            sigma: 高斯变异的标准差
            stagnation_threshold: 适应度停滞代数阈值
            increase_factor: 变异率增加因子
            decrease_factor: 变异率减少因子
        """
        self.mutation_rate = initial_mutation_rate
        self.min_mutation_rate = min_mutation_rate
        self.max_mutation_rate = max_mutation_rate
        self.sigma = sigma
        self.stagnation_threshold = stagnation_threshold
        self.increase_factor = increase_factor
        self.decrease_factor = decrease_factor

        # 内部状态
        self._best_fitness = float('-inf')
        self._stagnation_count = 0

    def update(self, current_best_fitness: float):
        """
        根据当前最优适应度更新变异率

        Args:
            current_best_fitness: 当前种群的最优适应度
        """
        if current_best_fitness > self._best_fitness:
            # 适应度改善，降低变异率
            self._best_fitness = current_best_fitness
            self._stagnation_count = 0
            self.mutation_rate = max(
                self.min_mutation_rate,
                self.mutation_rate * self.decrease_factor
            )
        else:
            # 适应度停滞，增加变异率
            self._stagnation_count += 1
            if self._stagnation_count >= self.stagnation_threshold:
                self.mutation_rate = min(
                    self.max_mutation_rate,
                    self.mutation_rate * self.increase_factor
                )
                self._stagnation_count = 0

    def mutate(self, individual: Individual) -> Individual:
        mutated = individual.copy()
        for i in range(len(mutated.chromosome)):
            if random.random() < self.mutation_rate:
                if isinstance(mutated.chromosome[i], (int, float)):
                    # 实数编码：高斯变异
                    noise = random.gauss(0, self.sigma)
                    mutated.chromosome[i] = type(mutated.chromosome[i])(mutated.chromosome[i] + noise)
                else:
                    # 其他编码：随机扰动
                    pass
        return mutated

    @property
    def current_mutation_rate(self) -> float:
        """获取当前变异率"""
        return self.mutation_rate

    def reset(self):
        """重置自适应状态"""
        self._best_fitness = float('-inf')
        self._stagnation_count = 0
        self.mutation_rate = self.min_mutation_rate
