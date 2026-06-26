"""
遗传算法 - 交叉操作模块
Genetic Algorithm - Crossover Operators Module

交叉（Crossover）是 GA 的核心操作，模拟生物繁殖过程。
两个父代个体交换部分基因，产生新的子代个体。

交叉操作的作用：
    1. 组合优秀的基因片段
    2. 探索解空间的新区域
    3. 是 GA 搜索能力的主要来源

交叉概率（Pc）：
    通常取值：0.6 - 0.9
        - 过高：搜索变成随机游走
        - 过低：收敛慢，基因组合不足
"""

import random
from typing import List, Tuple
from src.core.individual import Individual


class CrossoverOperator:
    """交叉操作符基类"""
    name: str = "base"

    def crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        raise NotImplementedError

    @staticmethod
    def _make_individual(chromosome: list) -> Individual:
        """Helper: create Individual with default fitness=0.0"""
        ind = Individual(chromosome)
        ind.fitness = 0.0
        return ind


class SinglePointCrossover(CrossoverOperator):
    """
    单点交叉 (Single-Point Crossover)

    在基因序列中随机选择一个交叉点，交叉点两侧的基因交换。

    示例：
        父代1: [A B | C D E]
        父代2: [a b | c d e]
        交叉后:
        子代1: [A B | c d e]
        子代2: [a b | C D E]

    优点：
        - 实现简单
        - 保持基因块完整性
    缺点：
        - 只适用于固定长度的编码
    """
    name = "single_point"

    def crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        gene1 = parent1.chromosome.copy()
        gene2 = parent2.chromosome.copy()

        if len(gene1) < 2:
            return self._make_individual(gene1), self._make_individual(gene2)

        crossover_point = random.randint(1, len(gene1) - 1)
        gene1[crossover_point:], gene2[crossover_point:] = \
            gene2[crossover_point:], gene1[crossover_point:]

        return self._make_individual(gene1), self._make_individual(gene2)


class MultiPointCrossover(CrossoverOperator):
    """
    多点交叉 (Multi-Point Crossover)

    在基因序列中随机选择多个交叉点，交替交换基因片段。

    示例（2点交叉）：
        父代1: [A B | C D | E F G]
        父代2: [a b | c d | e f g]
        交叉后:
        子代1: [A B | c d | E F G]
        子代2: [a b | C D | e f g]

    优点：
        - 比单点交叉更灵活
        - 可以打破更强的基因关联
    缺点：
        - 交叉点越多，越接近随机重组
    """
    name = "multi_point"

    def __init__(self, num_points: int = 2):
        self.num_points = num_points

    def crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        gene1 = parent1.chromosome.copy()
        gene2 = parent2.chromosome.copy()

        if len(gene1) < 2:
            return self._make_individual(gene1), self._make_individual(gene2)

        max_points = min(self.num_points, len(gene1) - 1)
        if max_points < 1:
            return self._make_individual(gene1), self._make_individual(gene2)

        crossover_points = sorted(random.sample(range(1, len(gene1)), max_points))

        for i, point in enumerate(crossover_points):
            if i % 2 == 0:
                gene1[point:], gene2[point:] = gene2[point:], gene1[point:]

        return self._make_individual(gene1), self._make_individual(gene2)


class UniformCrossover(CrossoverOperator):
    """
    均匀交叉 (Uniform Crossover)

    对每个基因位独立地以概率 Pc 决定是否交换。

    示例：
        父代1: [A B C D E]
        父代2: [a b c d e]
        掩码:   [1 0 1 0 1]  (1=交换, 0=不交换)
        交叉后:
        子代1: [A b C d E]
        子代2: [a B c D e]

    优点：
        - 每个基因位独立处理
        - 探索能力强
    缺点：
        - 可能破坏优良基因块
    """
    name = "uniform"

    def __init__(self, crossover_rate: float = 0.5):
        self.crossover_rate = crossover_rate

    def crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        gene1 = parent1.chromosome.copy()
        gene2 = parent2.chromosome.copy()

        crossover_mask = [random.random() < self.crossover_rate for _ in range(len(gene1))]

        for i in range(len(gene1)):
            if crossover_mask[i]:
                gene1[i], gene2[i] = gene2[i], gene1[i]

        return self._make_individual(gene1), self._make_individual(gene2)


