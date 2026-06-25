"""
测试函数单元测试
"""

import numpy as np
import pytest
from src.functions import (
    sphere,
    rosenbrock,
    rastrigin,
    ackley,
    griewank,
    get_function,
    BENCHMARK_FUNCTIONS,
)


class TestSphere:
    """Sphere 函数测试"""

    def test_optimal(self):
        """测试最优解"""
        x = np.zeros(5)
        assert sphere(x) == pytest.approx(0.0)

    def test_known_values(self):
        """测试已知值"""
        assert sphere(np.array([1.0, 0.0])) == pytest.approx(1.0)
        assert sphere(np.array([3.0, 4.0])) == pytest.approx(25.0)
        assert sphere(np.array([1.0, 1.0, 1.0])) == pytest.approx(3.0)

    def test_symmetry(self):
        """测试对称性"""
        x = np.array([3.0, -4.0])
        assert sphere(x) == pytest.approx(25.0)


class TestRosenbrock:
    """Rosenbrock 函数测试"""

    def test_optimal(self):
        """测试最优解"""
        x = np.ones(5)
        assert rosenbrock(x) == pytest.approx(0.0)

    def test_known_values(self):
        """测试已知值"""
        # f(0, 0) = 100*(0-0)^2 + (1-0)^2 = 1
        assert rosenbrock(np.array([0.0, 0.0])) == pytest.approx(1.0)

        # f(1, 0) = 100*(0-1)^2 + (1-1)^2 = 100
        assert rosenbrock(np.array([1.0, 0.0])) == pytest.approx(100.0)

    def test_minimum_dimensions(self):
        """测试最小维度要求"""
        with pytest.raises(ValueError):
            rosenbrock(np.array([1.0]))


class TestRastrigin:
    """Rastrigin 函数测试"""

    def test_optimal(self):
        """测试最优解"""
        x = np.zeros(5)
        assert rastrigin(x) == pytest.approx(0.0)

    def test_known_values(self):
        """测试已知值"""
        # f(0) = 0
        assert rastrigin(np.array([0.0])) == pytest.approx(0.0)

        # f(1) = 10 + 1 - 10*cos(2*pi) = 10 + 1 - 10 = 1
        assert rastrigin(np.array([1.0])) == pytest.approx(1.0)

    def test_periodicity(self):
        """测试周期性"""
        # Rastrigin 函数在整数点有特殊性质
        x1 = np.array([1.0, 0.0])
        x2 = np.array([-1.0, 0.0])
        assert rastrigin(x1) == pytest.approx(rastrigin(x2))


class TestAckley:
    """Ackley 函数测试"""

    def test_optimal(self):
        """测试最优解"""
        x = np.zeros(5)
        assert ackley(x) == pytest.approx(0.0, abs=1e-10)

    def test_known_values(self):
        """测试已知值"""
        # f(0) = 0
        assert ackley(np.array([0.0])) == pytest.approx(0.0, abs=1e-10)

    def test_non_negative(self):
        """测试非负性"""
        # Ackley 函数值应该非负
        for _ in range(100):
            x = np.random.uniform(-32, 32, 3)
            assert ackley(x) >= -1e-10  # 允许小的数值误差


class TestGriewank:
    """Griewank 函数测试"""

    def test_optimal(self):
        """测试最优解"""
        x = np.zeros(5)
        assert griewank(x) == pytest.approx(0.0, abs=1e-10)

    def test_known_values(self):
        """测试已知值"""
        # f(0) = 0
        assert griewank(np.array([0.0])) == pytest.approx(0.0, abs=1e-10)

    def test_non_negative(self):
        """测试非负性"""
        # Griewank 函数值应该非负
        for _ in range(100):
            x = np.random.uniform(-600, 600, 3)
            assert griewank(x) >= -1e-10  # 允许小的数值误差


class TestGetFunction:
    """get_function 测试"""

    def test_get_existing_function(self):
        """测试获取存在的函数"""
        for name in BENCHMARK_FUNCTIONS:
            func_info = get_function(name)
            assert "function" in func_info
            assert "bounds" in func_info
            assert "optimal" in func_info

    def test_get_nonexistent_function(self):
        """测试获取不存在的函数"""
        with pytest.raises(KeyError):
            get_function("nonexistent_function")

    def test_all_functions_optimal(self):
        """测试所有函数的最优值"""
        for name, func_info in BENCHMARK_FUNCTIONS.items():
            func = func_info["function"]
            optimal_pos = func_info["optimal_position"](2)
            optimal_val = func(optimal_pos)
            assert optimal_val == pytest.approx(0.0, abs=1e-6), f"{name} 的最优值不为 0"


class TestBenchmarkFunctions:
    """测试函数注册表测试"""

    def test_registry_complete(self):
        """测试注册表完整性"""
        expected = ["sphere", "rosenbrock", "rastrigin", "ackley", "griewank"]
        for name in expected:
            assert name in BENCHMARK_FUNCTIONS

    def test_registry_structure(self):
        """测试注册表结构"""
        for name, info in BENCHMARK_FUNCTIONS.items():
            assert "function" in info
            assert "bounds" in info
            assert "optimal" in info
            assert "optimal_position" in info
            assert "description" in info

            # 测试边界
            assert info["bounds"][0] < info["bounds"][1]

            # 测试最优位置函数
            pos = info["optimal_position"](3)
            assert len(pos) == 3
