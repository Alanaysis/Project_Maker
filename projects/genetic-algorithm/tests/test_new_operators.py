"""
新增算子测试：均匀交叉、算术交叉、高斯变异、自适应变异
"""

import pytest
import sys
import os
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.individual import Individual
from src.operators.crossover import UniformCrossover, ArithmeticCrossover
from src.operators.mutation import GaussianMutation, AdaptiveMutation


class TestUniformCrossover:
    """均匀交叉测试"""

    def test_basic_crossover(self):
        """测试基本交叉功能"""
        parent1 = Individual([1, 2, 3, 4, 5])
        parent2 = Individual([6, 7, 8, 9, 10])

        crossover = UniformCrossover(crossover_rate=1.0, swap_probability=0.5)
        child1, child2 = crossover.crossover(parent1, parent2)

        # 子代应该包含两个父代的基因
        all_values = sorted(child1.chromosome + child2.chromosome)
        assert all_values == list(range(1, 11))

    def test_crossover_rate(self):
        """测试交叉率"""
        parent1 = Individual([1, 2, 3])
        parent2 = Individual([4, 5, 6])

        # 交叉率为 0 时，子代应该是父代的副本
        crossover = UniformCrossover(crossover_rate=0.0)
        child1, child2 = crossover.crossover(parent1, parent2)

        assert child1.chromosome == [1, 2, 3]
        assert child2.chromosome == [4, 5, 6]

    def test_swap_probability_zero(self):
        """测试交换概率为 0 的情况"""
        parent1 = Individual([1, 2, 3, 4, 5])
        parent2 = Individual([6, 7, 8, 9, 10])

        crossover = UniformCrossover(crossover_rate=1.0, swap_probability=0.0)
        child1, child2 = crossover.crossover(parent1, parent2)

        # 不应该交换任何基因
        assert child1.chromosome == [1, 2, 3, 4, 5]
        assert child2.chromosome == [6, 7, 8, 9, 10]

    def test_swap_probability_one(self):
        """测试交换概率为 1 的情况"""
        parent1 = Individual([1, 2, 3, 4, 5])
        parent2 = Individual([6, 7, 8, 9, 10])

        crossover = UniformCrossover(crossover_rate=1.0, swap_probability=1.0)
        child1, child2 = crossover.crossover(parent1, parent2)

        # 所有基因都应该交换
        assert child1.chromosome == [6, 7, 8, 9, 10]
        assert child2.chromosome == [1, 2, 3, 4, 5]

    def test_preserves_all_genes(self):
        """测试保留所有基因"""
        parent1 = Individual([10, 20, 30, 40, 50])
        parent2 = Individual([60, 70, 80, 90, 100])

        crossover = UniformCrossover(crossover_rate=1.0)
        child1, child2 = crossover.crossover(parent1, parent2)

        # 两个子代的基因应该是两个父代基因的并集
        all_parent = sorted(parent1.chromosome + parent2.chromosome)
        all_child = sorted(child1.chromosome + child2.chromosome)
        assert all_parent == all_child


class TestArithmeticCrossover:
    """算术交叉测试"""

    def test_basic_crossover(self):
        """测试基本交叉功能"""
        parent1 = Individual([1.0, 2.0, 3.0])
        parent2 = Individual([4.0, 5.0, 6.0])

        crossover = ArithmeticCrossover(crossover_rate=1.0, alpha=0.5)
        child1, child2 = crossover.crossover(parent1, parent2)

        # alpha=0.5 时，两个子代的平均值应该等于父代的平均值
        for i in range(3):
            parent_avg = (parent1.chromosome[i] + parent2.chromosome[i]) / 2
            child_avg = (child1.chromosome[i] + child2.chromosome[i]) / 2
            assert abs(parent_avg - child_avg) < 1e-6

    def test_crossover_rate(self):
        """测试交叉率"""
        parent1 = Individual([1.0, 2.0, 3.0])
        parent2 = Individual([4.0, 5.0, 6.0])

        crossover = ArithmeticCrossover(crossover_rate=0.0)
        child1, child2 = crossover.crossover(parent1, parent2)

        assert child1.chromosome == [1.0, 2.0, 3.0]
        assert child2.chromosome == [4.0, 5.0, 6.0]

    def test_alpha_zero(self):
        """测试 alpha=0 的情况"""
        parent1 = Individual([1.0, 2.0, 3.0])
        parent2 = Individual([4.0, 5.0, 6.0])

        crossover = ArithmeticCrossover(crossover_rate=1.0, alpha=0.0)
        child1, child2 = crossover.crossover(parent1, parent2)

        # alpha=0 时，child1 应该等于 parent2
        for i in range(3):
            assert abs(child1.chromosome[i] - parent2.chromosome[i]) < 1e-6
            assert abs(child2.chromosome[i] - parent1.chromosome[i]) < 1e-6

    def test_preserves_average(self):
        """测试保持平均值"""
        parent1 = Individual([1.0, 2.0, 3.0])
        parent2 = Individual([4.0, 5.0, 6.0])

        crossover = ArithmeticCrossover(crossover_rate=1.0, alpha=0.3)
        child1, child2 = crossover.crossover(parent1, parent2)

        # 两个子代的平均值应该等于两个父代的平均值
        for i in range(3):
            parent_avg = (parent1.chromosome[i] + parent2.chromosome[i]) / 2
            child_avg = (child1.chromosome[i] + child2.chromosome[i]) / 2
            assert abs(parent_avg - child_avg) < 1e-6


