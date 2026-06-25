"""模型评估指标测试"""

import numpy as np
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.evaluation import mean_squared_error, root_mean_squared_error
from src.evaluation import mean_absolute_error, r2_score


class TestMSE:
    """MSE 测试"""

    def test_perfect_prediction(self):
        """测试完美预测"""
        y = np.array([1, 2, 3, 4, 5])
        assert mean_squared_error(y, y) == 0.0

    def test_known_value(self):
        """测试已知值"""
        y_true = np.array([1, 2, 3])
        y_pred = np.array([2, 3, 4])
        expected = np.mean([1, 1, 1])  # (1+1+1)/3 = 1.0
        assert abs(mean_squared_error(y_true, y_pred) - expected) < 1e-10


class TestRMSE:
    """RMSE 测试"""

    def test_perfect_prediction(self):
        """测试完美预测"""
        y = np.array([1, 2, 3])
        assert root_mean_squared_error(y, y) == 0.0

    def test_equals_sqrt_mse(self):
        """测试 RMSE = sqrt(MSE)"""
        y_true = np.array([1, 2, 3])
        y_pred = np.array([2, 3, 5])
        mse = mean_squared_error(y_true, y_pred)
        rmse = root_mean_squared_error(y_true, y_pred)
        assert abs(rmse - np.sqrt(mse)) < 1e-10


class TestMAE:
    """MAE 测试"""

    def test_perfect_prediction(self):
        """测试完美预测"""
        y = np.array([1, 2, 3])
        assert mean_absolute_error(y, y) == 0.0

    def test_known_value(self):
        """测试已知值"""
        y_true = np.array([1, 2, 3])
        y_pred = np.array([2, 3, 4])
        expected = 1.0  # |1|+|1|+|1| / 3 = 1.0
        assert abs(mean_absolute_error(y_true, y_pred) - expected) < 1e-10


class TestR2Score:
    """R2 分数测试"""

    def test_perfect_prediction(self):
        """测试完美预测"""
        y_true = np.array([1, 2, 3, 4, 5])
        y_pred = np.array([1, 2, 3, 4, 5])
        assert r2_score(y_true, y_pred) == 1.0

    def test_mean_prediction(self):
        """测试均值预测"""
        y_true = np.array([1, 2, 3, 4, 5])
        y_pred = np.array([3, 3, 3, 3, 3])
        assert abs(r2_score(y_true, y_pred)) < 1e-10

    def test_bad_prediction(self):
        """测试差的预测"""
        y_true = np.array([1, 2, 3, 4, 5])
        y_pred = np.array([5, 4, 3, 2, 1])
        assert r2_score(y_true, y_pred) < 0

    def test_good_prediction(self):
        """测试好的预测"""
        np.random.seed(42)
        y_true = np.array([1, 2, 3, 4, 5])
        y_pred = y_true + np.random.randn(5) * 0.1
        assert r2_score(y_true, y_pred) > 0.9

    def test_constant_true_values(self):
        """测试常数真实值（避免除以零）"""
        y_true = np.array([3, 3, 3, 3])
        y_pred = np.array([3, 3, 3, 3])
        assert r2_score(y_true, y_pred) == 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