class ArithmeticCrossover(CrossoverOperator):
    """
    算术交叉 (Arithmetic Crossover)

    通过线性组合产生子代，主要用于实数编码。

    公式：
        子代1 = alpha * 父代1 + (1 - alpha) * 父代2
        子代2 = (1 - alpha) * 父代1 + alpha * 父代2

    其中 alpha 通常在 [0, 1] 范围内随机选取。

    当 alpha = 0.5 时，称为中间交叉（Intermediate Crossover）：
        子代1 = 子代2 = (父代1 + 父代2) / 2

    优点：
        - 适用于实数编码
        - 产生父代基因之间的中间解
        - 保持解的连通性
    缺点：
        - 仅适用于连续空间
        - 探索范围受限（在父代之间）
    """
    name = "arithmetic"

    def __init__(self, alpha: float = 0.5):
        self.alpha = alpha

    def crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        gene1 = parent1.chromosome.copy()
        gene2 = parent2.chromosome.copy()

        min_len = min(len(gene1), len(gene2))

        for i in range(min_len):
            a = random.uniform(0, 1)
            gene1[i] = a * gene1[i] + (1 - a) * gene2[i]
            gene2[i] = (1 - a) * gene1[i] + a * gene2[i]

        return self._make_individual(gene1), self._make_individual(gene2)


class BlendCrossover(CrossoverOperator):
    """
    BLX-alpha 交叉 (Blend Crossover)

    在父代基因值的扩展范围内随机采样。

    公式：
        对于每个基因位 i:
            min_val = min(g1[i], g2[i]) - alpha * |g1[i] - g2[i]|
            max_val = max(g1[i], g2[i]) + alpha * |g1[i] - g2[i]|
            子代基因 = Uniform(min_val, max_val)

    其中 alpha 控制扩展范围：
        - alpha = 0: 等价于中间交叉
        - alpha > 0: 扩展探索范围

    优点：
        - 扩展探索范围
        - 适合实数编码
    缺点：
        - 可能产生超出父代范围的解
    """
    name = "blend"

    def __init__(self, alpha: float = 0.5):
        self.alpha = alpha

    def crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        gene1 = parent1.chromosome.copy()
        gene2 = parent2.chromosome.copy()

        min_len = min(len(gene1), len(gene2))

        for i in range(min_len):
            g1, g2 = gene1[i], gene2[i]
            low = min(g1, g2) - self.alpha * abs(g1 - g2)
            high = max(g1, g2) + self.alpha * abs(g1 - g2)
            gene1[i] = random.uniform(low, high)
            gene2[i] = random.uniform(low, high)

        return self._make_individual(gene1), self._make_individual(gene2)


class OrderCrossover(CrossoverOperator):
    """
    顺序交叉 (Order Crossover, OX)

    专为排列编码（如 TSP）设计的交叉算子。
    保证子代也是有效的排列（无重复/缺失基因）。

    步骤：
        1. 从父代1随机选一段子序列
        2. 在父代2中找到该子序列对应的相对顺序
        3. 用父代2中剩余基因填充空缺位置

    示例（TSP问题）：
        父代1: [1 2 | 3 4 5 | 6 7]
        父代2: [4 5 | 2 8 1 | 3 6]
        子代1: [8 1 | 3 4 5 | 2 6]

    优点：
        - 保持排列合法性
        - 保留相对顺序信息
    缺点：
        - 实现较复杂
    """
    name = "order"

    def crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        gene1 = parent1.chromosome.copy()
        gene2 = parent2.chromosome.copy()
        n = len(gene1)

        point1, point2 = sorted(random.sample(range(n), 2))

        child1_gene = [None] * n
        child1_gene[point1:point2 + 1] = gene1[point1:point2 + 1]

        remaining = [g for g in gene2 if g not in child1_gene[point1:point2 + 1]]

        idx = 0
        for i in range(n):
            if child1_gene[i] is None:
                child1_gene[i] = remaining[idx]
                idx += 1

        child2_gene = [None] * n
        child2_gene[point1:point2 + 1] = gene2[point1:point2 + 1]

        remaining = [g for g in gene1 if g not in child2_gene[point1:point2 + 1]]

        idx = 0
        for i in range(n):
            if child2_gene[i] is None:
                child2_gene[i] = remaining[idx]
                idx += 1

        return self._make_individual(child1_gene), self._make_individual(child2_gene)


def get_crossover_operator(name: str, **kwargs) -> CrossoverOperator:
    """
    工厂函数：根据名称获取交叉操作符

    Args:
        name: 交叉算子名称
            - 'single_point': 单点交叉
            - 'multi_point': 多点交叉
            - 'uniform': 均匀交叉
            - 'arithmetic': 算术交叉
            - 'blend': BLX-alpha 交叉
            - 'order': 顺序交叉 (OX)

    Returns:
        CrossoverOperator 实例
    """
    operators = {
        'single_point': SinglePointCrossover,
        'multi_point': MultiPointCrossover,
        'uniform': UniformCrossover,
        'arithmetic': ArithmeticCrossover,
        'blend': BlendCrossover,
        'order': OrderCrossover,
    }

    if name not in operators:
        raise ValueError(f"Unknown crossover operator: {name}. "
                         f"Available: {list(operators.keys())}")

    return operators[name](**kwargs)
