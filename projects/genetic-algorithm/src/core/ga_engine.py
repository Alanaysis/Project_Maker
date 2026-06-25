"""
遗传算法引擎：核心算法实现
"""

from typing import Dict, List, Optional

from .individual import Individual
from .population import Population
from ..operators.selection import SelectionOperator, TournamentSelection, ElitismSelection
from ..operators.crossover import CrossoverOperator, SinglePointCrossover
from ..operators.mutation import MutationOperator, BitFlipMutation, AdaptiveMutation
from ..problems.base import Problem


class GAEngine:
    """
    遗传算法核心引擎

    协调种群、选择、交叉、变异等组件，执行遗传算法流程。
    支持精英保留策略和自适应变异。
    """

    def __init__(
        self,
        problem: Problem,
        population_size: int = 100,
        selection: Optional[SelectionOperator] = None,
        crossover: Optional[CrossoverOperator] = None,
        mutation: Optional[MutationOperator] = None,
        elitism_count: int = 0,
    ):
        """
        初始化 GA 引擎

        Args:
            problem: 优化问题
            population_size: 种群大小
            selection: 选择算子
            crossover: 交叉算子
            mutation: 变异算子
            elitism_count: 精英保留数量（0 表示不使用精英保留）
        """
        self.problem = problem
        self.population_size = population_size
        self.elitism_count = elitism_count

        # 默认算子
        self.selection = selection or TournamentSelection()
        self.crossover = crossover or SinglePointCrossover()
        self.mutation = mutation or BitFlipMutation()

        # 初始化种群
        self.population = Population()
        self.population.initialize(population_size, problem.create_individual)

        # 历史记录
        self.history: Dict[str, List] = {
            'best_fitness': [],
            'average_fitness': [],
            'best_individual': None,
            'mutation_rate': [],
        }

        # 当前代数
        self.generation = 0

    def evolve_one_generation(self):
        """
        进化一代

        执行一次完整的遗传算法循环：评估 → 精英保留 → 选择 → 交叉 → 变异
        """
        # 评估种群
        self.population.evaluate(self.problem.fitness)

        # 记录统计信息
        stats = self.population.get_statistics()
        self.history['best_fitness'].append(stats['best'])
        self.history['average_fitness'].append(stats['average'])

        # 更新自适应变异率
        if isinstance(self.mutation, AdaptiveMutation):
            self.mutation.update(stats['best'])
            self.history['mutation_rate'].append(self.mutation.current_mutation_rate)

        # 精英保留
        elites = []
        if self.elitism_count > 0:
            elitism = ElitismSelection()
            elites = elitism.select(self.population, self.elitism_count)

        # 选择父代
        parents = self.selection.select(self.population, self.population_size)

        # 交叉产生子代
        offspring = []
        for i in range(0, len(parents) - 1, 2):
            child1, child2 = self.crossover.crossover(parents[i], parents[i + 1])
            offspring.extend([child1, child2])

        # 处理奇数情况
        if len(parents) % 2 == 1:
            offspring.append(parents[-1].copy())

        # 变异
        offspring = [self.mutation.mutate(ind) for ind in offspring]

        # 将精英个体加入新种群
        if elites:
            # 替换最差的个体为精英
            offspring.sort(key=lambda x: x.fitness, reverse=True)
            offspring = elites + offspring[self.elitism_count:]

        # 更新种群
        self.population.replace(offspring)

        # 更新代数
        self.generation += 1

    def run(self, generations: int = 100, verbose: bool = True) -> Individual:
        """
        运行遗传算法

        Args:
            generations: 迭代代数
            verbose: 是否打印进度

        Returns:
            最优个体
        """
        for gen in range(generations):
            self.evolve_one_generation()

            if verbose and gen % 10 == 0:
                stats = self.population.get_statistics()
                print(f"Generation {gen}: Best={stats['best']:.4f}, Avg={stats['average']:.4f}")

        # 返回最优解
        self.population.evaluate(self.problem.fitness)
        best = self.population.get_best()
        self.history['best_individual'] = best
        return best

    def get_best_solution(self) -> Individual:
        """
        获取当前最优解

        Returns:
            当前种群中最优的个体
        """
        self.population.evaluate(self.problem.fitness)
        return self.population.get_best()

    def get_convergence_data(self) -> Dict[str, List]:
        """
        获取收敛数据

        Returns:
            包含 best_fitness 和 average_fitness 的字典
        """
        return self.history
