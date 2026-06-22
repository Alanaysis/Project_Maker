"""线性回归模型测试"""

import numpy as np
import pytest
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.model import LinearRegression


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
        # 生成线性数据
        np.random.seed(42)
        X = 2 * np.random.rand(100, 1)
        y = 4 + 3 * X.flatten() + np.random.randn(100) * 0.1

        model = LinearRegression(learning_rate=0.1, n_iterations=500)
        model.fit(X, y)

        # 检查损失是否下降
        assert model.losses[-1] < model.losses[0]

    def test_predict_basic(self):
        """测试基本的预测功能"""
        model = LinearRegression(learning_rate=0.01, n_iterations=100)
        X_train = np.array([[1], [2], [3]])
        y_train = np.array([2, 4, 6])

        model.fit(X_train, y_train)

        X_test = np.array([[4]])
        y_pred = model.predict(X_test)

        # 预测值应该接近 8
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
        """测试 R² 分数"""
        np.random.seed(42)
        X = 2 * np.random.rand(100, 1)
        y = 4 + 3 * X.flatten() + np.random.randn(100) * 0.1

        model = LinearRegression(learning_rate=0.1, n_iterations=500)
        model.fit(X, y)

        score = model.score(X, y)
        assert score > 0.9  # R² 应该很高

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

    def test_loss_history(self):
        """测试损失历史记录"""
        model = LinearRegression(learning_rate=0.01, n_iterations=50)
        X = np.array([[1], [2], [3]])
        y = np.array([2, 4, 6])

        model.fit(X, y)

        assert len(model.losses) == 50
        assert all(isinstance(loss, float) for loss in model.losses)

    def test_weight_history(self):
        """测试权重历史记录"""
        model = LinearRegression(learning_rate=0.01, n_iterations=50)
        X = np.array([[1], [2], [3]])
        y = np.array([2, 4, 6])

        model.fit(X, y)

        assert len(model.weight_history) == 50
        assert all(isinstance(w, np.ndarray) for w in model.weight_history)

    def test_dimension_mismatch(self):
        """测试维度不匹配"""
        model = LinearRegression(learning_rate=0.01, n_iterations=100)
        X = np.array([[1], [2], [3]])
        y = np.array([2, 4])  # 维度不匹配

        with pytest.raises(ValueError):
            model.fit(X, y)


class TestLinearRegressionIntegration:
    """集成测试"""

    def test_simple_linear_relationship(self):
        """测试简单线性关系"""
        np.random.seed(42)

        # 生成 y = 2x + 1 的数据
        X = np.array([[1], [2], [3], [4], [5]])
        y = 2 * X.flatten() + 1

        model = LinearRegression(learning_rate=0.01, n_iterations=1000)
        model.fit(X, y)

        # 验证权重接近 2
        assert abs(model.weights[0] - 2) < 0.1

        # 验证偏置接近 1
        assert abs(model.bias - 1) < 0.5

    def test_noisy_data(self):
        """测试带噪声的数据"""
        np.random.seed(42)

        # 生成带噪声的数据
        X = 2 * np.random.rand(100, 1)
        y = 4 + 3 * X.flatten() + np.random.randn(100) * 0.5

        model = LinearRegression(learning_rate=0.1, n_iterations=500)
        model.fit(X, y)

        # 验证模型能够学习到大致的线性关系
        score = model.score(X, y)
        assert score > 0.8


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
