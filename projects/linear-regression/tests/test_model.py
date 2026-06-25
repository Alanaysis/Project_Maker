"""线性回归模型测试

测试所有回归模型：LinearRegression, RidgeRegression, LassoRegression, ElasticNet
"""

import numpy as np
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.model import LinearRegression, RidgeRegression, LassoRegression, ElasticNet


class TestLinearRegression:
    """线性回归模型测试"""

    def test_initialization(self):
        """测试模型初始化"""
        model = LinearRegression(learning_rate=0.01, n_iterations=100)
        assert model.learning_rate == 0.01
        assert model.n_iterations == 100
        assert model.weights is None
        assert model.bias == 0.0

    def test_fit_basic(self):
        """测试基本的模型训练"""
        model = LinearRegression(learning_rate=0.01, n_iterations=100)
        X = np.array([[1], [2], [3]])
        y = np.array([2, 4, 6])

        model.fit(X, y)

        assert model.weights is not None
        assert len(model.weights) == 1
        assert len(model.losses) == 100

    def test_fit_convergence(self):
        """测试模型收敛"""
        np.random.seed(42)
        X = 2 * np.random.rand(100, 1)
        y = 4 + 3 * X.flatten() + np.random.randn(100) * 0.1

        model = LinearRegression(learning_rate=0.1, n_iterations=500)
        model.fit(X, y)

        assert model.losses[-1] < model.losses[0]

    def test_predict_basic(self):
        """测试基本的预测功能"""
        model = LinearRegression(learning_rate=0.01, n_iterations=100)
        X_train = np.array([[1], [2], [3]])
        y_train = np.array([2, 4, 6])

        model.fit(X_train, y_train)

        X_test = np.array([[4]])
        y_pred = model.predict(X_test)

        assert abs(y_pred[0] - 8) < 1.0

    def test_predict_without_fit(self):
        """测试未训练时预测"""
        model = LinearRegression()
        X = np.array([[1], [2], [3]])

        with pytest.raises(RuntimeError):
            model.predict(X)

    def test_fit_1d_input(self):
        """测试 1D 输入"""
        model = LinearRegression(learning_rate=0.01, n_iterations=100)
        X = np.array([1, 2, 3])
        y = np.array([2, 4, 6])

        model.fit(X, y)

        assert model.weights is not None
        assert len(model.weights) == 1

    def test_fit_multiple_features(self):
        """测试多特征输入"""
        model = LinearRegression(learning_rate=0.01, n_iterations=100)
        X = np.array([[1, 2], [3, 4], [5, 6]])
        y = np.array([5, 11, 17])

        model.fit(X, y)

        assert model.weights is not None
        assert len(model.weights) == 2

    def test_score(self):
        """测试 R2 分数"""
        np.random.seed(42)
        X = 2 * np.random.rand(100, 1)
        y = 4 + 3 * X.flatten() + np.random.randn(100) * 0.1

        model = LinearRegression(learning_rate=0.1, n_iterations=500)
        model.fit(X, y)

        score = model.score(X, y)
        assert score > 0.9

    def test_get_params(self):
        """测试获取参数"""
        model = LinearRegression(learning_rate=0.05, n_iterations=200)
        params = model.get_params()

        assert params["learning_rate"] == 0.05
        assert params["n_iterations"] == 200
        assert params["weights"] is None

    def test_repr(self):
        """测试字符串表示"""
        model = LinearRegression(learning_rate=0.01, n_iterations=100)
        repr_str = repr(model)

        assert "LinearRegression" in repr_str
        assert "0.01" in repr_str
        assert "100" in repr_str

    def test_dimension_mismatch(self):
        """测试维度不匹配"""
        model = LinearRegression(learning_rate=0.01, n_iterations=100)
        X = np.array([[1], [2], [3]])
        y = np.array([2, 4])

        with pytest.raises(ValueError):
            model.fit(X, y)


