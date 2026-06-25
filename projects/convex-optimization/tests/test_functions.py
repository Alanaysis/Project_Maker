"""
凸函数测试
"""

import numpy as np
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.functions.convex_function import ConvexFunction
from src.functions.test_functions import (
    QuadraticFunction,
    RosenbrockFunction,
    LogisticLoss,
    HuberLoss,
    L1Norm,
    ElasticNet,
)


class TestQuadraticFunction:
    """二次函数测试"""

    def test_function_value(self):
        """测试函数值计算"""
        A = np.array([[2, 0], [0, 2]])
        b = np.array([0, 0])
        f = QuadraticFunction(A, b)

        x = np.array([1, 1])
        assert abs(f(x) - 2.0) < 1e-10

    def test_gradient(self):
        """测试梯度计算"""
        A = np.array([[2, 0], [0, 2]])
        b = np.array([1, 1])
        f = QuadraticFunction(A, b)

        x = np.array([1, 1])
        grad = f.gradient(x)
        expected = np.array([3, 3])
        np.testing.assert_allclose(grad, expected)

    def test_hessian(self):
        """测试海森矩阵"""
        A = np.array([[2, 1], [1, 3]])
        f = QuadraticFunction(A)

        x = np.array([0, 0])
        H = f.hessian(x)
        np.testing.assert_allclose(H, A)

    def test_convexity(self):
        """测试凸性"""
        # 正定矩阵 -> 凸函数
        A = np.array([[2, 0], [0, 2]])
        f = QuadraticFunction(A)
        x = np.array([1, 0])
        y = np.array([0, 1])
        assert f.is_convex_by_definition(x, y)

    def test_strong_convexity(self):
        """测试强凸性"""
        A = np.array([[4, 0], [0, 4]])
        f = QuadraticFunction(A)
        x = np.array([0, 0])
        assert f.is_strongly_convex(x, mu=2.0)
        assert not f.is_strongly_convex(x, mu=5.0)

    def test_diagonal_creation(self):
        """测试对角矩阵创建"""
        eigenvalues = np.array([1, 2, 3])
        f = QuadraticFunction.create_diagonal(eigenvalues)
        expected = np.diag(eigenvalues)
        np.testing.assert_allclose(f.A, expected)


class TestRosenbrockFunction:
    """Rosenbrock 函数测试"""

    def test_function_value(self):
        """测试函数值计算"""
        f = RosenbrockFunction(a=1, b=100)
        x = np.array([1, 1])  # 最小值点
        assert abs(f(x)) < 1e-10

    def test_gradient_at_minimum(self):
        """测试最小值点梯度"""
        f = RosenbrockFunction(a=1, b=100)
        x = np.array([1, 1])
        grad = f.gradient(x)
        np.testing.assert_allclose(grad, [0, 0], atol=1e-10)

    def test_non_convexity(self):
        """测试非凸性"""
        f = RosenbrockFunction(a=1, b=100)
        x = np.array([0, 0])
        y = np.array([2, 4])
        # Rosenbrock 函数是非凸的
        assert not f.is_convex_by_definition(x, y, num_samples=1000)


class TestLogisticLoss:
    """逻辑损失测试"""

    def test_function_value(self):
        """测试函数值计算"""
        X = np.array([[1, 0], [0, 1]])
        y = np.array([1, -1])
        f = LogisticLoss(X, y)

        w = np.array([0, 0])
        expected = np.log(2)  # log(1 + exp(0))
        assert abs(f(w) - expected) < 1e-10

    def test_gradient(self):
        """测试梯度计算"""
        X = np.array([[1, 0], [0, 1]])
        y = np.array([1, -1])
        f = LogisticLoss(X, y)

        w = np.array([0, 0])
        grad = f.gradient(w)
        # 在零点，梯度应该是 -0.5/n * X^T y，其中 n=2
        expected = -0.5 / 2 * X.T @ y
        np.testing.assert_allclose(grad, expected)

    def test_convexity(self):
        """测试凸性"""
        X = np.array([[1, 0], [0, 1], [1, 1]])
        y = np.array([1, -1, 1])
        f = LogisticLoss(X, y)

        x = np.array([0, 0])
        y_vec = np.array([1, 1])
        assert f.is_convex_by_definition(x, y_vec)


class TestHuberLoss:
    """Huber 损失测试"""

    def test_smooth_region(self):
        """测试光滑区域"""
        f = HuberLoss(delta=1.0)
        x = np.array([0.5])
        expected = 0.5 * 0.5 ** 2
        assert abs(f(x) - expected) < 1e-10

    def test_linear_region(self):
        """测试线性区域"""
        f = HuberLoss(delta=1.0)
        x = np.array([2.0])
        expected = 1.0 * (2.0 - 0.5 * 1.0)
        assert abs(f(x) - expected) < 1e-10

    def test_gradient_smooth(self):
        """测试光滑区域梯度"""
        f = HuberLoss(delta=1.0)
        x = np.array([0.5])
        grad = f.gradient(x)
        expected = np.array([0.5])
        np.testing.assert_allclose(grad, expected)

    def test_gradient_linear(self):
        """测试线性区域梯度"""
        f = HuberLoss(delta=1.0)
        x = np.array([2.0])
        grad = f.gradient(x)
        expected = np.array([1.0])
        np.testing.assert_allclose(grad, expected)

    def test_convexity(self):
        """测试凸性"""
        f = HuberLoss(delta=1.0)
        x = np.array([-2, 0])
        y = np.array([2, 1])
        assert f.is_convex_by_definition(x, y)


class TestL1Norm:
    """L1 范数测试"""

    def test_function_value(self):
        """测试函数值计算"""
        f = L1Norm()
        x = np.array([1, -2, 3])
        assert f(x) == 6.0

    def test_subgradient(self):
        """测试次梯度"""
        f = L1Norm()
        x = np.array([1, -2, 0])
        subgrad = f.subgradient(x)
        expected = np.array([1, -1, 0])
        np.testing.assert_array_equal(subgrad, expected)

    def test_gradient_error(self):
        """测试不可微点报错"""
        f = L1Norm()
        x = np.array([0, 0])
        with pytest.raises(ValueError):
            f.gradient(x)


class TestElasticNet:
    """弹性网络测试"""

    def test_function_value(self):
        """测试函数值计算"""
        A = np.array([[1, 0], [0, 1]])
        b = np.array([1, 1])
        f = ElasticNet(A, b, lambda1=0.1, lambda2=0.1)

        x = np.array([0, 0])
        expected = 0.5 * np.sum(b ** 2)  # 0.5 * ||b||²
        assert abs(f(x) - expected) < 1e-10

    def test_convexity(self):
        """测试凸性"""
        A = np.array([[1, 0], [0, 1]])
        b = np.array([1, 1])
        f = ElasticNet(A, b, lambda1=0.1, lambda2=0.1)

        x = np.array([0, 0])
        y = np.array([1, 1])
        assert f.is_convex_by_definition(x, y)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
