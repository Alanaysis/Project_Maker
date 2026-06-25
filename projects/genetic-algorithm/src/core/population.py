"""
种群类：管理一组个体
"""

from typing import Any, Callable, Dict, List
import numpy as np

from .individual import Individual


class Population:
    """
    种群管理类

    管理一组个体，提供初始化、评估、统计等功能
    """

    def __init__(self):
        """初始化空种群"""
        self.individuals: List[Individual] = []
        self.size: int = 0

    def initialize(self, size: int, chromosome_factory: Callable[[], List[Any]]):
        """
        初始化种群

        Args:
            size: 种群大小
            chromosome_factory: 染色体工厂函数，生成随机染色体
        """
        self.size = size
        self.individuals = [Individual(chromosome_factory()) for _ in range(size)]

    def evaluate(self, fitness_func: Callable[[List[Any]], float]):
        """
        评估所有个体的适应度

        Args:
            fitness_func: 适应度函数
        """
        for ind in self.individuals:
            ind.evaluate(fitness_func)

    def get_best(self) -> Individual:
        """
        获取最优个体

        Returns:
            适应度最高的个体
        """
        return max(self.individuals, key=lambda x: x.fitness)

    def get_worst(self) -> Individual:
        """
        获取最差个体

        Returns:
            适应度最低的个体
        """
        return min(self.individuals, key=lambda x: x.fitness)

    def get_statistics(self) -> Dict[str, float]:
        """
        获取种群统计信息

        Returns:
            包含 best, worst, average, std 的字典
        """
        fitnesses = [ind.fitness for ind in self.individuals]
        return {
            'best': max(fitnesses),
            'worst': min(fitnesses),
            'average': sum(fitnesses) / len(fitnesses),
            'std': float(np.std(fitnesses))
        }

    def replace(self, new_individuals: List[Individual]):
        """
        替换种群中的个体

        Args:
            new_individuals: 新的个体列表
        """
        self.individuals = new_individuals
        self.size = len(new_individuals)

    def __len__(self) -> int:
        return len(self.individuals)

    def __getitem__(self, index: int) -> Individual:
        return self.individuals[index]

    def __iter__(self):
        return iter(self.individuals)
