"""
集成测试
"""

import pytest
import sys
import os
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.ga_engine import GAEngine
from src.operators.selection import TournamentSelection
from src.operators.crossover import OrderCrossover, SinglePointCrossover
from src.operators.mutation import SwapMutation, BitFlipMutation
from src.problems.tsp import TSPProblem
from src.problems.base import Problem
from src.core.individual import Individual


class SimpleProblem(Problem):
    """简单的测试问题：最大化 sum(x^2)"""

    def __init__(self, size: int = 3):
        self.size = size

    def create_individual(self):
        return [random.uniform(-10, 10) for _ in range(self.size)]

    def fitness(self, chromosome):
        # 最小化 sum(x^2)，适应度为倒数
        value = sum(x ** 2 for x in chromosome)
        return 1.0 / (1.0 + value)

    def display(self, chromosome):
        print(f"Solution: {chromosome}")


class TestGAIntegration:
    """遗传算法集成测试"""

    def test_basic_optimization(self):
        """测试基础优化"""
        problem = SimpleProblem(size=3)
        engine = GAEngine(problem, population_size=50)

        best = engine.run(generations=50, verbose=False)

        # 应该找到接近最优解的解
        assert best.fitness > 0.1  # 适应度应该足够高

    def test_tsp_convergence(self):
        """测试 TSP 收敛"""
        # 小规模 TSP 问题
        cities = [(0, 0), (1, 0), (1, 1), (0, 1), (0.5, 0.5)]
        problem = TSPProblem(cities)

        engine = GAEngine(
            problem,
            population_size=50,
            selection=TournamentSelection(tournament_size=3),
            crossover=OrderCrossover(crossover_rate=0.8),
            mutation=SwapMutation(mutation_rate=0.2)
        )

        best = engine.run(generations=100, verbose=False)

        # 应该找到合理长度的路径
        distance = problem.calculate_distance(best.chromosome)
        assert distance < 5.0  # 路径长度应该小于某个阈值

    def test_convergence_history(self):
        """测试收敛历史"""
        cities = [(0, 0), (1, 0), (1, 1), (0, 1)]
        problem = TSPProblem(cities)

        engine = GAEngine(problem, population_size=30)
        engine.run(generations=50, verbose=False)

        # 应该有历史记录
        assert len(engine.history['best_fitness']) == 50
        assert len(engine.history['average_fitness']) == 50

        # 最优适应度应该有提升
        assert engine.history['best_fitness'][-1] >= engine.history['best_fitness'][0]

    def test_custom_operators(self):
        """测试自定义算子"""
        problem = SimpleProblem(size=2)

        engine = GAEngine(
            problem,
            population_size=30,
            selection=TournamentSelection(tournament_size=2),
            crossover=SinglePointCrossover(crossover_rate=0.9),
            mutation=BitFlipMutation(mutation_rate=0.1)
        )

        best = engine.run(generations=30, verbose=False)
        assert best.fitness > 0.0

    def test_get_best_solution(self):
        """测试获取最优解"""
        problem = SimpleProblem(size=2)
        engine = GAEngine(problem, population_size=20)

        engine.run(generations=20, verbose=False)
        best = engine.get_best_solution()

        assert best is not None
        assert best.fitness > 0.0

    def test_get_convergence_data(self):
        """测试获取收敛数据"""
        problem = SimpleProblem(size=2)
        engine = GAEngine(problem, population_size=20)

        engine.run(generations=20, verbose=False)
        data = engine.get_convergence_data()

        assert 'best_fitness' in data
        assert 'average_fitness' in data
        assert len(data['best_fitness']) == 20


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
