"""
遗传算法 - 个体与种群管理模块
Genetic Algorithm - Individual and Population Management Module

本模块定义了 GA 中的基本数据结构：
- Individual: 代表一个可能的解（染色体）
- Population: 代表个体集合（种群）

GA 核心思想：
    用"染色体"编码问题的解空间
    用"种群"并行探索多个区域
    通过"适者生存"逐步逼近最优解
"""

import random
import copy
from dataclasses import dataclass, field
from typing import List, Optional, Callable, Any, Tuple


@dataclass
class Individual:
    """
    个体（染色体）类

    每个个体代表优化问题的一个潜在解。
    个体包含：
        - gene: 基因序列（编码方案取决于问题）
        - fitness: 适应度值（由适应度函数计算）

    编码方式：
        - 二进制编码: gene = [0, 1, 1, 0, ...]
        - 实数编码: gene = [x1, x2, x3, ...]
        - 排列编码: gene = [3, 1, 4, 2, ...]（用于 TSP 等）
    """
    gene: List[Any] = field(default_factory=list)
    fitness: float = 0.0

    def __post_init__(self):
        if not self.gene:
            self.gene = []
        self.fitness = 0.0

    def __copy__(self):
        """深拷贝个体"""
        return Individual(
            gene=self.gene.copy(),
            fitness=self.fitness
        )

    def __deepcopy__(self, memo):
        """深度拷贝个体"""
        return Individual(
            gene=copy.deepcopy(self.gene),
            fitness=self.fitness
        )

    def __lt__(self, other):
        """支持排序比较"""
        return self.fitness < other.fitness

    def __le__(self, other):
        return self.fitness <= other.fitness

    def __gt__(self, other):
        return self.fitness > other.fitness

    def __ge__(self, other):
        return self.fitness >= other.fitness

    def __eq__(self, other):
        if not isinstance(other, Individual):
            return False
        return self.gene == other.gene

    def __hash__(self):
        return hash(tuple(self.gene))

    def __repr__(self):
        return f"Individual(fitness={self.fitness:.4f}, gene={self.gene[:10]}{'...' if len(self.gene) > 10 else ''})"


class Population:
    """
    种群类

    维护一组个体，提供种群级别的操作：
    - 初始化（随机生成）
    - 统计信息（最佳/平均/最差适应度）
    - 排序和选择
    - 种群多样性分析

    种群大小是 GA 的关键参数：
        - 太小：探索不足，容易早熟收敛
        - 太大：计算开销大
        - 通常取值：50-200
    """

    def __init__(self, size: int, individuals: Optional[List[Individual]] = None):
        self.size = size
        self.individuals: List[Individual] = individuals if individuals else []
        self.best_individual: Optional[Individual] = None
        self.best_fitness: float = float('-inf')
        self.averaged_fitness: float = 0.0

    def __len__(self):
        return len(self.individuals)

    def __iter__(self):
        return iter(self.individuals)

    def __getitem__(self, index):
        return self.individuals[index]

    def __repr__(self):
        return (f"Population(size={self.size}, count={len(self.individuals)}, "
                f"best_fitness={self.best_fitness:.4f}, avg_fitness={self.averaged_fitness:.4f})")

    def evaluate(self, fitness_func: Callable):
        """
        评估种群中所有个体的适应度

        Args:
            fitness_func: 适应度函数，接收个体基因列表，返回适应度值
        """
        for individual in self.individuals:
            individual.fitness = fitness_func(individual.gene)
        self._update_statistics()

    def _update_statistics(self):
        """更新种群统计信息"""
        if not self.individuals:
            return

        fitnesses = [ind.fitness for ind in self.individuals]
        self.best_fitness = max(fitnesses)
        self.averaged_fitness = sum(fitnesses) / len(fitnesses)
        self.best_individual = max(self.individuals, key=lambda ind: ind.fitness)

    def sort_by_fitness(self, descending: bool = True):
        """按适应度排序"""
        self.individuals.sort(key=lambda ind: ind.fitness, reverse=descending)

    def get_best(self) -> Optional[Individual]:
        """获取当前种群中最佳个体"""
        if not self.individuals:
            return None
        return max(self.individuals, key=lambda ind: ind.fitness)

    def get_worst(self) -> Optional[Individual]:
        """获取当前种群中最差个体"""
        if not self.individuals:
            return None
        return min(self.individuals, key=lambda ind: ind.fitness)

    def get_diversity(self) -> float:
        """
        计算种群多样性（基因差异的平均值）

        多样性是 GA 健康度的重要指标：
            - 高多样性：探索充分，但可能收敛慢
            - 低多样性：可能早熟收敛，需要增加变异率
        """
        if len(self.individuals) < 2:
            return 0.0

        total_distance = 0.0
        count = 0

        for i in range(len(self.individuals)):
            for j in range(i + 1, len(self.individuals)):
                total_distance += self._gene_distance(
                    self.individuals[i].gene,
                    self.individuals[j].gene
                )
                count += 1

        return total_distance / count if count > 0 else 0.0

    @staticmethod
    def _gene_distance(gene1: List, gene2: List) -> float:
        """计算两个基因序列的距离"""
        if len(gene1) != len(gene2):
            return float('inf')

        if isinstance(gene1[0], (int, float)) if gene1 else False:
            return sum((a - b) ** 2 for a, b in zip(gene1, gene2)) ** 0.5
        else:
            return sum(1 for a, b in zip(gene1, gene2) if a != b)
