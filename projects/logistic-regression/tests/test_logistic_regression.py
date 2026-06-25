"""
逻辑回归模型单元测试
"""

import sys
import os
import numpy as np
import pytest

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.logistic_regression import LogisticRegression


class TestLogisticRegression:
    """逻辑回归测试类"""

    @pytest.fixture
    def simple_dataset(self):
        """简单二分类数据集"""
        np.random.seed(42)
        # 生成两类数据
        X1 = np.random.randn(50, 2) + np.array([2, 2])
        X2 = np.random.randn(50, 2) + np.array([-2, -2])
        X = np.vstack([X1, X2])
        y = np.array([1] * 50 + [0] * 50)
        return X, y

    @pytest.fixture
    def linear_separable_dataset(self):
        """线性可分数据集"""
        np.random.seed(42)
        X = np.array([
            [1, 1], [2, 2], [3, 3],  # 正类
            [-1, -1], [-2, -2], [-3, -3]  # 负类
        ])
        y = np.array([1, 1, 1, 0, 0, 0])
        return X, y

    def test_sigmoid(self):
        """测试Sigmoid函数"""
        model = LogisticRegression()

        # 测试基本sigmoid值
        z = np.array([0, 1, -1, 100, -100])
        result = model._sigmoid(z)

        # 验证sigmoid性质
        assert abs(result[0] - 0.5) < 1e-10  # sigmoid(0) = 0.5
        assert result[1] > 0.5  # sigmoid(1) > 0.5
        assert result[2] < 0.5  # sigmoid(-1) < 0.5
        assert result[3] > 0.99  # sigmoid(100) ≈ 1
        assert result[4] < 0.01  # sigmoid(-100) ≈ 0

    def test_sigmoid_range(self):
        """测试Sigmoid输出范围"""
        model = LogisticRegression()
        z = np.linspace(-20, 20, 1000)
        result = model._sigmoid(z)

        # 所有输出应在(0,1)之间（允许浮点精度误差）
        assert np.all(result > 0)
        assert np.all(result <= 1)
        # 大部分输出应严格在(0,1)之间
        assert np.sum((result > 0) & (result < 1)) > 990

    def test_loss_computation(self):
        """测试损失计算"""
        model = LogisticRegression()

        # 完美预测的损失应该接近0
        y_true = np.array([1, 0, 1, 0])
        y_pred_perfect = np.array([0.9999, 0.0001, 0.9999, 0.0001])
        loss_perfect = model._compute_loss(y_true, y_pred_perfect)
        assert loss_perfect < 0.01

        # 错误预测的损失应该很大
        y_pred_wrong = np.array([0.0001, 0.9999, 0.0001, 0.9999])
        loss_wrong = model._compute_loss(y_true, y_pred_wrong)
        assert loss_wrong > 5.0

    def test_fit_simple(self, simple_dataset):
        """测试模型训练"""
        X, y = simple_dataset
        model = LogisticRegression(learning_rate=0.1, n_iterations=1000)
        model.fit(X, y)

        # 模型应该已经训练
        assert model.weights is not None
        assert len(model.losses) == 1000

    def test_predict(self, simple_dataset):
        """测试预测功能"""
        X, y = simple_dataset
        model = LogisticRegression(learning_rate=0.1, n_iterations=1000)
        model.fit(X, y)

        predictions = model.predict(X)

        # 预测结果应该是0或1
        assert set(predictions).issubset({0, 1})
        assert len(predictions) == len(y)

    def test_predict_proba(self, simple_dataset):
        """测试概率预测"""
        X, y = simple_dataset
        model = LogisticRegression(learning_rate=0.1, n_iterations=1000)
        model.fit(X, y)

        proba = model.predict_proba(X)

        # 概率应该在(0,1)之间
        assert np.all(proba > 0)
        assert np.all(proba < 1)

    def test_accuracy(self, linear_separable_dataset):
        """测试准确率"""
        X, y = linear_separable_dataset
        model = LogisticRegression(learning_rate=0.5, n_iterations=1000)
        model.fit(X, y)

        accuracy = model.score(X, y)

        # 线性可分数据应该达到高准确率
        assert accuracy > 0.8

    def test_gradient_descent_convergence(self, simple_dataset):
        """测试梯度下降收敛"""
        X, y = simple_dataset
        model = LogisticRegression(learning_rate=0.1, n_iterations=500)
        model.fit(X, y)

        # 损失应该逐渐减小
        losses = model.losses
        assert losses[-1] < losses[0]

        # 损失应该是递减的（或至少平均趋势是递减的）
        first_half_mean = np.mean(losses[:100])
        second_half_mean = np.mean(losses[-100:])
        assert second_half_mean < first_half_mean

    def test_regularization(self, simple_dataset):
        """测试L2正则化"""
        X, y = simple_dataset

        # 无正则化
        model_no_reg = LogisticRegression(
            learning_rate=0.1,
            n_iterations=500,
            regularization=0.0
        )
        model_no_reg.fit(X, y)

        # 有正则化
        model_with_reg = LogisticRegression(
            learning_rate=0.1,
            n_iterations=500,
            regularization=1.0
        )
        model_with_reg.fit(X, y)

        # 正则化应该限制权重大小
        weight_norm_no_reg = np.linalg.norm(model_no_reg.weights)
        weight_norm_with_reg = np.linalg.norm(model_with_reg.weights)
        assert weight_norm_with_reg <= weight_norm_no_reg

    def test_threshold(self, simple_dataset):
        """测试分类阈值"""
        X, y = simple_dataset
        model = LogisticRegression(learning_rate=0.1, n_iterations=1000)
        model.fit(X, y)

        # 不同阈值应该产生不同预测
        model.threshold = 0.3
        pred_low = model.predict(X)

        model.threshold = 0.7
        pred_high = model.predict(X)

        # 低阈值应该预测更多正类
        assert np.sum(pred_low) >= np.sum(pred_high)

    def test_get_params(self):
        """测试参数获取"""
        model = LogisticRegression(learning_rate=0.05, n_iterations=500)
        params = model.get_params()

        assert params['learning_rate'] == 0.05
        assert params['n_iterations'] == 500
        assert params['weights'] is None  # 未训练时权重为None

    def test_repr(self):
        """测试字符串表示"""
        model = LogisticRegression(learning_rate=0.1, n_iterations=100)
        repr_str = repr(model)
        assert 'LogisticRegression' in repr_str
        assert '0.1' in repr_str


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
