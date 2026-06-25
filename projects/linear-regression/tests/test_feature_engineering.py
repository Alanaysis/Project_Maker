"""特征工程测试"""

import numpy as np
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.feature_engineering import (
    StandardScaler,
    MinMaxScaler,
    PolynomialFeatures,
    FeatureSelector,
    cross_validation,
)
from src.model import LinearRegression


class TestStandardScaler:
    """标准化缩放器测试"""

    def test_fit_transform(self):
        """测试拟合转换"""
        X = np.array([[1, 2], [3, 4], [5, 6]], dtype=float)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # 标准化后均值应接近 0
        np.testing.assert_array_almost_equal(np.mean(X_scaled, axis=0), np.zeros(2), decimal=10)

    def test_standard_deviation(self):
        """测试标准差为 1"""
        X = np.random.randn(100, 3)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        stds = np.std(X_scaled, axis=0)
        np.testing.assert_array_almost_equal(stds, np.ones(3), decimal=10)

    def test_inverse_transform(self):
        """测试逆转换"""
        X = np.array([[1, 10], [2, 20], [3, 30]], dtype=float)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        X_restored = scaler.inverse_transform(X_scaled)

        np.testing.assert_array_almost_equal(X, X_restored, decimal=10)

    def test_1d_input(self):
        """测试 1D 输入"""
        X = np.array([1, 2, 3, 4, 5], dtype=float)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        assert X_scaled.shape == (5, 1)

    def test_constant_feature(self):
        """测试常数特征"""
        X = np.array([[1, 5], [1, 10], [1, 15]], dtype=float)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # 常数特征标准化后应为 0
        np.testing.assert_array_almost_equal(X_scaled[:, 0], np.zeros(3))


class TestMinMaxScaler:
    """归一化缩放器测试"""

    def test_fit_transform(self):
        """测试拟合转换"""
        X = np.array([[1, 10], [2, 20], [3, 30]], dtype=float)
        scaler = MinMaxScaler()
        X_scaled = scaler.fit_transform(X)

        # 归一化后应在 [0, 1] 范围内
        assert X_scaled.min() >= -1e-10
        assert X_scaled.max() <= 1 + 1e-10

    def test_min_max_values(self):
        """测试最小最大值"""
        X = np.array([[1, 10], [2, 20], [3, 30]], dtype=float)
        scaler = MinMaxScaler()
        X_scaled = scaler.fit_transform(X)

        # 最小值应为 0，最大值应为 1
        np.testing.assert_array_almost_equal(X_scaled.min(axis=0), np.zeros(2))
        np.testing.assert_array_almost_equal(X_scaled.max(axis=0), np.ones(2))

    def test_inverse_transform(self):
        """测试逆转换"""
        X = np.array([[1, 10], [2, 20], [3, 30]], dtype=float)
        scaler = MinMaxScaler()
        X_scaled = scaler.fit_transform(X)
        X_restored = scaler.inverse_transform(X_scaled)

        np.testing.assert_array_almost_equal(X, X_restored, decimal=10)

    def test_custom_range(self):
        """测试自定义范围"""
        X = np.array([[1], [2], [3]], dtype=float)
        scaler = MinMaxScaler(feature_range=(-1, 1))
        X_scaled = scaler.fit_transform(X)

        assert X_scaled.min() >= -1 - 1e-10
        assert X_scaled.max() <= 1 + 1e-10


