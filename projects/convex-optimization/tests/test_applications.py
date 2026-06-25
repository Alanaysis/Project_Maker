"""
实际应用测试
"""

import numpy as np
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.applications.least_squares import (
    LeastSquares,
    RidgeRegression,
    LassoRegression,
)
from src.applications.svm import SVM
from src.applications.portfolio import PortfolioOptimizer


class TestLeastSquares:
    """最小二乘测试"""

    def test_analytical_solution(self):
        """测试解析解"""
        A = np.array([[1, 0], [0, 1], [1, 1]])
        b = np.array([1, 2, 3])
        ls = LeastSquares(A, b)

        x = ls.solve_analytical()
        # 验证残差最小
        residual = ls.residual(x)
        assert np.linalg.norm(residual) < 1e-10

    def test_gradient_descent(self):
        """测试梯度下降"""
        A = np.array([[1, 0], [0, 1], [1, 1]])
        b = np.array([1, 2, 3])
        ls = LeastSquares(A, b)

        x_gd = ls.solve_gradient_descent(max_iter=10000, learning_rate=0.01)
        x_analytical = ls.solve_analytical()

        np.testing.assert_allclose(x_gd, x_analytical, atol=1e-3)

    def test_qr_solution(self):
        """测试 QR 分解"""
        A = np.array([[1, 0], [0, 1], [1, 1]])
        b = np.array([1, 2, 3])
        ls = LeastSquares(A, b)

        x_qr = ls.solve_qr()
        x_analytical = ls.solve_analytical()

        np.testing.assert_allclose(x_qr, x_analytical, atol=1e-10)

    def test_svd_solution(self):
        """测试 SVD 分解"""
        A = np.array([[1, 0], [0, 1], [1, 1]])
        b = np.array([1, 2, 3])
        ls = LeastSquares(A, b)

        x_svd = ls.solve_svd()
        x_analytical = ls.solve_analytical()

        np.testing.assert_allclose(x_svd, x_analytical, atol=1e-10)


class TestRidgeRegression:
    """岭回归测试"""

    def test_solution(self):
        """测试解"""
        A = np.array([[1, 0], [0, 1], [1, 1]])
        b = np.array([1, 2, 3])
        ridge = RidgeRegression(A, b, lambda_=0.1)

        x = ridge.solve_analytical()
        assert len(x) == 2

    def test_regularization_effect(self):
        """测试正则化效果"""
        A = np.array([[1, 0], [0, 1]])
        b = np.array([1, 2])

        # 无正则化
        ls = LeastSquares(A, b)
        x_ls = ls.solve_analytical()

        # 有正则化
        ridge = RidgeRegression(A, b, lambda_=1.0)
        x_ridge = ridge.solve_analytical()

        # 正则化应该使解更小
        assert np.linalg.norm(x_ridge) < np.linalg.norm(x_ls)

    def test_gradient_descent(self):
        """测试梯度下降"""
        A = np.array([[1, 0], [0, 1], [1, 1]])
        b = np.array([1, 2, 3])
        ridge = RidgeRegression(A, b, lambda_=0.1)

        x_gd = ridge.solve_gradient_descent(max_iter=10000, learning_rate=0.01)
        x_analytical = ridge.solve_analytical()

        np.testing.assert_allclose(x_gd, x_analytical, atol=1e-3)


