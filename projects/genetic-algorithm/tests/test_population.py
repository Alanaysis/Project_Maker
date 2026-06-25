"""
种群类测试
"""

import pytest
import sys
import os
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.individual import Individual
from src.core.population import Population


class TestPopulation:
    """种群类测试"""

    def test_initialization(self):
        """测试种群初始化"""
        pop = Population()
        pop.initialize(10, lambda: [random.randint(0, 1) for _ in range(5)])

        assert pop.size == 10
        assert len(pop.individuals) == 10
        for ind in pop.individuals:
            assert len(ind.chromosome) == 5

    def test_evaluate(self):
        """测试种群评估"""
        pop = Population()
        pop.initialize(5, lambda: [1, 2, 3])
        pop.evaluate(lambda x: sum(x))

        for ind in pop.individuals:
            assert ind.fitness == 6.0

    def test_get_best(self):
        """测试获取最优个体"""
        pop = Population()
        pop.individuals = [
            Individual([1, 2, 3]),
            Individual([4, 5, 6]),
            Individual([7, 8, 9])
        ]
        pop.individuals[0].fitness = 10
        pop.individuals[1].fitness = 20
        pop.individuals[2].fitness = 15

        best = pop.get_best()
        assert best.fitness == 20

    def test_get_worst(self):
        """测试获取最差个体"""
        pop = Population()
        pop.individuals = [
            Individual([1, 2, 3]),
            Individual([4, 5, 6]),
            Individual([7, 8, 9])
        ]
        pop.individuals[0].fitness = 10
        pop.individuals[1].fitness = 20
        pop.individuals[2].fitness = 15

        worst = pop.get_worst()
        assert worst.fitness == 10

    def test_get_statistics(self):
        """测试统计信息"""
        pop = Population()
        pop.individuals = [
            Individual([1]),
            Individual([2]),
            Individual([3])
        ]
        pop.individuals[0].fitness = 10
        pop.individuals[1].fitness = 20
        pop.individuals[2].fitness = 30

        stats = pop.get_statistics()
        assert stats['best'] == 30
        assert stats['worst'] == 10
        assert stats['average'] == 20

    def test_replace(self):
        """测试种群替换"""
        pop = Population()
        pop.initialize(3, lambda: [1, 2, 3])

        new_individuals = [
            Individual([4, 5, 6]),
            Individual([7, 8, 9])
        ]
        pop.replace(new_individuals)

        assert len(pop) == 2
        assert pop[0].chromosome == [4, 5, 6]
        assert pop[1].chromosome == [7, 8, 9]

    def test_len(self):
        """测试长度"""
        pop = Population()
        pop.initialize(5, lambda: [1])
        assert len(pop) == 5

    def test_getitem(self):
        """测试索引访问"""
        pop = Population()
        pop.initialize(3, lambda: [1, 2, 3])
        assert pop[0].chromosome == [1, 2, 3]

    def test_iter(self):
        """测试迭代"""
        pop = Population()
        pop.initialize(3, lambda: [1, 2, 3])
        count = 0
        for ind in pop:
            count += 1
        assert count == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