class TestPolynomialFeatures:
    """多项式特征测试"""

    def test_degree_2(self):
        """测试 2 阶多项式"""
        X = np.array([[2], [3]], dtype=float)
        poly = PolynomialFeatures(degree=2)
        X_poly = poly.fit_transform(X)

        # 对于单特征 x，应该生成 [x, x^2]
        assert X_poly.shape == (2, 2)
        np.testing.assert_array_almost_equal(X_poly[:, 0], [2, 3])
        np.testing.assert_array_almost_equal(X_poly[:, 1], [4, 9])

    def test_two_features_degree_2(self):
        """测试双特征 2 阶多项式"""
        X = np.array([[1, 2], [3, 4]], dtype=float)
        poly = PolynomialFeatures(degree=2)
        X_poly = poly.fit_transform(X)

        # 应该有: x0, x1, x0^2, x1^2, x0*x1 = 5 个特征
        assert X_poly.shape[1] == 5

    def test_include_bias(self):
        """测试包含偏置项"""
        X = np.array([[2], [3]], dtype=float)
        poly = PolynomialFeatures(degree=2, include_bias=True)
        X_poly = poly.fit_transform(X)

        # 应该有: 1, x, x^2 = 3 个特征
        assert X_poly.shape[1] == 3
        np.testing.assert_array_almost_equal(X_poly[:, 0], [1, 1])

    def test_feature_names(self):
        """测试特征名称"""
        poly = PolynomialFeatures(degree=2)
        names = poly.get_feature_names(2)
        assert "x0" in names
        assert "x1" in names
        assert "x0^2" in names
        assert "x0*x1" in names


class TestFeatureSelector:
    """特征选择器测试"""

    def test_variance_threshold(self):
        """测试方差阈值选择"""
        X = np.array([
            [1, 5, 10],
            [2, 5, 20],
            [3, 5, 30],
            [4, 5, 40],
        ], dtype=float)

        X_selected, indices = FeatureSelector.variance_threshold(X, threshold=0.5)

        # 第 2 列方差为 0，应被移除
        assert len(indices) == 2
        assert 1 not in indices

    def test_correlation_selection(self):
        """测试相关性选择"""
        np.random.seed(42)
        X = np.random.randn(100, 5)
        y = X[:, 0] * 3 + X[:, 1] * 2 + np.random.randn(100) * 0.1

        X_selected, indices = FeatureSelector.correlation_selection(X, y, top_k=2)

        # 应该选择与 y 最相关的 2 个特征
        assert len(indices) == 2
        assert 0 in indices  # x0 与 y 高度相关
        assert 1 in indices  # x1 与 y 高度相关

    def test_correlation_threshold(self):
        """测试相关性阈值选择"""
        np.random.seed(42)
        X = np.random.randn(100, 5)
        y = X[:, 0] * 3 + np.random.randn(100) * 0.1

        X_selected, indices = FeatureSelector.correlation_selection(X, y, threshold=0.5)

        # 只有 x0 的相关性超过 0.5
        assert 0 in indices

    def test_rfe_ranking(self):
        """测试 RFE 排名"""
        np.random.seed(42)
        X = np.random.randn(100, 5)
        true_w = np.array([5.0, -3.0, 0.1, 0.05, 0.02])
        y = X @ true_w + np.random.randn(100) * 0.1

        ranking, selected = FeatureSelector.rfe_ranking(X, y, n_features_to_select=2)

        # 最重要的 2 个特征应该是 x0 和 x1
        assert 0 in selected
        assert 1 in selected


class TestCrossValidation:
    """交叉验证测试"""

    def test_basic_cv(self):
        """测试基本交叉验证"""
        np.random.seed(42)
        X = np.random.randn(100, 3)
        y = X @ np.array([1.0, 2.0, 3.0]) + 1.0

        result = cross_validation(
            X, y,
            model_class=LinearRegression,
            model_params={"learning_rate": 0.01, "n_iterations": 500},
            n_folds=5,
            metric="mse",
        )

        assert len(result["scores"]) == 5
        assert result["mean"] > 0
        assert result["std"] >= 0

    def test_cv_different_metrics(self):
        """测试不同评估指标"""
        np.random.seed(42)
        X = np.random.randn(100, 2)
        y = X @ np.array([1.0, -1.0]) + 0.5

        for metric in ["mse", "rmse", "mae", "r2"]:
            result = cross_validation(
                X, y,
                model_class=LinearRegression,
                model_params={"learning_rate": 0.01, "n_iterations": 500},
                n_folds=3,
                metric=metric,
            )
            assert len(result["scores"]) == 3

    def test_cv_result_keys(self):
        """测试返回结果的键"""
        np.random.seed(42)
        X = np.random.randn(50, 2)
        y = X @ np.array([1.0, -1.0])

        result = cross_validation(
            X, y,
            model_class=LinearRegression,
            model_params={"learning_rate": 0.01, "n_iterations": 500},
            n_folds=3,
        )

        assert "scores" in result
        assert "mean" in result
        assert "std" in result
        assert "min" in result
        assert "max" in result


