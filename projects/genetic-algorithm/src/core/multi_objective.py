"""
多目标优化：NSGA-II 算法实现

非支配排序遗传算法 (Non-dominated Sorting Genetic Algorithm II)
用于求解多目标优化问题，找到 Pareto 最优解集。
"""

from typing import Any, Callable, Dict, List, Optional, Tuple
import random
import numpy as np

from .individual import Individual
from .population import Population


class MultiObjectiveProblem:
    """
    多目标优化问题基类

    子类需要实现多个目标函数
    """

    def create_individual(self) -> List[Any]:
        """创建随机个体"""
        raise NotImplementedError

    def objectives(self, chromosome: List[Any]) -> List[float]:
        """
        计算多个目标函数值

        Args:
            chromosome: 染色体

        Returns:
            目标函数值列表（所有目标都是最小化）
        """
        raise NotImplementedError

    def display(self, chromosome: List[Any]) -> None:
        """显示解"""
        raise NotImplementedError


def dominates(obj1: List[float], obj2: List[float]) -> bool:
    """
    判断 obj1 是否支配 obj2

    obj1 支配 obj2 当且仅当：
    1. obj1 在所有目标上都不比 obj2 差
    2. obj1 至少在一个目标上严格优于 obj2

    Args:
        obj1: 第一个解的目标值列表
        obj2: 第二个解的目标值列表

    Returns:
        obj1 是否支配 obj2
    """
    all_less_equal = all(a <= b for a, b in zip(obj1, obj2))
    any_less = any(a < b for a, b in zip(obj1, obj2))
    return all_less_equal and any_less


def fast_non_dominated_sort(population: List[Tuple[Individual, List[float]]]) -> List[List[int]]:
    """
    快速非支配排序

    将种群分为多个前沿 (front)，第一个前沿是最优的非支配解集。

    Args:
        population: 种群中每个个体及其目标值的列表

    Returns:
        前沿列表，每个前沿包含个体的索引
    """
    n = len(population)

    # 支配计数和被支配集合
    domination_count = [0] * n  # 被多少个个体支配
    dominated_set = [[] for _ in range(n)]  # 支配哪些个体

    fronts = [[]]

    for i in range(n):
        for j in range(i + 1, n):
            obj_i = population[i][1]
            obj_j = population[j][1]

            if dominates(obj_i, obj_j):
                dominated_set[i].append(j)
                domination_count[j] += 1
            elif dominates(obj_j, obj_i):
                dominated_set[j].append(i)
                domination_count[i] += 1

        if domination_count[i] == 0:
            fronts[0].append(i)

    # 生成后续前沿
    current_front = 0
    while fronts[current_front]:
        next_front = []
        for i in fronts[current_front]:
            for j in dominated_set[i]:
                domination_count[j] -= 1
                if domination_count[j] == 0:
                    next_front.append(j)
        current_front += 1
        if next_front:
            fronts.append(next_front)
        else:
            break

    return fronts


def crowding_distance_assignment(population: List[Tuple[Individual, List[float]]], front: List[int]) -> Dict[int, float]:
    """
    拥挤度距离计算

    拥挤度距离用于保持种群多样性，距离越大表示个体越"孤立"。

    Args:
        population: 种群中每个个体及其目标值的列表
        front: 同一前沿中的个体索引列表

    Returns:
        每个个体的拥挤度距离
    """
    distances = {i: 0.0 for i in front}
    n_objectives = len(population[front[0]][1]) if front else 0

    if len(front) <= 2:
        for i in front:
            distances[i] = float('inf')
        return distances

    for m in range(n_objectives):
        # 按第 m 个目标排序
        sorted_front = sorted(front, key=lambda i: population[i][1][m])

        # 边界个体距离为无穷大
        distances[sorted_front[0]] = float('inf')
        distances[sorted_front[-1]] = float('inf')

        # 目标值范围
        obj_min = population[sorted_front[0]][1][m]
        obj_max = population[sorted_front[-1]][1][m]

        if obj_max == obj_min:
            continue

        # 计算中间个体的拥挤度距离
        for k in range(1, len(sorted_front) - 1):
            distances[sorted_front[k]] += (
                (population[sorted_front[k + 1]][1][m] - population[sorted_front[k - 1]][1][m])
                / (obj_max - obj_min)
            )

    return distances