class TestGaussianMutation:
    """高斯变异测试"""

    def test_basic_mutation(self):
        """测试基本变异功能"""
        ind = Individual([1.0, 2.0, 3.0, 4.0, 5.0])

        # 变异率为 1.0 时，所有基因都应该变异
        mutator = GaussianMutation(mutation_rate=1.0, sigma=0.1)
        mutated = mutator.mutate(ind)

        # 变异后应该不完全相同（概率极高）
        assert mutated.chromosome != [1.0, 2.0, 3.0, 4.0, 5.0]
        # 原个体应该不变
        assert ind.chromosome == [1.0, 2.0, 3.0, 4.0, 5.0]

    def test_mutation_rate_zero(self):
        """测试变异率为 0 的情况"""
        ind = Individual([1.0, 2.0, 3.0])

        mutator = GaussianMutation(mutation_rate=0.0, sigma=1.0)
        mutated = mutator.mutate(ind)

        assert mutated.chromosome == [1.0, 2.0, 3.0]

    def test_boundary_constraints(self):
        """测试边界约束"""
        ind = Individual([0.0, 0.0, 0.0])

        mutator = GaussianMutation(
            mutation_rate=1.0,
            sigma=10.0,
            min_value=-1.0,
            max_value=1.0
        )
        mutated = mutator.mutate(ind)

        # 所有基因应该在边界内
        for val in mutated.chromosome:
            assert -1.0 <= val <= 1.0

    def test_mutation_effect(self):
        """测试变异效果"""
        ind = Individual([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

        mutator = GaussianMutation(mutation_rate=1.0, sigma=1.0)
        mutated = mutator.mutate(ind)

        # 变异后的值应该在合理范围内（大约 -3 到 3）
        for val in mutated.chromosome:
            assert -5.0 <= val <= 5.0


class TestAdaptiveMutation:
    """自适应变异测试"""

    def test_basic_mutation(self):
        """测试基本变异功能"""
        ind = Individual([1.0, 2.0, 3.0])

        mutator = AdaptiveMutation(initial_mutation_rate=0.5, sigma=0.1)
        mutated = mutator.mutate(ind)

        # 应该产生变异
        assert isinstance(mutated.chromosome, list)

    def test_adaptation_on_improvement(self):
        """测试适应度改善时变异率降低"""
        mutator = AdaptiveMutation(
            initial_mutation_rate=0.5,
            min_mutation_rate=0.01,
            decrease_factor=0.5
        )

        initial_rate = mutator.current_mutation_rate

        # 模拟适应度改善
        mutator.update(10.0)
        mutator.update(20.0)
        mutator.update(30.0)

        # 变异率应该降低
        assert mutator.current_mutation_rate < initial_rate

    def test_adaptation_on_stagnation(self):
        """测试适应度停滞时变异率增加"""
        mutator = AdaptiveMutation(
            initial_mutation_rate=0.1,
            max_mutation_rate=0.5,
            stagnation_threshold=3,
            increase_factor=2.0
        )

        initial_rate = mutator.current_mutation_rate

        # 模拟适应度停滞
        mutator.update(10.0)
        mutator.update(10.0)
        mutator.update(10.0)
        mutator.update(10.0)

        # 变异率应该增加
        assert mutator.current_mutation_rate > initial_rate

    def test_mutation_rate_bounds(self):
        """测试变异率边界"""
        mutator = AdaptiveMutation(
            initial_mutation_rate=0.1,
            min_mutation_rate=0.01,
            max_mutation_rate=0.5,
            decrease_factor=0.1,
            increase_factor=10.0,
            stagnation_threshold=1
        )

        # 大量改善，变异率应该不低于最小值
        for i in range(100):
            mutator.update(float(i * 10))

        assert mutator.current_mutation_rate >= 0.01

        # 大量停滞，变异率应该不高于最大值
        for _ in range(100):
            mutator.update(0.0)

        assert mutator.current_mutation_rate <= 0.5

    def test_reset(self):
        """测试重置功能"""
        mutator = AdaptiveMutation(
            initial_mutation_rate=0.5,
            stagnation_threshold=2,
            increase_factor=2.0
        )

        # 修改状态
        mutator.update(10.0)
        mutator.update(10.0)
        mutator.update(10.0)

        # 重置
        mutator.reset()

        assert mutator.current_mutation_rate == 0.01  # min_mutation_rate


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
