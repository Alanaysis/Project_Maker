"""
遗传算法 - 选择方法模块
Genetic Algorithm - Selection Methods Module

选择操作决定哪些个体可以进入下一代。
核心思想：适应度高的个体有更大概率被选中（"适者生存"）。

选择方法：
    1. 锦标赛选择 (Tournament Selection)
       - 随机选 k 个个体，选其中最优的
       - 优点：参数少，并行友好
       - 缺点：选择压力固定

    2. 轮盘赌选择 (Roulette Wheel Selection)
       - 按适应度比例分配选中概率
       - 优点：简单直观
       - 缺点：适应度需为正，易早熟

    3. 排名选择 (Rank-Based Selection)
       - 按排名而非原始适应度分配概率
       - 优点：避免适应度差异过大
       - 缺点：需排序

    4. 精英保留 (Elitism)
       - 确保最佳个体直接进入下一代
       - 优点：保证最优解不丢失
       - 缺点：可能降低多样性
"""

import random
from typing import List, Optional, Tuple
from src.core.individual import Individual
from src.core.population import Population


class SelectionMethod:
    """选择方法的基类"""
    name: str = "base"

    def select(self, population: Population, count: int) -> List[Individual]:
        raise NotImplementedError


class TournamentSelection(SelectionMethod):
    """
    锦标赛选择 (Tournament Selection)

    每次从种群中随机抽取 tournament_size 个个体，
    从中选出适应度最高的作为父代。

    参数：
        tournament_size: 锦标赛大小
            - 越大：选择压力越大，收敛越快，但多样性丧失快
            - 越小：选择压力越小，探索更强，但收敛慢
            - 通常取值：2-5
    """
    name = "tournament"

    def __init__(self, tournament_size: int = 3):
        self.tournament_size = tournament_size

    def select(self, population: Population, count: int) -> List[Individual]:
        selected = []
        for _ in range(count):
            # 随机抽取 tournament_size 个个体
            tournament = random.sample(population.individuals,
                                       min(self.tournament_size, len(population)))
            # 选出锦标赛中的最优个体
            winner = max(tournament, key=lambda ind: ind.fitness)
            selected.append(copy_individual(winner))
        return selected


class RouletteWheelSelection(SelectionMethod):
    """
    轮盘赌选择 (Roulette Wheel Selection)

    每个个体被选中的概率与其适应度成正比。
    适应度越高，轮盘上占据的扇区越大，被选中的概率越高。

    注意：
        - 所有适应度必须为正数
        - 如果适应度有负数，需要先做平移变换
        - 当个体间适应度差异大时，高适应度个体可能垄断选择
    """
    name = "roulette"

    def __init__(self):
        pass

    def select(self, population: Population, count: int) -> List[Individual]:
        if not population.individuals:
            return []

        # 确保所有适应度为正
        fitnesses = [ind.fitness for ind in population.individuals]
        min_fitness = min(fitnesses)

        # 如果存在负适应度，做平移
        if min_fitness < 0:
            fitnesses = [f - min_fitness + 1e-6 for f in fitnesses]
        else:
            fitnesses = [f + 1e-6 for f in fitnesses]

        total_fitness = sum(fitnesses)
        if total_fitness <= 0:
            # 退化到随机选择
            return [copy_individual(random.choice(population.individuals))
                    for _ in range(count)]

        # 计算累积概率
        probabilities = [f / total_fitness for f in fitnesses]

        selected = []
        for _ in range(count):
            # 轮盘赌选择
            r = random.random()
            cumulative = 0.0
            for i, prob in enumerate(probabilities):
                cumulative += prob
                if r <= cumulative:
                    selected.append(copy_individual(population.individuals[i]))
                    break
            else:
                # 浮点误差处理，选最后一个
                selected.append(copy_individual(population.individuals[-1]))

        return selected


class RankSelection(SelectionMethod):
    """
    排名选择 (Rank-Based Selection)

    将个体按适应度排序后，按排名分配选择概率。
    排名最高的个体获得最大概率，排名最低的获得最小概率。

    优点：
        - 不受适应度绝对值影响
        - 避免早熟收敛
        - 选择压力可控

    参数：
        min_prob: 最差的个体被选中的最小概率
        max_prob: 最好的个体被选中的最大概率
    """
    name = "rank"

    def __init__(self, min_prob: float = 0.1, max_prob: float = 0.9):
        self.min_prob = min_prob
        self.max_prob = max_prob

    def select(self, population: Population, count: int) -> List[Individual]:
        if not population.individuals:
            return []

        # 按适应度排序（从小到大）
        sorted_pop = sorted(population.individuals, key=lambda ind: ind.fitness)

        n = len(sorted_pop)
        # 按排名分配概率
        probabilities = []
        for i, ind in enumerate(sorted_pop):
            # 线性排名
            rank = i + 1  # 排名从 1 开始
            prob = self.min_prob + (self.max_prob - self.min_prob) * (rank - 1) / (n - 1) if n > 1 else self.max_prob
            probabilities.append(prob)

        total_prob = sum(probabilities)
        probabilities = [p / total_prob for p in probabilities]

        selected = []
        for _ in range(count):
            r = random.random()
            cumulative = 0.0
            for i, prob in enumerate(probabilities):
                cumulative += prob
                if r <= cumulative:
                    selected.append(copy_individual(sorted_pop[i]))
                    break
            else:
                selected.append(copy_individual(sorted_pop[-1]))

        return selected


class ElitismSelection(SelectionMethod):
    """
    精英保留选择 (Elitism Selection)

    直接选择种群中适应度最高的 k 个个体。
    精英保留是 GA 的重要策略，确保最优解不会在进化过程中丢失。

    通常与其他选择方法结合使用：
        - 先用精英保留选出最佳个体
        - 其余位置用其他选择方法填充

    参数：
        elite_count: 精英个体数量
            - 通常取 1-5
            - 过多会降低多样性
    """
    name = "elitism"

    def __init__(self, elite_count: int = 1):
        self.elite_count = elite_count

    def select(self, population: Population, count: int) -> List[Individual]:
        if not population.individuals:
            return []

        sorted_pop = sorted(population.individuals,
                            key=lambda ind: ind.fitness, reverse=True)

        # 取前 elite_count 个精英
        elite = [copy_individual(ind) for ind in sorted_pop[:self.elite_count]]

        # 如果请求数量少于精英数量，截断
        if count <= self.elite_count:
            return elite[:count]

        # 其余位置也选精英（或可以结合其他选择方法）
        remaining = count - len(elite)
        for i in range(remaining):
            idx = i % len(sorted_pop)
            elite.append(copy_individual(sorted_pop[idx]))

        return elite


def copy_individual(individual: Individual) -> Individual:
    """深拷贝个体"""
    ind = Individual(individual.chromosome.copy()); ind.fitness = individual.fitness; return ind


def get_selection_method(name: str, **kwargs):
    """
    工厂函数：根据名称获取选择方法实例

    Args:
        name: 选择方法名称
            - 'tournament': 锦标赛选择
            - 'roulette': 轮盘赌选择
            - 'rank': 排名选择
            - 'elitism': 精英保留

    Returns:
        SelectionMethod 实例
    """
    methods = {
        'tournament': TournamentSelection,
        'roulette': RouletteWheelSelection,
        'rank': RankSelection,
        'elitism': ElitismSelection,
    }

    if name not in methods:
        raise ValueError(f"Unknown selection method: {name}. "
                         f"Available: {list(methods.keys())}")

    return methods[name](**kwargs)
