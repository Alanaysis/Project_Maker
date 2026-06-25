"""
TSP 问题测试
"""

import pytest
import sys
import os
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.problems.tsp import TSPProblem


class TestTSPProblem:
    """TSP 问题测试"""

    def test_distance_matrix(self):
        """测试距离矩阵计算"""
        cities = [(0, 0), (1, 0), (0, 1)]
        problem = TSPProblem(cities)

        # 验证距离计算
        assert abs(problem.distance_matrix[0][1] - 1.0) < 1e-6
        assert abs(problem.distance_matrix[0][2] - 1.0) < 1e-6
        assert abs(problem.distance_matrix[1][2] - np.sqrt(2)) < 1e-6

    def test_fitness_calculation(self):
        """测试适应度计算"""
        cities = [(0, 0), (1, 0), (1, 1), (0, 1)]
        problem = TSPProblem(cities)

        # 正方形路径
        route = [0, 1, 2, 3]
        distance = problem.calculate_distance(route)
        fitness = problem.fitness(route)

        assert abs(distance - 4.0) < 1e-6
        assert abs(fitness - 0.25) < 1e-6

    def test_create_individual(self):
        """测试个体创建"""
        cities = [(0, 0), (1, 0), (2, 0)]
        problem = TSPProblem(cities)

        individual = problem.create_individual()

        assert len(individual) == 3
        assert sorted(individual) == [0, 1, 2]  # 应该是排列

    def test_optimal_solution(self):
        """测试最优解"""
        # 简单的正方形，最优路径应该是 4
        cities = [(0, 0), (1, 0), (1, 1), (0, 1)]
        problem = TSPProblem(cities)

        optimal_route = [0, 1, 2, 3]
        distance = problem.calculate_distance(optimal_route)

        assert abs(distance - 4.0) < 1e-6

    def test_different_routes(self):
        """测试不同路径"""
        cities = [(0, 0), (1, 0), (1, 1), (0, 1)]
        problem = TSPProblem(cities)

        # 不同路径应该有不同的距离
        route1 = [0, 1, 2, 3]
        route2 = [0, 2, 1, 3]

        dist1 = problem.calculate_distance(route1)
        dist2 = problem.calculate_distance(route2)

        assert dist1 != dist2

    def test_generate_random_cities(self):
        """测试随机城市生成"""
        cities = TSPProblem.generate_random_cities(10)

        assert len(cities) == 10
        for city in cities:
            assert len(city) == 2
            assert 0 <= city[0] <= 100
            assert 0 <= city[1] <= 100

    def test_generate_circle_cities(self):
        """测试圆形城市生成"""
        cities = TSPProblem.generate_circle_cities(8)

        assert len(cities) == 8
        # 所有城市应该在半径为 50 的圆上
        for city in cities:
            distance = np.sqrt(city[0] ** 2 + city[1] ** 2)
            assert abs(distance - 50.0) < 1e-6

    def test_display(self, capsys):
        """测试显示功能"""
        cities = [(0, 0), (1, 0), (1, 1), (0, 1)]
        problem = TSPProblem(cities)

        route = [0, 1, 2, 3]
        problem.display(route)

        captured = capsys.readouterr()
        assert "Route" in captured.out
        assert "Total distance" in captured.out


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
