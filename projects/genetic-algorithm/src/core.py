"""
遗传算法 - 核心引擎模块
Genetic Algorithm - Core Engine Module

实现完整的遗传算法进化循环：

    世代模式 (Generational):
        1. 评估当前种群
        2. 选择父代
        3. 交叉产生子代种群
        4. 变异子代种群
        5. 用子代完全替换父代（+精英保留）
        6. 检查终止条件

    稳态模式 (Steady-State):
        1. 评估当前种群
        2. 选择一对父代
        3. 交叉产生子代
        4. 变异子代
        5. 用子代替换种群中最差的个体
        6. 重复步骤 2-5

GA 伪代码（世代模式）：
    1. 初始化种群 P(t)
    2. 评估 P(t)
    3. While 未收敛:
        a. 从 P(t) 选择父代
        b. 交叉产生子代 C(t)
        c. 变异 C(t)
        d. 评估 C(t)
        e. 选择 P(t+1) = C(t) ∪ 精英
        f. t = t + 1
    4. 返回最佳个体
"""

import random
import time
from typing import Callable, Optional, List, Tuple, Any, Dict
from dataclasses import dataclass, field

from .individual import Individual, Population
from .selection import get_selection_method, copy_individual
from .crossover import get_crossover_operator, CrossoverOperator
from .mutation import get_mutation_operator, MutationOperator
from .convergence import ConvergenceDetector, get_convergence_detector
from .config import GAParameters


@dataclass
class GAResult:
    """
    遗传算法优化结果

    Attributes:
        best_individual: 最佳个体
        best_fitness: 最佳适应度
        fitness_history: 每代最佳适应度历史
        avg_fitness_history: 每代平均适应度历史
        diversity_history: 每代种群多样性历史
        total_generations: 总进化代数
        elapsed_time: 运行时间（秒）
        converged: 是否收敛
        convergence_reason: 收敛原因
    """
    best_individual: Optional[Individual] = None
    best_fitness: float = 0.0
    fitness_history: List[float] = field(default_factory=list)
    avg_fitness_history: List[float] = field(default_factory=list)
    diversity_history: List[float] = field(default_factory=list)
    total_generations: int = 0
    elapsed_time: float = 0.0
    converged: bool = False
    convergence_reason: str = ""


