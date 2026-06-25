"""损失函数测试

测试 MSE、RMSE、MAE 损失函数。
"""

import numpy as np
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.losses import MSELoss, MAELoss, RMSELoss


class TestMSELoss:
    """MSE 损失函数测试"""

    def test_compute_basic(self):
        """测试基本的 MSE 计算"""
        y_true = np.array([1, 2, 3])
        y_pred = np.array([1, 2, 3])
        loss = MSELoss.compute(y_true, y_pred)
        assert loss == 0.0

    def test_compute_with_error(self):
        """测试有误差的 MSE 计算"""
        y_true = np.array([1, 2, 3])
        y_pred = np.array([1.1, 2.2, 2.8])
        loss = MSELoss.compute(y_true, y_pred)
        expected = np.mean((y_true - y_pred) ** 2)
        assert abs(loss - expected) < 1e-10

    def test_compute_shape_mismatch(self):
        """测试维度不匹配"""
        y_true = np.array([1, 2, 3])
        y_pred = np.array([1, 2])
        with pytest.raises(ValueError):
            MSELoss.compute(y_true, y_pred)

    def test_gradient_basic(self):
        """测试基本的梯度计算"""
        y_true = np.array([1, 2, 3])
        y_pred = np.array([1, 2, 3])
        grad = MSELoss.gradient(y_true, y_pred)
        expected = np.zeros(3)
        np.testing.assert_array_almost_equal(grad, expected)

    def test_gradient_with_error(self):
        """测试有误差的梯度计算"""
        y_true = np.array([1, 2, 3])
        y_pred = np.array([2, 3, 4])
        grad = MSELoss.gradient(y_true, y_pred)
        n = len(y_true)
        expected = (2.0 / n) * (y_pred - y_true)
        np.testing.assert_array_almost_equal(grad, expected)

    def test_compute_large_values(self):
        """测试大数值"""
        y_true = np.array([1000, 2000, 3000])
        y_pred = np.array([1001, 2002, 2998])
        loss = MSELoss.compute(y_true, y_pred)
        assert loss > 0

    def test_compute_negative_values(self):
        """测试负值"""
        y_true = np.array([-1, -2, -3])
        y_pred = np.array([-1.1, -2.2, -2.8])
        loss = MSELoss.compute(y_true, y_pred)
        assert loss > 0


class TestRMSELoss:
    """RMSE 损失函数测试"""

    def test_compute_basic(self):
        """测试基本的 RMSE 计算"""
        y_true = np.array([1, 2, 3])
        y_pred = np.array([1, 2, 3])
        loss = RMSELoss.compute(y_true, y_pred)
        assert loss == 0.0

    def test_compute_with_error(self):
        """测试有误差的 RMSE 计算"""
        y_true = np.array([1, 2, 3])
        y_pred = np.array([1.1, 2.2, 2.8])
        loss = RMSELoss.compute(y_true, y_pred)
        expected = np.sqrt(np.mean((y_true - y_pred) ** 2))
        assert abs(loss - expected) < 1e-10

    def test_rmse_equals_sqrt_mse(self):
        """测试 RMSE = sqrt(MSE)"""
        y_true = np.array([1, 2, 3, 4, 5])
        y_pred = np.array([1.1, 2.2, 2.8, 4.1, 5.2])

        mse = MSELoss.compute(y_true, y_pred)
        rmse = RMSELoss.compute(y_true, y_pred)

        assert abs(rmse - np.sqrt(mse)) < 1e-10

    def test_gradient_zero_prediction(self):
        """测试完美预测时的梯度"""
        y_true = np.array([1, 2, 3])
        y_pred = np.array([1, 2, 3])
        grad = RMSELoss.gradient(y_true, y_pred)
        # 完美预测时 RMSE=0，梯度应为零（避免除以零）
        np.testing.assert_array_almost_equal(grad, np.zeros(3))


class TestMAELoss:
    """MAE 损失函数测试"""

    def test_compute_basic(self):
        """测试基本的 MAE 计算"""
        y_true = np.array([1, 2, 3])
        y_pred = np.array([1, 2, 3])
        loss = MAELoss.compute(y_true, y_pred)
        assert loss == 0.0

    def test_compute_with_error(self):
        """测试有误差的 MAE 计算"""
        y_true = np.array([1, 2, 3])
        y_pred = np.array([1.1, 2.2, 2.8])
        loss = MAELoss.compute(y_true, y_pred)
        expected = np.mean(np.abs(y_true - y_pred))
        assert abs(loss - expected) < 1e-10

    def test_gradient_basic(self):
        """测试基本的梯度计算"""
        y_true = np.array([1, 2, 3])
        y_pred = np.array([2, 3, 4])
        grad = MAELoss.gradient(y_true, y_pred)
        n = len(y_true)
        expected = np.sign(y_pred - y_true) / n
        np.testing.assert_array_almost_equal(grad, expected)

    def test_mae_robust_to_outliers(self):
        """测试 MAE 对异常值的鲁棒性"""
        y_true = np.array([1, 2, 3, 4, 5])
        y_pred_normal = np.array([1.1, 2.1, 3.1, 4.1, 5.1])
        y_pred_outlier = np.array([1.1, 2.1, 3.1, 4.1, 100.0])

        mae_normal = MAELoss.compute(y_true, y_pred_normal)
        mae_outlier = MAELoss.compute(y_true, y_pred_outlier)

        mse_normal = MSELoss.compute(y_true, y_pred_normal)
        mse_outlier = MSELoss.compute(y_true, y_pred_outlier)

        # MAE 受异常值影响小于 MSE
        mae_ratio = mae_outlier / mae_normal
        mse_ratio = mse_outlier / mse_normal
        assert mae_ratio < mse_ratio


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