class TestLinearRegressionNormalEquation:
    """正规方程法测试"""

    def test_normal_equation_basic(self):
        """测试正规方程基本功能"""
        np.random.seed(42)
        X = 2 * np.random.rand(100, 1)
        y = 4 + 3 * X.flatten() + np.random.randn(100) * 0.1

        model = LinearRegression(method="normal_equation")
        model.fit(X, y)

        assert model.weights is not None
        assert abs(model.weights[0] - 3) < 0.5
        assert abs(model.bias - 4) < 0.5

    def test_normal_equation_multiple_features(self):
        """测试正规方程多特征"""
        np.random.seed(42)
        X = np.random.randn(100, 3)
        true_w = np.array([2.0, -1.0, 3.0])
        y = X @ true_w + 1.0 + np.random.randn(100) * 0.1

        model = LinearRegression(method="normal_equation")
        model.fit(X, y)

        np.testing.assert_array_almost_equal(model.weights, true_w, decimal=0)

    def test_normal_equation_vs_gradient_descent(self):
        """测试正规方程和梯度下降结果相近"""
        np.random.seed(42)
        X = np.random.randn(50, 2)
        y = X @ np.array([1.5, -2.0]) + 3.0

        model_ne = LinearRegression(method="normal_equation")
        model_ne.fit(X, y)

        model_gd = LinearRegression(learning_rate=0.01, n_iterations=2000)
        model_gd.fit(X, y)

        # 两种方法应该得到相近的结果
        np.testing.assert_array_almost_equal(model_ne.weights, model_gd.weights, decimal=1)


class TestLinearRegressionIntegration:
    """集成测试"""

    def test_simple_linear_relationship(self):
        """测试简单线性关系"""
        X = np.array([[1], [2], [3], [4], [5]])
        y = 2 * X.flatten() + 1

        model = LinearRegression(learning_rate=0.01, n_iterations=1000)
        model.fit(X, y)

        assert abs(model.weights[0] - 2) < 0.1
        assert abs(model.bias - 1) < 0.5

    def test_noisy_data(self):
        """测试带噪声的数据"""
        np.random.seed(42)
        X = 2 * np.random.rand(100, 1)
        y = 4 + 3 * X.flatten() + np.random.randn(100) * 0.5

        model = LinearRegression(learning_rate=0.1, n_iterations=500)
        model.fit(X, y)

        score = model.score(X, y)
        assert score > 0.8


class TestRidgeRegression:
    """岭回归测试"""

    def test_initialization(self):
        """测试初始化"""
        model = RidgeRegression(alpha=1.0)
        assert model.alpha == 1.0
        assert model.weights is None

    def test_fit_basic(self):
        """测试基本训练"""
        np.random.seed(42)
        X = np.random.randn(50, 3)
        y = X @ np.array([1.0, 2.0, 3.0]) + 1.0

        model = RidgeRegression(alpha=0.1, learning_rate=0.01, n_iterations=500)
        model.fit(X, y)

        assert model.weights is not None
        assert len(model.weights) == 3

    def test_predict(self):
        """测试预测"""
        np.random.seed(42)
        X = np.random.randn(50, 2)
        y = X @ np.array([1.0, -1.0]) + 0.5

        model = RidgeRegression(alpha=0.1, learning_rate=0.01, n_iterations=500)
        model.fit(X, y)

        y_pred = model.predict(X)
        assert y_pred.shape == (50,)

    def test_score(self):
        """测试 R2 分数"""
        np.random.seed(42)
        X = np.random.randn(100, 3)
        y = X @ np.array([2.0, -1.0, 0.5]) + 1.0

        model = RidgeRegression(alpha=0.1, learning_rate=0.01, n_iterations=1000)
        model.fit(X, y)

        score = model.score(X, y)
        assert score > 0.8

    def test_normal_equation(self):
        """测试正规方程求解"""
        np.random.seed(42)
        X = np.random.randn(50, 2)
        y = X @ np.array([1.0, -1.0]) + 0.5

        model = RidgeRegression(alpha=1.0, method="normal_equation")
        model.fit(X, y)

        assert model.weights is not None
        assert model.score(X, y) > 0.8

    def test_weight_shrinkage(self):
        """测试权重收缩效果"""
        np.random.seed(42)
        X = np.random.randn(50, 5)
        y = X @ np.array([3.0, -2.0, 0.0, 0.0, 0.0]) + 1.0

        # 无正则化
        model_no_reg = LinearRegression(learning_rate=0.01, n_iterations=1000)
        model_no_reg.fit(X, y)

        # 强正则化
        model_ridge = RidgeRegression(alpha=10.0, learning_rate=0.01, n_iterations=1000)
        model_ridge.fit(X, y)

        # Ridge 的权重应该更小
        assert np.sum(model_ridge.weights ** 2) < np.sum(model_no_reg.weights ** 2)

    def test_repr(self):
        """测试字符串表示"""
        model = RidgeRegression(alpha=1.0, learning_rate=0.01, n_iterations=100)
        repr_str = repr(model)
        assert "RidgeRegression" in repr_str
        assert "1.0" in repr_str


