"""
背包问题测试
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.problems.knapsack import KnapsackProblem, MultiKnapsackProblem


class TestKnapsackProblem:
    """0/1 背包问题测试"""

    def test_create_individual(self):
        """测试个体创建"""
        items = [(10, 60), (20, 100), (30, 120)]
        problem = KnapsackProblem(items, capacity=50)

        ind = problem.create_individual()

        assert len(ind) == 3
        for val in ind:
            assert val in [0, 1]

    def test_fitness_valid_solution(self):
        """测试有效解的适应度"""
        items = [(10, 60), (20, 100), (30, 120)]
        problem = KnapsackProblem(items, capacity=50)

        # 选择物品 0 和 1，总重量 30，总价值 160
        chromosome = [1, 1, 0]
        fitness = problem.fitness(chromosome)

        assert fitness == 160.0

    def test_fitness_overweight_solution(self):
        """测试超重解的适应度"""
        items = [(10, 60), (20, 100), (30, 120)]
        problem = KnapsackProblem(items, capacity=25)

        # 选择所有物品，总重量 60，超过容量 25
        chromosome = [1, 1, 1]
        fitness = problem.fitness(chromosome)

        # 应该有惩罚，适应度低于总价值
        assert fitness < 280.0

    def test_fitness_empty_solution(self):
        """测试空解的适应度"""
        items = [(10, 60), (20, 100), (30, 120)]
        problem = KnapsackProblem(items, capacity=50)

        chromosome = [0, 0, 0]
        fitness = problem.fitness(chromosome)

        assert fitness == 0.0

    def test_is_valid(self):
        """测试有效性检查"""
        items = [(10, 60), (20, 100), (30, 120)]
        problem = KnapsackProblem(items, capacity=50)

        # 有效解
        assert problem.is_valid([1, 1, 0])  # 重量 30
        assert problem.is_valid([0, 0, 1])  # 重量 30

        # 无效解（超重）
        assert not problem.is_valid([1, 1, 1])  # 重量 60

    def test_calculate_total_weight(self):
        """测试总重量计算"""
        items = [(10, 60), (20, 100), (30, 120)]
        problem = KnapsackProblem(items, capacity=50)

        assert problem.calculate_total_weight([1, 1, 0]) == 30
        assert problem.calculate_total_weight([0, 0, 1]) == 30
        assert problem.calculate_total_weight([1, 1, 1]) == 60

    def test_calculate_total_value(self):
        """测试总价值计算"""
        items = [(10, 60), (20, 100), (30, 120)]
        problem = KnapsackProblem(items, capacity=50)

        assert problem.calculate_total_value([1, 1, 0]) == 160
        assert problem.calculate_total_value([0, 0, 1]) == 120
        assert problem.calculate_total_value([1, 1, 1]) == 280

    def test_generate_random_problem(self):
        """测试随机问题生成"""
        problem = KnapsackProblem.generate_random_problem(n_items=10, max_weight=50, max_value=100)

        assert problem.n_items == 10
        assert len(problem.items) == 10
        assert problem.capacity > 0

        for weight, value in problem.items:
            assert 1 <= weight <= 50
            assert 1 <= value <= 100

    def test_display(self, capsys):
        """测试显示功能"""
        items = [(10, 60), (20, 100), (30, 120)]
        problem = KnapsackProblem(items, capacity=50)

        problem.display([1, 1, 0])

        captured = capsys.readouterr()
        assert "Selected items" in captured.out
        assert "Total weight" in captured.out
        assert "Total value" in captured.out

    def test_optimal_solution(self):
        """测试最优解"""
        # 经典背包问题示例
        items = [(10, 60), (20, 100), (30, 120)]
        problem = KnapsackProblem(items, capacity=50)

        # 最优解：选择物品 1 和 2，总重量 50，总价值 220
        optimal = [0, 1, 1]
        assert problem.is_valid(optimal)
        assert problem.calculate_total_value(optimal) == 220.0


class TestMultiKnapsackProblem:
    """多重背包问题测试"""

    def test_create_individual(self):
        """测试个体创建"""
        items = [(10, 60), (20, 100), (30, 120)]
        capacities = [25, 35]
        problem = MultiKnapsackProblem(items, capacities)

        ind = problem.create_individual()

        assert len(ind) == 3
        for val in ind:
            assert 0 <= val <= 2  # 0 表示不选择，1 或 2 表示分配到背包

    def test_fitness_valid_solution(self):
        """测试有效解的适应度"""
        items = [(10, 60), (20, 100), (30, 120)]
        capacities = [30, 40]
        problem = MultiKnapsackProblem(items, capacities)

        # 物品 0 分配到背包 1，物品 1 分配到背包 2
        chromosome = [1, 2, 0]
        fitness = problem.fitness(chromosome)

        assert fitness == 160.0

    def test_fitness_overweight_solution(self):
        """测试超重解的适应度"""
        items = [(10, 60), (20, 100), (30, 120)]
        capacities = [15, 15]
        problem = MultiKnapsackProblem(items, capacities)

        # 物品 0 和 1 都分配到背包 1，超重
        chromosome = [1, 1, 0]
        fitness = problem.fitness(chromosome)

        # 应该有惩罚
        assert fitness < 160.0

    def test_is_valid(self):
        """测试有效性检查"""
        items = [(10, 60), (20, 100), (30, 120)]
        capacities = [30, 40]
        problem = MultiKnapsackProblem(items, capacities)

        # 有效解
        assert problem.is_valid([1, 2, 0])  # 背包 1: 10, 背包 2: 20

        # 无效解（超重）
        assert not problem.is_valid([1, 1, 1])  # 背包 1: 60

    def test_display(self, capsys):
        """测试显示功能"""
        items = [(10, 60), (20, 100), (30, 120)]
        capacities = [30, 40]
        problem = MultiKnapsackProblem(items, capacities)

        problem.display([1, 2, 0])

        captured = capsys.readouterr()
        assert "Total value" in captured.out
        assert "Knapsack" in captured.out

    def test_generate_random_problem(self):
        """测试随机问题生成"""
        problem = MultiKnapsackProblem.generate_random_problem(
            n_items=10, n_knapsacks=3, max_weight=30, max_value=100
        )

        assert problem.n_items == 10
        assert problem.n_knapsacks == 3
        assert len(problem.items) == 10
        assert len(problem.capacities) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