class TestOptimizers:
    """优化器测试"""

    def test_learning_rate_scheduler_constant(self):
        """测试恒定学习率调度"""
        from src.optimizers import LearningRateScheduler

        scheduler = LearningRateScheduler(initial_lr=0.1, strategy="constant")
        assert scheduler.get_lr(0) == 0.1
        assert scheduler.get_lr(100) == 0.1

    def test_learning_rate_scheduler_step_decay(self):
        """测试阶梯衰减"""
        from src.optimizers import LearningRateScheduler

        scheduler = LearningRateScheduler(
            initial_lr=0.1, strategy="step_decay", decay_rate=0.5, decay_steps=100
        )
        assert scheduler.get_lr(0) == 0.1
        assert abs(scheduler.get_lr(100) - 0.05) < 1e-10
        assert abs(scheduler.get_lr(200) - 0.025) < 1e-10

    def test_learning_rate_scheduler_exponential(self):
        """测试指数衰减"""
        from src.optimizers import LearningRateScheduler

        scheduler = LearningRateScheduler(
            initial_lr=0.1, strategy="exponential_decay", decay_rate=0.5, decay_steps=100
        )
        lr_0 = scheduler.get_lr(0)
        lr_100 = scheduler.get_lr(100)
        assert lr_0 == 0.1
        assert abs(lr_100 - 0.05) < 1e-10

    def test_learning_rate_scheduler_cosine(self):
        """测试余弦退火"""
        from src.optimizers import LearningRateScheduler

        scheduler = LearningRateScheduler(
            initial_lr=0.1, strategy="cosine_annealing", min_lr=0.001
        )
        lr_0 = scheduler.get_lr(0, total_steps=100)
        lr_mid = scheduler.get_lr(50, total_steps=100)
        lr_end = scheduler.get_lr(100, total_steps=100)

        assert lr_0 > lr_mid
        assert lr_mid > lr_end
        assert abs(lr_end - 0.001) < 1e-10

    def test_learning_rate_scheduler_min_lr(self):
        """测试最小学习率"""
        from src.optimizers import LearningRateScheduler

        scheduler = LearningRateScheduler(
            initial_lr=0.1, strategy="step_decay", decay_rate=0.5,
            decay_steps=10, min_lr=0.01
        )
        # 经过很多步后不应低于 min_lr
        lr = scheduler.get_lr(1000)
        assert lr >= 0.01

    def test_batch_gradient_descent(self):
        """测试批量梯度下降"""
        from src.optimizers import BatchGradientDescent

        bgd = BatchGradientDescent(learning_rate=0.01)
        X = np.array([[1, 2], [3, 4]])
        y = np.array([5, 11])
        y_pred = np.array([4.5, 10.5])
        weights = np.array([1.0, 2.0])

        dw, db = bgd.compute_gradients(X, y, y_pred, weights, 0.0)
        new_w, new_b = bgd.update(weights, 0.0, dw, db)

        assert new_w.shape == (2,)
        assert isinstance(new_b, float)

    def test_minibatch_gradient_descent(self):
        """测试小批量梯度下降"""
        from src.optimizers import MiniBatchGradientDescent

        mbgd = MiniBatchGradientDescent(learning_rate=0.01, batch_size=2)
        X = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
        y = np.array([5, 11, 17, 23])

        batches = mbgd.get_batches(X, y)
        assert len(batches) == 2
        assert batches[0][0].shape[0] == 2

    def test_repr(self):
        """测试字符串表示"""
        from src.optimizers import LearningRateScheduler

        scheduler = LearningRateScheduler(initial_lr=0.1, strategy="constant")
        repr_str = repr(scheduler)
        assert "LearningRateScheduler" in repr_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
