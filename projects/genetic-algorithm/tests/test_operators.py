"""
遗传算子测试
"""

import pytest
import sys
import os
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.individual import Individual
from src.core.population import Population
from src.operators.selection import (
    RouletteWheelSelection,
    TournamentSelection,
    ElitismSelection,
)
from src.operators.crossover import (
    SinglePointCrossover,
    TwoPointCrossover,
    OrderCrossover,
)
from src.operators.mutation import (
    BitFlipMutation,
    SwapMutation,
    InversionMutation,
)


class TestSelectionOperators:
    """选择算子测试"""

    def _create_test_population(self):
        """创建测试种群"""
        pop = Population()
        pop.individuals = [
            Individual([1]),
            Individual([2]),
            Individual([3])
        ]
        pop.individuals[0].fitness = 10
        pop.individuals[1].fitness = 20
        pop.individuals[2].fitness = 30
        return pop

    def test_roulette_wheel_selection(self):
        """测试轮盘赌选择"""
        pop = self._create_test_population()
        selector = RouletteWheelSelection()
        selected = selector.select(pop, 3)

        assert len(selected) == 3
        # 适应度高的个体应该被选中更多次
        fitnesses = [ind.fitness for ind in selected]
        assert max(fitnesses) >= 20  # 至少选中一个高适应度个体

    def test_tournament_selection(self):
        """测试锦标赛选择"""
        pop = self._create_test_population()
        selector = TournamentSelection(tournament_size=2)
        selected = selector.select(pop, 2)

        assert len(selected) == 2
        # 锦标赛选择应该倾向于选择高适应度个体
        fitnesses = [ind.fitness for ind in selected]
        assert all(f >= 10 for f in fitnesses)

    def test_elitism_selection(self):
        """测试精英保留选择"""
        pop = Population()
        pop.individuals = [
            Individual([1]),
            Individual([2]),
            Individual([3]),
            Individual([4])
        ]
        pop.individuals[0].fitness = 10
        pop.individuals[1].fitness = 20
        pop.individuals[2].fitness = 30
        pop.individuals[3].fitness = 40

        selector = ElitismSelection()
        selected = selector.select(pop, 2)

        assert len(selected) == 2
        fitnesses = sorted([ind.fitness for ind in selected], reverse=True)
        assert fitnesses == [40, 30]  # 保留最优的两个


class TestCrossoverOperators:
    """交叉算子测试"""

    def test_single_point_crossover(self):
        """测试单点交叉"""
        parent1 = Individual([1, 2, 3, 4, 5])
        parent2 = Individual([6, 7, 8, 9, 10])

        crossover = SinglePointCrossover(crossover_rate=1.0)
        child1, child2 = crossover.crossover(parent1, parent2)

        # 子代应该是父代的组合
        all_values = sorted(child1.chromosome + child2.chromosome)
        assert all_values == list(range(1, 11))

    def test_crossover_rate(self):
        """测试交叉率"""
        parent1 = Individual([1, 2, 3])
        parent2 = Individual([4, 5, 6])

        # 交叉率为 0 时，子代应该是父代的副本
        crossover = SinglePointCrossover(crossover_rate=0.0)
        child1, child2 = crossover.crossover(parent1, parent2)

        assert child1.chromosome == [1, 2, 3]
        assert child2.chromosome == [4, 5, 6]

    def test_two_point_crossover(self):
        """测试两点交叉"""
        parent1 = Individual([1, 2, 3, 4, 5])
        parent2 = Individual([6, 7, 8, 9, 10])

        crossover = TwoPointCrossover(crossover_rate=1.0)
        child1, child2 = crossover.crossover(parent1, parent2)

        # 子代应该是父代的组合
        all_values = sorted(child1.chromosome + child2.chromosome)
        assert all_values == list(range(1, 11))

    def test_order_crossover(self):
        """测试顺序交叉 (OX)"""
        parent1 = Individual([1, 2, 3, 4, 5, 6])
        parent2 = Individual([4, 5, 6, 1, 2, 3])

        crossover = OrderCrossover(crossover_rate=1.0)
        child1, child2 = crossover.crossover(parent1, parent2)

        # 子代应该包含所有城市
        assert sorted(child1.chromosome) == list(range(1, 7))
        assert sorted(child2.chromosome) == list(range(1, 7))


class TestMutationOperators:
    """变异算子测试"""

    def test_bit_flip_mutation(self):
        """测试位翻转变异"""
        ind = Individual([0, 0, 0, 0, 0])

        # 变异率为 1.0 时，所有位都应该翻转
        mutator = BitFlipMutation(mutation_rate=1.0)
        mutated = mutator.mutate(ind)

        assert mutated.chromosome == [1, 1, 1, 1, 1]
        # 原个体应该不变
        assert ind.chromosome == [0, 0, 0, 0, 0]

    def test_swap_mutation(self):
        """测试交换变异"""
        ind = Individual([1, 2, 3, 4, 5])

        # 变异率为 1.0 时，应该发生交换
        mutator = SwapMutation(mutation_rate=1.0)
        mutated = mutator.mutate(ind)

        # 交换后应该仍然是排列
        assert sorted(mutated.chromosome) == [1, 2, 3, 4, 5]

    def test_inversion_mutation(self):
        """测试逆序变异"""
        ind = Individual([1, 2, 3, 4, 5])

        mutator = InversionMutation(mutation_rate=1.0)
        mutated = mutator.mutate(ind)

        # 逆序后应该仍然是排列
        assert sorted(mutated.chromosome) == [1, 2, 3, 4, 5]

    def test_mutation_preserves_validity(self):
        """测试变异保持解的有效性"""
        ind = Individual([0, 1, 2, 3, 4])

        mutator = SwapMutation(mutation_rate=0.5)
        mutated = mutator.mutate(ind)

        # 变异后应该仍然是有效排列
        assert sorted(mutated.chromosome) == [0, 1, 2, 3, 4]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
