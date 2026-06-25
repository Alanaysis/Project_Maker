"""
选择算子：从种群中选择个体作为父代
"""

from abc import ABC, abstractmethod
from typing import List
import random

import numpy as np

from ..core.individual import Individual
from ..core.population import Population


class SelectionOperator(ABC):
    """选择算子基类"""

    @abstractmethod
    def select(self, population: Population, n: int) -> List[Individual]:
        """
        从种群中选择 n 个个体

        Args:
            population: 种群
            n: 选择数量

        Returns:
            选中的个体列表
        """
        pass


class RouletteWheelSelection(SelectionOperator):
    """
    轮盘赌选择：适应度越高，被选中概率越大

    每个个体被选中的概率 = 个体适应度 / 总适应度
    """

    def select(self, population: Population, n: int) -> List[Individual]:
        fitnesses = [ind.fitness for ind in population.individuals]

        # 处理负适应度
        min_fitness = min(fitnesses)
        if min_fitness < 0:
            fitnesses = [f - min_fitness + 1 for f in fitnesses]

        total_fitness = sum(fitnesses)

        # 处理总适应度为 0 的情况
        if total_fitness == 0:
            # 随机选择
            indices = random.choices(range(len(population.individuals)), k=n)
        else:
            probabilities = [f / total_fitness for f in fitnesses]
            indices = np.random.choice(
                len(population.individuals),
                size=n,
                p=probabilities,
                replace=True
            )

        return [population.individuals[i].copy() for i in indices]


class TournamentSelection(SelectionOperator):
    """
    锦标赛选择：随机选择 k 个个体，取适应度最高的

    通过调整锦标赛大小 k 可以控制选择压力
    """

    def __init__(self, tournament_size: int = 3):
        """
        初始化锦标赛选择

        Args:
            tournament_size: 锦标赛大小（每次参与竞争的个体数）
        """
        self.tournament_size = tournament_size

    def select(self, population: Population, n: int) -> List[Individual]:
        selected = []
        for _ in range(n):
            # 随机选择 tournament_size 个个体
            tournament = random.sample(population.individuals, self.tournament_size)
            # 选择适应度最高的
            winner = max(tournament, key=lambda x: x.fitness)
            selected.append(winner.copy())
        return selected


class ElitismSelection(SelectionOperator):
    """
    精英保留选择：保留适应度最高的 n 个个体

    确保最优个体不丢失，通常与其他选择算子结合使用
    """

    def select(self, population: Population, n: int) -> List[Individual]:
        sorted_pop = sorted(population.individuals, key=lambda x: x.fitness, reverse=True)
        return [ind.copy() for ind in sorted_pop[:n]]
