"""测试函数测试"""

import numpy as np
import pytest
from src.functions import QuadraticFunction, RosenbrockFunction, HimmelblauFunction


class TestQuadraticFunction:
    """二次函数测试"""

    def test_basic_initialization(self):
        """测试基本初始化"""
        func = QuadraticFunction(a=1.0, b=1.0)
        assert func.name == 'quadratic'
        assert func.ndim == 2
        assert func.a == 1.0
        assert func.b == 1.0

    def test_function_value(self):
        """测试函数值计算"""
        func = QuadraticFunction(a=1.0, b=1.0, center=np.array([0, 0]))

        # 最小值点
        x = np.array([0, 0])
        assert func(x) == 0.0

        # 其他点
        x = np.array([1, 1])
        expected = 0.5 * (1 * 1**2 + 1 * 1**2)
        assert abs(func(x) - expected) < 1e-10

    def test_gradient(self):
        """测试梯度计算"""
        func = QuadraticFunction(a=1.0, b=1.0, center=np.array([0, 0]))

        # 最小值点梯度为 0
        x = np.array([0, 0])
        grad = func.gradient(x)
        np.testing.assert_array_almost_equal(grad, [0, 0])

        # 其他点
        x = np.array([1, 1])
        grad = func.gradient(x)
        np.testing.assert_array_almost_equal(grad, [1, 1])

    def test_minimum(self):
        """测试最小值"""
        center = np.array([1, 2])
        func = QuadraticFunction(a=1.0, b=1.0, center=center)

        min_x, min_val = func.minimum()
        np.testing.assert_array_almost_equal(min_x, center)
        assert min_val == 0.0

    def test_initial_point(self):
        """测试初始点"""
        func = QuadraticFunction()
        x0 = func.initial_point()
        assert len(x0) == 2

    def test_is_minimum(self):
        """测试最小值检查"""
        center = np.array([0, 0])
        func = QuadraticFunction(a=1.0, b=1.0, center=center)

        # 接近最小值
        x = np.array([0.001, 0.001])
        assert func.is_minimum(x, tol=0.01)

        # 远离最小值
        x = np.array([1, 1])
        assert not func.is_minimum(x, tol=0.01)

    def test_search_range(self):
        """测试搜索范围"""
        func = QuadraticFunction()
        ranges = func.search_range()
        assert len(ranges) == 2
        assert ranges[0] == (-5, 5)
        assert ranges[1] == (-5, 5)


class TestRosenbrockFunction:
    """Rosenbrock 函数测试"""

    def test_basic_initialization(self):
        """测试基本初始化"""
        func = RosenbrockFunction(a=1.0, b=100.0)
        assert func.name == 'rosenbrock'
        assert func.ndim == 2
        assert func.a == 1.0
        assert func.b == 100.0

    def test_function_value(self):
        """测试函数值计算"""
        func = RosenbrockFunction(a=1.0, b=100.0)

        # 最小值点 (1, 1)
        x = np.array([1, 1])
        assert abs(func(x)) < 1e-10

        # 其他点
        x = np.array([0, 0])
        expected = (1 - 0)**2 + 100 * (0 - 0**2)**2
        assert abs(func(x) - expected) < 1e-10

    def test_gradient(self):
        """测试梯度计算"""
        func = RosenbrockFunction(a=1.0, b=100.0)

        # 最小值点梯度为 0
        x = np.array([1, 1])
        grad = func.gradient(x)
        np.testing.assert_array_almost_equal(grad, [0, 0], decimal=5)

    def test_minimum(self):
        """测试最小值"""
        func = RosenbrockFunction(a=1.0, b=100.0)

        min_x, min_val = func.minimum()
        np.testing.assert_array_almost_equal(min_x, [1, 1])
        assert abs(min_val) < 1e-10

    def test_initial_point(self):
        """测试初始点"""
        func = RosenbrockFunction()
        x0 = func.initial_point()
        assert len(x0) == 2

    def test_hessian(self):
        """测试海森矩阵"""
        func = RosenbrockFunction(a=1.0, b=100.0)

        # 最小值点的海森矩阵
        x = np.array([1, 1])
        H = func.hessian(x)
        assert H.shape == (2, 2)

        # 海森矩阵应该是对称的
        assert abs(H[0, 1] - H[1, 0]) < 1e-10

    def test_search_range(self):
        """测试搜索范围"""
        func = RosenbrockFunction()
        ranges = func.search_range()
        assert len(ranges) == 2
        assert ranges[0] == (-2, 2)
        assert ranges[1] == (-1, 3)