class TestLassoRegression:
    """Lasso 回归测试"""

    def test_sparsity(self):
        """测试稀疏性"""
        # 创建稀疏信号
        np.random.seed(42)
        n, m = 100, 50
        A = np.random.randn(n, m)
        x_true = np.zeros(m)
        x_true[:5] = np.random.randn(5)
        b = A @ x_true + 0.1 * np.random.randn(n)

        lasso = LassoRegression(A, b, lambda_=1.0)
        x = lasso.solve_coordinate_descent()

        # 应该有稀疏性
        n_nonzero = np.sum(np.abs(x) > 1e-6)
        assert n_nonzero < m

    def test_coordinate_descent(self):
        """测试坐标下降"""
        A = np.array([[1, 0], [0, 1], [1, 1]])
        b = np.array([1, 2, 3])
        lasso = LassoRegression(A, b, lambda_=0.1)

        x = lasso.solve_coordinate_descent()
        assert len(x) == 2

    def test_proximal_gradient(self):
        """测试近端梯度法"""
        A = np.array([[1, 0], [0, 1], [1, 1]])
        b = np.array([1, 2, 3])
        lasso = LassoRegression(A, b, lambda_=0.1)

        x_cd = lasso.solve_coordinate_descent()
        x_pg = lasso.solve_proximal_gradient(max_iter=10000)

        # 两种方法应该给出相似结果
        np.testing.assert_allclose(x_cd, x_pg, atol=0.1)


class TestSVM:
    """SVM 测试"""

    def test_linear_separable(self):
        """测试线性可分数据"""
        np.random.seed(42)

        # 生成线性可分数据
        X1 = np.random.randn(20, 2) + np.array([2, 2])
        X2 = np.random.randn(20, 2) + np.array([-2, -2])
        X = np.vstack([X1, X2])
        y = np.array([1] * 20 + [-1] * 20)

        svm = SVM(C=1.0, max_iter=1000)
        result = svm.fit(X, y)

        # 应该找到支持向量
        assert result.n_support > 0

        # 训练准确率应该很高
        predictions = svm.predict(X, result)
        accuracy = np.mean(predictions == y)
        assert accuracy > 0.9

    def test_margin(self):
        """测试间隔"""
        np.random.seed(42)

        # 简单的线性可分数据
        X = np.array([[1, 0], [0, 1], [-1, 0], [0, -1]])
        y = np.array([1, 1, -1, -1])

        svm = SVM(C=10.0, max_iter=1000)
        result = svm.fit(X, y)

        # 权重向量应该正确
        w_norm = np.linalg.norm(result.w)
        assert w_norm > 0


class TestPortfolioOptimizer:
    """投资组合优化测试"""

    def test_min_variance(self):
        """测试最小方差组合"""
        np.random.seed(42)
        returns = np.random.randn(100, 3) * 0.01 + 0.001

        optimizer = PortfolioOptimizer(returns)
        result = optimizer.min_variance_portfolio()

        # 权重应该和为 1
        assert abs(np.sum(result.weights) - 1.0) < 1e-6

        # 权重应该非负
        assert np.all(result.weights >= -1e-6)

    def test_max_sharpe(self):
        """测试最大夏普比率组合"""
        np.random.seed(42)
        returns = np.random.randn(100, 3) * 0.01 + 0.001

        optimizer = PortfolioOptimizer(returns, risk_free_rate=0.0001)
        result = optimizer.max_sharpe_portfolio()

        # 权重应该和为 1
        assert abs(np.sum(result.weights) - 1.0) < 1e-6

    def test_efficient_frontier(self):
        """测试有效前沿"""
        np.random.seed(42)
        returns = np.random.randn(100, 3) * 0.01 + 0.001

        optimizer = PortfolioOptimizer(returns)
        portfolios = optimizer.efficient_frontier(n_points=10)

        # 应该有多个组合
        assert len(portfolios) > 0

        # 风险应该递增
        risks = [p.risk for p in portfolios]
        for i in range(len(risks) - 1):
            assert risks[i] <= risks[i + 1] + 1e-6

    def test_risk_parity(self):
        """测试风险平价组合"""
        np.random.seed(42)
        returns = np.random.randn(100, 3) * 0.01

        optimizer = PortfolioOptimizer(returns)
        result = optimizer.risk_parity()

        # 权重应该和为 1
        assert abs(np.sum(result.weights) - 1.0) < 1e-6

        # 每个资产的风险贡献应该相似
        Sigma = optimizer.cov_matrix
        w = result.weights
        risk = np.sqrt(w @ Sigma @ w)
        marginal_risk = Sigma @ w / risk
        risk_contrib = w * marginal_risk

        # 风险贡献应该近似相等
        assert np.std(risk_contrib) < 0.1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
