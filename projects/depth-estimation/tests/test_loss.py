"""
深度估计损失函数测试
"""

import pytest
import torch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.loss import (
    DepthMSELoss,
    DepthMAELoss,
    SILogLoss,
    GradientLoss,
    CombinedDepthLoss,
    BerHuLoss,
)


class TestDepthMSELoss:
    """MSE 损失测试"""

    def test_basic(self):
        """测试基本功能"""
        criterion = DepthMSELoss()
        pred = torch.ones(2, 1, 8, 8)
        target = torch.zeros(2, 1, 8, 8)
        loss = criterion(pred, target)
        assert loss.item() == pytest.approx(1.0)

    def test_zero_loss(self):
        """测试相同输入"""
        criterion = DepthMSELoss()
        x = torch.rand(2, 1, 8, 8)
        loss = criterion(x, x)
        assert loss.item() == pytest.approx(0.0)

    def test_with_mask(self):
        """测试带掩码"""
        criterion = DepthMSELoss()
        pred = torch.ones(2, 1, 8, 8)
        target = torch.zeros(2, 1, 8, 8)
        mask = torch.zeros(2, 1, 8, 8)
        mask[:, :, :4, :] = 1  # 只有前半部分有效
        loss = criterion(pred, target, mask)
        assert loss.item() == pytest.approx(1.0)

    def test_normalize(self):
        """测试归一化"""
        criterion = DepthMSELoss(normalize=True)
        pred = torch.tensor([[[[1.0, 2.0], [3.0, 4.0]]]])
        target = torch.tensor([[[[1.0, 2.0], [3.0, 4.0]]]])
        loss = criterion(pred, target)
        assert loss.item() == pytest.approx(0.0)


class TestDepthMAELoss:
    """MAE 损失测试"""

    def test_basic(self):
        """测试基本功能"""
        criterion = DepthMAELoss()
        pred = torch.ones(2, 1, 8, 8) * 2
        target = torch.ones(2, 1, 8, 8)
        loss = criterion(pred, target)
        assert loss.item() == pytest.approx(1.0)

    def test_zero_loss(self):
        """测试相同输入"""
        criterion = DepthMAELoss()
        x = torch.rand(2, 1, 8, 8)
        loss = criterion(x, x)
        assert loss.item() == pytest.approx(0.0, abs=1e-6)


class TestSILogLoss:
    """SILog 损失测试"""

    def test_basic(self):
        """测试基本功能"""
        criterion = SILogLoss()
        pred = torch.rand(2, 1, 8, 8) * 10 + 0.1
        target = torch.rand(2, 1, 8, 8) * 10 + 0.1
        loss = criterion(pred, target)
        assert loss.item() > 0

    def test_scale_invariance(self):
        """测试尺度不变性"""
        criterion = SILogLoss(lambda_weight=0.0)
        pred = torch.rand(1, 1, 8, 8) * 10 + 1
        target = pred * 2  # 缩放
        loss = criterion(pred, target)
        # 纯尺度差异时损失应该很小
        assert loss.item() < 1.0


class TestGradientLoss:
    """梯度损失测试"""

    def test_basic(self):
        """测试基本功能"""
        criterion = GradientLoss()
        pred = torch.rand(2, 1, 8, 8)
        target = torch.rand(2, 1, 8, 8)
        loss = criterion(pred, target)
        assert loss.item() >= 0

    def test_same_gradient(self):
        """测试相同梯度"""
        criterion = GradientLoss()
        # 创建具有相同梯度的深度图
        x = torch.linspace(0, 1, 8).unsqueeze(0).unsqueeze(0).unsqueeze(3)
        pred = x.expand(1, 1, 8, 8)
        target = x.expand(1, 1, 8, 8) * 2  # 缩放但保持梯度
        loss = criterion(pred, target)
        # 梯度方向相同，损失应该相对较小
        assert loss.item() < 0.5


class TestCombinedDepthLoss:
    """组合损失测试"""

    def test_basic(self):
        """测试基本功能"""
        criterion = CombinedDepthLoss()
        pred = torch.rand(2, 1, 8, 8) * 10 + 0.1
        target = torch.rand(2, 1, 8, 8) * 10 + 0.1
        loss_dict = criterion(pred, target)

        assert "total" in loss_dict
        assert "mse" in loss_dict
        assert "mae" in loss_dict
        assert "silog" in loss_dict
        assert "gradient" in loss_dict
        assert loss_dict["total"].item() > 0

    def test_loss_weights(self):
        """测试损失权重"""
        criterion = CombinedDepthLoss(mse_weight=0, mae_weight=0, silog_weight=0, gradient_weight=1)
        pred = torch.rand(2, 1, 8, 8) + 0.1
        target = torch.rand(2, 1, 8, 8) + 0.1
        loss_dict = criterion(pred, target)

        # 只有梯度损失
        assert loss_dict["total"].item() == pytest.approx(loss_dict["gradient"].item(), rel=1e-5)


class TestBerHuLoss:
    """BerHu 损失测试"""

    def test_basic(self):
        """测试基本功能"""
        criterion = BerHuLoss()
        pred = torch.rand(2, 1, 8, 8)
        target = torch.rand(2, 1, 8, 8)
        loss = criterion(pred, target)
        assert loss.item() >= 0

    def test_small_error(self):
        """测试小误差 (L1 区域)"""
        criterion = BerHuLoss()
        pred = torch.ones(2, 1, 8, 8) * 0.5
        target = torch.ones(2, 1, 8, 8) * 0.5001
        loss = criterion(pred, target)
        # 小误差应该接近 L1
        assert loss.item() < 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