class TestHimmelblauFunction:
    """Himmelblau 函数测试"""

    def test_basic_initialization(self):
        """测试基本初始化"""
        func = HimmelblauFunction()
        assert func.name == 'himmelblau'
        assert func.ndim == 2

    def test_function_value(self):
        """测试函数值计算"""
        func = HimmelblauFunction()

        # 最小值点 (3, 2)
        x = np.array([3, 2])
        assert abs(func(x)) < 1e-10

        # 其他点
        x = np.array([0, 0])
        expected = (0 + 0 - 11)**2 + (0 + 0 - 7)**2
        assert abs(func(x) - expected) < 1e-10

    def test_gradient(self):
        """测试梯度计算"""
        func = HimmelblauFunction()

        # 最小值点梯度为 0
        x = np.array([3, 2])
        grad = func.gradient(x)
        np.testing.assert_array_almost_equal(grad, [0, 0], decimal=5)

    def test_minimum(self):
        """测试最小值"""
        func = HimmelblauFunction()

        min_x, min_val = func.minimum()
        np.testing.assert_array_almost_equal(min_x, [3, 2])
        assert abs(min_val) < 1e-10

    def test_all_minima(self):
        """测试所有最小值点"""
        func = HimmelblauFunction()

        minima = func.all_minima()
        assert len(minima) == 4

        # 所有最小值点的函数值应该为 0
        for x in minima:
            assert abs(func(x)) < 1e-5

    def test_initial_point(self):
        """测试初始点"""
        func = HimmelblauFunction()
        x0 = func.initial_point()
        assert len(x0) == 2

    def test_search_range(self):
        """测试搜索范围"""
        func = HimmelblauFunction()
        ranges = func.search_range()
        assert len(ranges) == 2
        assert ranges[0] == (-5, 5)
        assert ranges[1] == (-5, 5)


class TestFunctionProperties:
    """测试函数性质测试"""

    def test_gradient_consistency(self):
        """测试梯度一致性"""
        # 使用有限差分验证梯度
        epsilon = 1e-6

        functions = [
            QuadraticFunction(),
            RosenbrockFunction(),
            HimmelblauFunction()
        ]

        for func in functions:
            # 随机选择一个点
            x = np.random.uniform(-2, 2, size=2)

            # 解析梯度
            grad_analytical = func.gradient(x)

            # 数值梯度
            grad_numerical = np.zeros_like(x)
            for i in range(len(x)):
                x_plus = x.copy()
                x_minus = x.copy()
                x_plus[i] += epsilon
                x_minus[i] -= epsilon
                grad_numerical[i] = (func(x_plus) - func(x_minus)) / (2 * epsilon)

            # 比较
            np.testing.assert_array_almost_equal(
                grad_analytical, grad_numerical, decimal=5
            )

    def test_minimum_is_global(self):
        """测试最小值是全局最小值"""
        functions = [
            QuadraticFunction(),
            HimmelblauFunction()
        ]

        for func in functions:
            min_x, min_val = func.minimum()

            # 在搜索范围内随机采样
            ranges = func.search_range()
            for _ in range(100):
                x = np.array([
                    np.random.uniform(r[0], r[1])
                    for r in ranges
                ])
                # 函数值应该 >= 最小值
                assert func(x) >= min_val - 1e-10


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
