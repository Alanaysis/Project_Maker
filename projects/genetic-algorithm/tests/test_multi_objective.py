"""
多目标优化测试
"""

import pytest
import sys
import os
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.multi_objective import (
    dominates,
    fast_non_dominated_sort,
    crowding_distance_assignment,
    MultiObjectiveProblem,
    NSGA2Engine,
)
from src.core.individual import Individual


class TestDominates:
    """支配关系测试"""

    def test_dominates_true(self):
        """测试支配关系成立"""
        # [1, 2] 支配 [2, 3]
        assert dominates([1, 2], [2, 3])

    def test_dominates_false_equal(self):
        """测试相等时不支配"""
        assert not dominates([1, 2], [1, 2])

    def test_dominates_false_worse(self):
        """测试更差时不支配"""
        assert not dominates([2, 3], [1, 2])

    def test_dominates_partial(self):
        """测试部分更优时不支配"""
        # [1, 3] 在第一个目标更优，第二个更差
        assert not dominates([1, 3], [2, 2])


class TestFastNonDominatedSort:
    """快速非支配排序测试"""

    def test_single_front(self):
        """测试单个前沿"""
        population = [
            (Individual([1]), [1.0, 2.0]),
            (Individual([2]), [3.0, 1.0]),
            (Individual([3]), [2.0, 3.0]),
        ]

        # [1, 2] 和 [3, 1] 互不支配
        fronts = fast_non_dominated_sort(population)
        assert len(fronts) >= 1

    def test_two_fronts(self):
        """测试两个前沿"""
        population = [
            (Individual([1]), [1.0, 1.0]),  # 最优
            (Individual([2]), [2.0, 2.0]),  # 被 [1] 支配
            (Individual([3]), [3.0, 3.0]),  # 被 [1] 和 [2] 支配
        ]

        fronts = fast_non_dominated_sort(population)
        assert len(fronts) == 3
        assert 0 in fronts[0]  # [1.0, 1.0] 在第一个前沿

    def test_complex_case(self):
        """测试复杂情况"""
        population = [
            (Individual([1]), [1.0, 3.0]),
            (Individual([2]), [2.0, 2.0]),
            (Individual([3]), [3.0, 1.0]),
            (Individual([4]), [2.0, 3.0]),  # 被 [2] 支配
            (Individual([5]), [3.0, 2.0]),  # 被 [3] 支配
        ]

        fronts = fast_non_dominated_sort(population)
        assert len(fronts) >= 2

        # 第一个前沿应该包含互不支配的解
        first_front_indices = fronts[0]
        assert len(first_front_indices) == 3  # [1,3], [2,2], [3,1]


class TestCrowdingDistanceAssignment:
    """拥挤度距离测试"""

    def test_two_individuals(self):
        """测试两个个体"""
        population = [
            (Individual([1]), [1.0, 2.0]),
            (Individual([2]), [2.0, 1.0]),
        ]
        front = [0, 1]

        distances = crowding_distance_assignment(population, front)

        # 两个个体的距离应该都是无穷大
        assert distances[0] == float('inf')
        assert distances[1] == float('inf')

    def test_three_individuals(self):
        """测试三个个体"""
        population = [
            (Individual([1]), [1.0, 3.0]),
            (Individual([2]), [2.0, 2.0]),
            (Individual([3]), [3.0, 1.0]),
        ]
        front = [0, 1, 2]

        distances = crowding_distance_assignment(population, front)

        # 边界个体距离为无穷大
        assert distances[0] == float('inf')
        assert distances[2] == float('inf')

        # 中间个体距离有限
        assert distances[1] < float('inf')


class SimpleBiObjectiveProblem(MultiObjectiveProblem):
    """简单的双目标优化问题：最小化 f1 和 f2"""

    def __init__(self, dimensions: int = 2):
        self.dimensions = dimensions

    def create_individual(self):
        return [random.uniform(-5, 5) for _ in range(self.dimensions)]

    def objectives(self, chromosome):
        # f1 = sum(x_i^2), f2 = sum((x_i - 1)^2)
        f1 = sum(x ** 2 for x in chromosome)
        f2 = sum((x - 1) ** 2 for x in chromosome)
        return [f1, f2]

    def display(self, chromosome):
        objs = self.objectives(chromosome)
        print(f"Solution: {chromosome}, Objectives: {objs}")


class TestNSGA2Engine:
    """NSGA-II 引擎测试"""

    def test_initialization(self):
        """测试初始化"""
        problem = SimpleBiObjectiveProblem(dimensions=2)
        engine = NSGA2Engine(problem, population_size=20)

        assert len(engine.population) == 20
        assert engine.generation == 0

    def test_evolve_one_generation(self):
        """测试进化一代"""
        problem = SimpleBiObjectiveProblem(dimensions=2)
        engine = NSGA2Engine(problem, population_size=20)

        engine.evolve_one_generation()

        assert engine.generation == 1
        assert len(engine.population) == 20

    def test_run(self):
        """测试运行"""
        problem = SimpleBiObjectiveProblem(dimensions=2)
        engine = NSGA2Engine(problem, population_size=30)

        pareto_front = engine.run(generations=10, verbose=False)

        # 应该返回 Pareto 前沿
        assert len(pareto_front) > 0
        assert len(pareto_front) <= 30

    def test_pareto_front_properties(self):
        """测试 Pareto 前沿性质"""
        problem = SimpleBiObjectiveProblem(dimensions=2)
        engine = NSGA2Engine(problem, population_size=50)

        pareto_front = engine.run(generations=20, verbose=False)

        # 评估 Pareto 前沿
        objectives = [problem.objectives(ind.chromosome) for ind in pareto_front]

        # Pareto 前沿中的解应该互不支配
        for i in range(len(objectives)):
            for j in range(i + 1, len(objectives)):
                assert not dominates(objectives[i], objectives[j])
                assert not dominates(objectives[j], objectives[i])

    def test_get_pareto_front(self):
        """测试获取 Pareto 前沿"""
        problem = SimpleBiObjectiveProblem(dimensions=2)
        engine = NSGA2Engine(problem, population_size=30)

        engine.run(generations=10, verbose=False)
        pareto_front = engine.get_pareto_front()

        assert len(pareto_front) > 0

        # 每个元素应该是 (Individual, List[float]) 元组
        for ind, objs in pareto_front:
            assert isinstance(ind, Individual)
            assert len(objs) == 2

    def test_convergence(self):
        """测试收敛性"""
        problem = SimpleBiObjectiveProblem(dimensions=2)
        engine = NSGA2Engine(problem, population_size=50)

        pareto_front = engine.run(generations=30, verbose=False)

        # 评估 Pareto 前沿的质量
        objectives = [problem.objectives(ind.chromosome) for ind in pareto_front]

        # 至少应该有一些解接近理想点 [0, 0]
        min_f1 = min(obj[0] for obj in objectives)
        min_f2 = min(obj[1] for obj in objectives)

        # 收敛后，最小目标值应该较小
        assert min_f1 < 5.0
        assert min_f2 < 5.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
