"""
函数优化问题测试
"""

import pytest
import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.problems.function_opt import (
    SphereProblem,
    RastriginProblem,
    RosenbrockProblem,
    AckleyProblem,
    GriewankProblem,
)


class TestSphereProblem:
    """Sphere 函数测试"""

    def test_optimal_solution(self):
        """测试最优解"""
        problem = SphereProblem(dimensions=3)
        optimal = [0.0, 0.0, 0.0]

        assert abs(problem.objective(optimal)) < 1e-10
        assert abs(problem.fitness(optimal) - 1.0) < 1e-10

    def test_create_individual(self):
        """测试个体创建"""
        problem = SphereProblem(dimensions=5, range_min=-10, range_max=10)
        ind = problem.create_individual()

        assert len(ind) == 5
        for val in ind:
            assert -10 <= val <= 10

    def test_fitness_calculation(self):
        """测试适应度计算"""
        problem = SphereProblem(dimensions=2)

        # 在原点处适应度最高
        assert problem.fitness([0.0, 0.0]) > problem.fitness([1.0, 1.0])
        assert problem.fitness([1.0, 1.0]) > problem.fitness([10.0, 10.0])

    def test_display(self, capsys):
        """测试显示功能"""
        problem = SphereProblem(dimensions=2)
        problem.display([1.0, 2.0])

        captured = capsys.readouterr()
        assert "Solution" in captured.out
        assert "Objective value" in captured.out


class TestRastriginProblem:
    """Rastrigin 函数测试"""

    def test_optimal_solution(self):
        """测试最优解"""
        problem = RastriginProblem(dimensions=3)
        optimal = [0.0, 0.0, 0.0]

        assert abs(problem.objective(optimal)) < 1e-10

    def test_create_individual(self):
        """测试个体创建"""
        problem = RastriginProblem(dimensions=4)
        ind = problem.create_individual()

        assert len(ind) == 4
        for val in ind:
            assert -5.12 <= val <= 5.12

    def test_local_optima(self):
        """测试存在局部最优"""
        problem = RastriginProblem(dimensions=2)

        # 全局最优
        global_opt = problem.objective([0.0, 0.0])

        # 局部最优（应该大于全局最优）
        local_opt = problem.objective([4.0, 4.0])
        assert local_opt > global_opt

    def test_fitness_ordering(self):
        """测试适应度排序"""
        problem = RastriginProblem(dimensions=2)

        # 越接近原点，适应度越高
        fitnesses = [
            problem.fitness([0.0, 0.0]),
            problem.fitness([1.0, 1.0]),
            problem.fitness([3.0, 3.0]),
        ]

        assert fitnesses[0] > fitnesses[1] > fitnesses[2]


class TestRosenbrockProblem:
    """Rosenbrock 函数测试"""

    def test_optimal_solution(self):
        """测试最优解"""
        problem = RosenbrockProblem(dimensions=3)
        optimal = [1.0, 1.0, 1.0]

        assert abs(problem.objective(optimal)) < 1e-10

    def test_create_individual(self):
        """测试个体创建"""
        problem = RosenbrockProblem(dimensions=3)
        ind = problem.create_individual()

        assert len(ind) == 3
        for val in ind:
            assert -5 <= val <= 10

    def test_banana_shape(self):
        """测试香蕉形状的山谷"""
        problem = RosenbrockProblem(dimensions=2)

        # 沿着山谷的点应该有较低的目标值
        valley_point = problem.objective([0.5, 0.25])
        outside_point = problem.objective([0.0, 0.0])

        assert valley_point < outside_point


class TestAckleyProblem:
    """Ackley 函数测试"""

    def test_optimal_solution(self):
        """测试最优解"""
        problem = AckleyProblem(dimensions=3)
        optimal = [0.0, 0.0, 0.0]

        assert abs(problem.objective(optimal)) < 1e-10

    def test_create_individual(self):
        """测试个体创建"""
        problem = AckleyProblem(dimensions=3)
        ind = problem.create_individual()

        assert len(ind) == 3
        for val in ind:
            assert -32.768 <= val <= 32.768

    def test_fitness_ordering(self):
        """测试适应度排序"""
        problem = AckleyProblem(dimensions=2)

        # 越接近原点，适应度越高
        assert problem.fitness([0.0, 0.0]) > problem.fitness([1.0, 1.0])


class TestGriewankProblem:
    """Griewank 函数测试"""

    def test_optimal_solution(self):
        """测试最优解"""
        problem = GriewankProblem(dimensions=3)
        optimal = [0.0, 0.0, 0.0]

        assert abs(problem.objective(optimal)) < 1e-10

    def test_create_individual(self):
        """测试个体创建"""
        problem = GriewankProblem(dimensions=3)
        ind = problem.create_individual()

        assert len(ind) == 3
        for val in ind:
            assert -600 <= val <= 600

    def test_fitness_ordering(self):
        """测试适应度排序"""
        problem = GriewankProblem(dimensions=2)

        # 越接近原点，适应度越高
        assert problem.fitness([0.0, 0.0]) > problem.fitness([10.0, 10.0])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