class NSGA2Engine:
    """
    NSGA-II 多目标优化引擎

    实现非支配排序和拥挤度距离选择的多目标遗传算法。
    """

    def __init__(
        self,
        problem: MultiObjectiveProblem,
        population_size: int = 100,
        crossover_rate: float = 0.9,
        mutation_rate: float = 0.1,
    ):
        """
        初始化 NSGA-II 引擎

        Args:
            problem: 多目标优化问题
            population_size: 种群大小（应为偶数）
            crossover_rate: 交叉概率
            mutation_rate: 变异概率
        """
        self.problem = problem
        self.population_size = population_size
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate

        # 初始化种群
        self.population: List[Individual] = []
        for _ in range(population_size):
            ind = Individual(problem.create_individual())
            self.population.append(ind)

        # 历史记录
        self.history: Dict[str, List] = {
            'pareto_front_size': [],
            'hypervolume': [],
        }

        self.generation = 0

    def _evaluate_population(self) -> List[Tuple[Individual, List[float]]]:
        """评估种群中所有个体的目标值"""
        evaluated = []
        for ind in self.population:
            objs = self.problem.objectives(ind.chromosome)
            ind.fitness = -sum(objs)  # 用于兼容性，实际使用 objectives
            evaluated.append((ind, objs))
        return evaluated

    def _tournament_selection(self, evaluated: List[Tuple[Individual, List[float]]], fronts: List[List[int]], crowding_distances: Dict[int, float]) -> Individual:
        """
        锦标赛选择（基于非支配排序和拥挤度距离）

        Args:
            evaluated: 评估后的种群
            fronts: 非支配前沿
            crowding_distances: 拥挤度距离

        Returns:
            选中的个体
        """
        # 随机选择两个个体
        i, j = random.sample(range(len(evaluated)), 2)

        # 找到每个个体所在的前沿
        front_i = next(f_idx for f_idx, front in enumerate(fronts) if i in front)
        front_j = next(f_idx for f_idx, front in enumerate(fronts) if j in front)

        # 优先选择前沿编号小的（更优）
        if front_i < front_j:
            return evaluated[i][0].copy()
        elif front_j < front_i:
            return evaluated[j][0].copy()
        else:
            # 同一前沿，选择拥挤度距离大的（多样性）
            if crowding_distances.get(i, 0) >= crowding_distances.get(j, 0):
                return evaluated[i][0].copy()
            else:
                return evaluated[j][0].copy()

    def _crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        """模拟二进制交叉 (SBX) 或简单均匀交叉"""
        if random.random() > self.crossover_rate:
            return parent1.copy(), parent2.copy()

        child1_chromosome = []
        child2_chromosome = []

        for g1, g2 in zip(parent1.chromosome, parent2.chromosome):
            if isinstance(g1, (int, float)) and isinstance(g2, (int, float)):
                # 实数编码：算术交叉
                alpha = random.random()
                child1_chromosome.append(alpha * g1 + (1 - alpha) * g2)
                child2_chromosome.append((1 - alpha) * g1 + alpha * g2)
            else:
                # 其他编码：均匀交叉
                if random.random() < 0.5:
                    child1_chromosome.append(g1)
                    child2_chromosome.append(g2)
                else:
                    child1_chromosome.append(g2)
                    child2_chromosome.append(g1)

        return Individual(child1_chromosome), Individual(child2_chromosome)

    def _mutate(self, individual: Individual) -> Individual:
        """变异操作"""
        mutated = individual.copy()
        for i in range(len(mutated.chromosome)):
            if random.random() < self.mutation_rate:
                if isinstance(mutated.chromosome[i], float):
                    mutated.chromosome[i] += random.gauss(0, 1.0)
                elif isinstance(mutated.chromosome[i], int):
                    mutated.chromosome[i] = random.randint(0, 1)  # 二进制翻转
        return mutated

    def evolve_one_generation(self):
        """进化一代"""
        # 评估种群
        evaluated = self._evaluate_population()

        # 非支配排序
        fronts = fast_non_dominated_sort(evaluated)

        # 计算拥挤度距离
        all_crowding_distances = {}
        for front in fronts:
            distances = crowding_distance_assignment(evaluated, front)
            all_crowding_distances.update(distances)

        # 记录统计信息
        self.history['pareto_front_size'].append(len(fronts[0]))

        # 生成子代
        offspring = []
        while len(offspring) < self.population_size:
            parent1 = self._tournament_selection(evaluated, fronts, all_crowding_distances)
            parent2 = self._tournament_selection(evaluated, fronts, all_crowding_distances)

            child1, child2 = self._crossover(parent1, parent2)
            child1 = self._mutate(child1)
            child2 = self._mutate(child2)

            offspring.extend([child1, child2])

        # 合并父代和子代
        combined = self.population + offspring[:self.population_size]
        combined_evaluated = [(ind, self.problem.objectives(ind.chromosome)) for ind in combined]

        # 非支配排序
        combined_fronts = fast_non_dominated_sort(combined_evaluated)

        # 选择新种群
        new_population = []
        for front in combined_fronts:
            if len(new_population) + len(front) <= self.population_size:
                # 整个前沿可以加入
                new_population.extend([combined[i] for i in front])
            else:
                # 需要根据拥挤度距离选择部分个体
                distances = crowding_distance_assignment(combined_evaluated, front)
                sorted_front = sorted(front, key=lambda i: distances.get(i, 0), reverse=True)
                remaining = self.population_size - len(new_population)
                new_population.extend([combined[i] for i in sorted_front[:remaining]])
                break

        self.population = new_population
        self.generation += 1

    def run(self, generations: int = 100, verbose: bool = True) -> List[Individual]:
        """
        运行 NSGA-II 算法

        Args:
            generations: 迭代代数
            verbose: 是否打印进度

        Returns:
            Pareto 最优解集
        """
        for gen in range(generations):
            self.evolve_one_generation()

            if verbose and gen % 10 == 0:
                evaluated = self._evaluate_population()
                fronts = fast_non_dominated_sort(evaluated)
                print(f"Generation {gen}: Pareto front size = {len(fronts[0])}")

        # 返回 Pareto 最优解
        evaluated = self._evaluate_population()
        fronts = fast_non_dominated_sort(evaluated)
        pareto_front = [evaluated[i][0] for i in fronts[0]]
        return pareto_front

    def get_pareto_front(self) -> List[Tuple[Individual, List[float]]]:
        """
        获取当前 Pareto 前沿

        Returns:
            Pareto 前沿中的个体及其目标值
        """
        evaluated = self._evaluate_population()
        fronts = fast_non_dominated_sort(evaluated)
        return [(evaluated[i][0], evaluated[i][1]) for i in fronts[0]]
