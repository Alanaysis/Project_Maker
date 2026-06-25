"""
优化算法测试
"""

import numpy as np
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.functions.test_functions import QuadraticFunction
from src.optimizers.gradient_descent import GradientDescent, Adam
from src.optimizers.newton_method import NewtonMethod
from src.optimizers.bfgs import BFGS, LBFGS


class TestGradientDescent:
    """梯度下降测试"""

    def test_quadratic_convergence(self):
        """测试二次函数收敛"""
        A = np.array([[2, 0], [0, 2]])
        f = QuadraticFunction(A)
        x0 = np.array([10.0, 10.0])

        optimizer = GradientDescent(learning_rate=0.1, max_iter=1000)
        result = optimizer.optimize(f, f.gradient, x0)

        assert result.success
        np.testing.assert_allclose(result.x, [0, 0], atol=1e-4)

    def test_momentum(self):
        """测试动量梯度下降"""
        A = np.array([[10, 0], [0, 1]])
        f = QuadraticFunction(A)
        x0 = np.array([10.0, 10.0])

        optimizer = GradientDescent(
            learning_rate=0.01,
            momentum=0.9,
            max_iter=5000,
        )
        result = optimizer.optimize(f, f.gradient, x0)

        assert result.success
        np.testing.assert_allclose(result.x, [0, 0], atol=1e-3)

    def test_nesterov(self):
        """测试 Nesterov 加速梯度下降"""
        A = np.array([[2, 0], [0, 2]])
        f = QuadraticFunction(A)
        x0 = np.array([10.0, 10.0])

        optimizer = GradientDescent(
            learning_rate=0.1,
            momentum=0.9,
            nesterov=True,
            max_iter=1000,
        )
        result = optimizer.optimize(f, f.gradient, x0)

        assert result.success
        np.testing.assert_allclose(result.x, [0, 0], atol=1e-4)


class TestNewtonMethod:
    """牛顿法测试"""

    def test_quadratic_convergence(self):
        """测试二次函数收敛（应快速收敛）"""
        A = np.array([[2, 0], [0, 2]])
        f = QuadraticFunction(A)
        x0 = np.array([10.0, 10.0])

        optimizer = NewtonMethod(use_line_search=False, max_iter=10)
        result = optimizer.optimize(f, f.gradient, x0, f.hessian)

        assert result.success
        np.testing.assert_allclose(result.x, [0, 0], atol=1e-6)
        assert result.nit <= 3  # 二次函数应该快速收敛（正则化可能需要多一步）

    def test_with_line_search(self):
        """测试带线搜索的牛顿法"""
        A = np.array([[2, 0], [0, 2]])
        f = QuadraticFunction(A)
        x0 = np.array([10.0, 10.0])

        optimizer = NewtonMethod(use_line_search=True, max_iter=10)
        result = optimizer.optimize(f, f.gradient, x0, f.hessian)

        assert result.success
        np.testing.assert_allclose(result.x, [0, 0], atol=1e-10)


class TestBFGS:
    """BFGS 测试"""

    def test_quadratic_convergence(self):
        """测试二次函数收敛"""
        A = np.array([[2, 0], [0, 2]])
        f = QuadraticFunction(A)
        x0 = np.array([10.0, 10.0])

        optimizer = BFGS(max_iter=100)
        result = optimizer.optimize(f, f.gradient, x0)

        assert result.success
        np.testing.assert_allclose(result.x, [0, 0], atol=1e-4)

    def test_ill_conditioned(self):
        """测试病态问题"""
        A = np.array([[100, 0], [0, 1]])
        f = QuadraticFunction(A)
        x0 = np.array([10.0, 10.0])

        optimizer = BFGS(max_iter=1000)
        result = optimizer.optimize(f, f.gradient, x0)

        assert result.success
        np.testing.assert_allclose(result.x, [0, 0], atol=1e-3)


class TestLBFGS:
    """L-BFGS 测试"""

    def test_quadratic_convergence(self):
        """测试二次函数收敛"""
        A = np.array([[2, 0], [0, 2]])
        f = QuadraticFunction(A)
        x0 = np.array([10.0, 10.0])

        optimizer = LBFGS(m=10, max_iter=100)
        result = optimizer.optimize(f, f.gradient, x0)

        assert result.success
        np.testing.assert_allclose(result.x, [0, 0], atol=1e-4)

    def test_large_problem(self):
        """测试大规模问题"""
        n = 100
        A = np.eye(n)
        f = QuadraticFunction(A)
        x0 = np.ones(n) * 10

        optimizer = LBFGS(m=20, max_iter=500)
        result = optimizer.optimize(f, f.gradient, x0)

        assert result.success
        np.testing.assert_allclose(result.x, np.zeros(n), atol=1e-3)


class TestAdam:
    """Adam 测试"""

    def test_quadratic_convergence(self):
        """测试二次函数收敛"""
        A = np.array([[2, 0], [0, 2]])
        f = QuadraticFunction(A)
        x0 = np.array([10.0, 10.0])

        optimizer = Adam(learning_rate=0.1, max_iter=1000)
        result = optimizer.optimize(f, f.gradient, x0)

        assert result.success
        np.testing.assert_allclose(result.x, [0, 0], atol=1e-3)


class TestOptimizerComparison:
    """优化器对比测试"""

    def test_convergence_comparison(self):
        """比较不同优化器的收敛性"""
        A = np.array([[2, 0], [0, 2]])
        f = QuadraticFunction(A)
        x0 = np.array([10.0, 10.0])

        optimizers = {
            "GD": GradientDescent(learning_rate=0.1, max_iter=1000),
            "Newton": NewtonMethod(max_iter=10),
            "BFGS": BFGS(max_iter=100),
        }

        results = {}
        for name, opt in optimizers.items():
            if name == "Newton":
                results[name] = opt.optimize(f, f.gradient, x0, f.hessian)
            else:
                results[name] = opt.optimize(f, f.gradient, x0)

        # 所有优化器都应该收敛
        for name, result in results.items():
            assert result.success, f"{name} 未收敛"
            np.testing.assert_allclose(
                result.x, [0, 0], atol=1e-3,
                err_msg=f"{name} 解不准确"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