class GeneticAlgorithm:
    """
    遗传算法主类

    支持世代模式和稳态模式两种进化策略。

    Usage:
        # 创建 GA 实例
        ga = GeneticAlgorithm(
            population_size=100,
            gene_length=30,
            fitness_func=my_fitness_function,
            bounds=(0, 1),  # 二进制编码范围
            crossover_rate=0.8,
            mutation_rate=0.01,
            max_generations=500,
            selection_method='tournament',
            tournament_size=3,
            crossover_operator='single_point',
            mutation_operator='bit_flip',
            elite_count=2,
        )

        # 运行优化
        result = ga.optimize()

        # 查看结果
        print(f"Best fitness: {result.best_fitness}")
        print(f"Best gene: {result.best_individual.gene}")
    """

    def __init__(self, **kwargs):
        """
        初始化遗传算法

        参数通过 **kwargs 传入，兼容 GAParameters 的所有字段。
        """
        self.params = GAParameters(**kwargs)

        # 随机种子设置
        if self.params.seed is not None:
            random.seed(self.params.seed)

        # 初始化组件
        self._selection = get_selection_method(
            self.params.selection_method,
            tournament_size=self.params.tournament_size
        )
        self._crossover = get_crossover_operator(
            self.params.crossover_operator,
            **self.params.crossover_params
        )
        self._mutation = get_mutation_operator(
            self.params.mutation_operator,
            **self.params.mutation_params
        )
        self._convergence_detector = get_convergence_detector(
            self.params.convergence_detector,
            **self.params.convergence_params
        )

        # 内部状态
        self.population: Optional[Population] = None
        self.result: Optional[GAResult] = None

    def optimize(self, fitness_func: Optional[Callable] = None,
                 initial_population: Optional[Population] = None) -> GAResult:
        """
        执行遗传算法优化

        Args:
            fitness_func: 适应度函数，接收基因列表，返回适应度值
            initial_population: 可选的初始种群

        Returns:
            GAResult: 优化结果
        """
        start_time = time.time()
        fitness_history = []
        avg_fitness_history = []
        diversity_history = []
        convergence_history = []

        # 初始化种群
        if initial_population is not None:
            self.population = initial_population
        else:
            self.population = self._initialize_population()

        # 评估初始种群
        if fitness_func:
            self.population.evaluate(fitness_func)

        convergence_history.append(self.population.best_fitness)

        # 世代进化
        for generation in range(self.params.max_generations):
            # 记录历史
            fitness_history.append(self.population.best_fitness)
            avg_fitness_history.append(self.population.averaged_fitness)
            diversity_history.append(self.population.get_diversity())

            # 检查是否达到目标适应度
            if (self.params.stop_fitness is not None and
                    self.population.best_fitness >= self.params.stop_fitness):
                if self.params.verbose:
                    print(f"  [Gen {generation}] 达到目标适应度 {self.params.stop_fitness}!")
                self.params.max_generations = generation + 1
                break

            # 执行一代进化
            self._evolve(fitness_func)

            # 检查收敛
            if self._convergence_detector.check_convergence(
                self.population, generation, convergence_history
            ):
                if self.params.verbose:
                    print(f"  [Gen {generation}] 检测到收敛!")
                self.result = GAResult(
                    best_individual=self.population.get_best(),
                    best_fitness=self.population.best_fitness,
                    fitness_history=fitness_history,
                    avg_fitness_history=avg_fitness_history,
                    diversity_history=diversity_history,
                    total_generations=generation + 1,
                    elapsed_time=time.time() - start_time,
                    converged=True,
                    convergence_reason="early_convergence"
                )
                return self.result

            if self.params.verbose and (generation % 50 == 0 or generation == self.params.max_generations - 1):
                print(f"  [Gen {generation:4d}] Best: {self.population.best_fitness:10.4f}  "
                      f"Avg: {self.population.averaged_fitness:10.4f}  "
                      f"Div: {self.population.get_diversity():10.4f}")

        # 完成优化
        elapsed_time = time.time() - start_time

        self.result = GAResult(
            best_individual=self.population.get_best(),
            best_fitness=self.population.best_fitness,
            fitness_history=fitness_history,
            avg_fitness_history=avg_fitness_history,
            diversity_history=diversity_history,
            total_generations=self.params.max_generations,
            elapsed_time=elapsed_time,
            converged=False,
            convergence_reason="max_generations_reached"
        )

        if self.params.verbose:
            print(f"\n  优化完成! 最佳适应度: {self.result.best_fitness:.4f}  "
                  f"耗时: {self.result.elapsed_time:.2f}s")

        return self.result

    def _initialize_population(self) -> Population:
        """初始化种群（随机生成）

        根据编码类型（二进制/实数/排列）生成初始个体。
        当前默认生成二进制编码个体。
        """
        individuals = []
        for _ in range(self.params.population_size):
            gene = [random.randint(0, 1) for _ in range(self.params.population_size)]
            individuals.append(Individual(gene=gene, fitness=0.0))
        return Population(size=self.params.population_size, individuals=individuals)

    def _evolve(self, fitness_func: Optional[Callable] = None):
        """执行一代进化

        根据稳态模式参数决定使用世代模式还是稳态模式。
        """
        if self.params.steady_state_rate > 0:
            self._evolve_steady_state(fitness_func)
        else:
            self._evolve_generational(fitness_func)

    def _evolve_generational(self, fitness_func: Optional[Callable] = None):
        """
        世代模式进化

        1. 选择父代
        2. 交叉产生子代种群
        3. 变异子代种群
        4. 评估子代
        5. 精英保留：将精英个体和子代合并，选出下一代
        """
        # 1. 选择父代（需要更多个体来产生子代）
        num_parents = self.params.population_size
        parents = self._selection.select(self.population, num_parents)

        # 2. 交叉产生子代
        children = []
        i = 0
        while i < len(parents) - 1:
            parent1, parent2 = parents[i], parents[i + 1]

            if random.random() < self.params.crossover_rate:
                child1, child2 = self._crossover.crossover(parent1, parent2)
            else:
                child1, child2 = copy_individual(parent1), copy_individual(parent2)

            # 3. 变异子代
            child1 = self._mutation.mutate(child1)
            child2 = self._mutation.mutate(child2)

            # 4. 评估子代
            if fitness_func:
                child1.fitness = fitness_func(child1.gene)
                child2.fitness = fitness_func(child2.gene)

            children.append(child1)
            children.append(child2)
            i += 2

        # 5. 精英保留
        elite = [copy_individual(ind) for ind in
                 sorted(self.population.individuals,
                        key=lambda x: x.fitness, reverse=True)[:self.params.elite_count]]

        # 用子代 + 精英构建新种群
        remaining = self.params.population_size - len(elite)
        new_individuals = elite + children[:remaining]

        self.population = Population(
            size=self.params.population_size,
            individuals=new_individuals
        )
        self.population._update_statistics()

    def _evolve_steady_state(self, fitness_func: Optional[Callable] = None):
        """
        稳态模式进化

        每次只产生少量子代，替换种群中最差的个体。
        这种方式种群变化更平滑，探索更充分。
        """
        num_new = int(self.params.population_size * self.params.steady_state_rate)
        new_individuals = []

        for _ in range(num_new):
            # 选择一对父代
            parents = self._selection.select(self.population, 2)

            # 交叉
            if random.random() < self.params.crossover_rate:
                child1, child2 = self._crossover.crossover(parents[0], parents[1])
            else:
                child1, child2 = copy_individual(parents[0]), copy_individual(parents[1])

            # 变异
            child1 = self._mutation.mutate(child1)
            child2 = self._mutation.mutate(child2)

            # 评估
            if fitness_func:
                child1.fitness = fitness_func(child1.gene)
                child2.fitness = fitness_func(child2.gene)

            new_individuals.extend([child1, child2])

        # 合并并保留最佳个体
        all_individuals = self.population.individuals + new_individuals
        all_individuals.sort(key=lambda x: x.fitness, reverse=True)
        self.population = Population(
            size=self.params.population_size,
            individuals=all_individuals[:self.params.population_size]
        )
        self.population._update_statistics()