class TestLassoRegression:
    """Lasso 回归测试"""

    def test_initialization(self):
        """测试初始化"""
        model = LassoRegression(alpha=1.0)
        assert model.alpha == 1.0

    def test_fit_basic(self):
        """测试基本训练"""
        np.random.seed(42)
        X = np.random.randn(50, 3)
        y = X @ np.array([1.0, 2.0, 3.0]) + 1.0

        model = LassoRegression(alpha=0.1, learning_rate=0.01, n_iterations=500)
        model.fit(X, y)

        assert model.weights is not None
        assert len(model.weights) == 3

    def test_predict(self):
        """测试预测"""
        np.random.seed(42)
        X = np.random.randn(50, 2)
        y = X @ np.array([1.0, -1.0]) + 0.5

        model = LassoRegression(alpha=0.1, learning_rate=0.01, n_iterations=500)
        model.fit(X, y)

        y_pred = model.predict(X)
        assert y_pred.shape == (50,)

    def test_sparsity(self):
        """测试稀疏性（L1 特性）"""
        np.random.seed(42)
        X = np.random.randn(100, 10)
        # 只有前 3 个特征有用
        true_w = np.zeros(10)
        true_w[:3] = np.array([3.0, -2.0, 1.0])
        y = X @ true_w + 1.0

        model = LassoRegression(alpha=5.0, learning_rate=0.01, n_iterations=3000)
        model.fit(X, y)

        # 强 L1 正则化应该使部分权重接近零
        n_near_zero = np.sum(np.abs(model.weights) < 0.1)
        assert n_near_zero > 0  # 至少有一些权重被压缩

    def test_get_params_nonzero(self):
        """测试获取非零权重数量"""
        np.random.seed(42)
        X = np.random.randn(50, 3)
        y = X @ np.array([1.0, 2.0, 3.0]) + 1.0

        model = LassoRegression(alpha=0.1, learning_rate=0.01, n_iterations=500)
        model.fit(X, y)

        params = model.get_params()
        assert "n_nonzero_weights" in params

    def test_repr(self):
        """测试字符串表示"""
        model = LassoRegression(alpha=1.0)
        repr_str = repr(model)
        assert "LassoRegression" in repr_str


class TestElasticNet:
    """Elastic Net 测试"""

    def test_initialization(self):
        """测试初始化"""
        model = ElasticNet(alpha=1.0, l1_ratio=0.5)
        assert model.alpha == 1.0
        assert model.l1_ratio == 0.5

    def test_fit_basic(self):
        """测试基本训练"""
        np.random.seed(42)
        X = np.random.randn(50, 3)
        y = X @ np.array([1.0, 2.0, 3.0]) + 1.0

        model = ElasticNet(alpha=0.1, l1_ratio=0.5, learning_rate=0.01, n_iterations=500)
        model.fit(X, y)

        assert model.weights is not None
        assert len(model.weights) == 3

    def test_predict(self):
        """测试预测"""
        np.random.seed(42)
        X = np.random.randn(50, 2)
        y = X @ np.array([1.0, -1.0]) + 0.5

        model = ElasticNet(alpha=0.1, l1_ratio=0.5, learning_rate=0.01, n_iterations=500)
        model.fit(X, y)

        y_pred = model.predict(X)
        assert y_pred.shape == (50,)

    def test_l1_ratio_zero_is_ridge(self):
        """测试 l1_ratio=0 退化为 Ridge"""
        np.random.seed(42)
        X = np.random.randn(50, 3)
        y = X @ np.array([1.0, 2.0, 3.0]) + 1.0

        model = ElasticNet(alpha=0.1, l1_ratio=0.0, learning_rate=0.01, n_iterations=1000)
        model.fit(X, y)

        # l1_ratio=0 时，没有 L1 惩罚，权重不应稀疏
        params = model.get_params()
        assert params["n_nonzero_weights"] == 3  # 所有权重都应非零

    def test_l1_ratio_one_is_lasso(self):
        """测试 l1_ratio=1 退化为 Lasso"""
        np.random.seed(42)
        X = np.random.randn(100, 10)
        true_w = np.zeros(10)
        true_w[:3] = np.array([3.0, -2.0, 1.0])
        y = X @ true_w + 1.0

        model = ElasticNet(
            alpha=5.0, l1_ratio=1.0, learning_rate=0.01, n_iterations=3000
        )
        model.fit(X, y)

        # l1_ratio=1 时，等同于 Lasso，应有稀疏性
        n_near_zero = np.sum(np.abs(model.weights) < 0.1)
        assert n_near_zero > 0

    def test_repr(self):
        """测试字符串表示"""
        model = ElasticNet(alpha=1.0, l1_ratio=0.5)
        repr_str = repr(model)
        assert "ElasticNet" in repr_str
        assert "0.5" in repr_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
