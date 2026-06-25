"""
损失函数测试。
"""

import pytest
import torch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.loss import KeypointMSELoss, KeypointOHKMLoss, CombinedPoseLoss


class TestKeypointMSELoss:
    """测试 MSE 损失。"""

    def test_identical_inputs(self):
        """测试相同输入的损失为零。"""
        criterion = KeypointMSELoss(use_target_weight=False)
        heatmaps = torch.rand(2, 17, 32, 32)
        loss_dict = criterion(heatmaps, heatmaps)
        assert loss_dict["loss"].item() < 1e-6

    def test_loss_positive(self):
        """测试损失为正数。"""
        criterion = KeypointMSELoss(use_target_weight=False)
        pred = torch.rand(2, 17, 32, 32)
        target = torch.rand(2, 17, 32, 32)
        loss_dict = criterion(pred, target)
        assert loss_dict["loss"].item() > 0

    def test_with_weights(self):
        """测试带权重的损失。"""
        criterion = KeypointMSELoss(use_target_weight=True)
        pred = torch.rand(4, 17, 32, 32)
        target = torch.rand(4, 17, 32, 32)
        weights = torch.ones(4, 17)
        # 部分关键点不可见
        weights[0, :5] = 0.0
        weights[1, 10:] = 0.0

        loss_dict = criterion(pred, target, weights)
        assert loss_dict["loss"].item() > 0

    def test_loss_weight(self):
        """测试损失权重系数。"""
        criterion1 = KeypointMSELoss(use_target_weight=False, loss_weight=1.0)
        criterion2 = KeypointMSELoss(use_target_weight=False, loss_weight=2.0)

        pred = torch.rand(2, 17, 32, 32)
        target = torch.rand(2, 17, 32, 32)

        loss1 = criterion1(pred, target)["loss"]
        loss2 = criterion2(pred, target)["loss"]

        assert abs(loss2.item() - 2 * loss1.item()) < 1e-4

    def test_gradient_flow(self):
        """测试梯度流。"""
        criterion = KeypointMSELoss(use_target_weight=False)
        pred = torch.rand(2, 17, 32, 32, requires_grad=True)
        target = torch.rand(2, 17, 32, 32)
        loss = criterion(pred, target)["loss"]
        loss.backward()
        assert pred.grad is not None

    def test_output_keys(self):
        """测试输出字典的键。"""
        criterion = KeypointMSELoss()
        pred = torch.rand(2, 17, 32, 32)
        target = torch.rand(2, 17, 32, 32)
        loss_dict = criterion(pred, target)
        assert "loss" in loss_dict
        assert "mse_loss" in loss_dict


class TestKeypointOHKMLoss:
    """测试 OHKM 损失。"""

    def test_output_shape(self):
        """测试输出。"""
        criterion = KeypointOHKMLoss(topk=8)
        pred = torch.rand(4, 17, 32, 32)
        target = torch.rand(4, 17, 32, 32)
        loss_dict = criterion(pred, target)
        assert loss_dict["loss"].dim() == 0  # 标量

    def test_topk_effect(self):
        """测试 Top-K 的效果。"""
        pred = torch.rand(4, 17, 32, 32)
        target = torch.rand(4, 17, 32, 32)

        criterion_small = KeypointOHKMLoss(topk=4)
        criterion_large = KeypointOHKMLoss(topk=12)

        loss_small = criterion_small(pred, target)["loss"]
        loss_large = criterion_large(pred, target)["loss"]

        # 两者都应该是正数
        assert loss_small.item() > 0
        assert loss_large.item() > 0

    def test_with_weights(self):
        """测试带权重。"""
        criterion = KeypointOHKMLoss(topk=8, use_target_weight=True)
        pred = torch.rand(2, 17, 32, 32)
        target = torch.rand(2, 17, 32, 32)
        weights = torch.ones(2, 17)
        weights[0, :5] = 0.0

        loss_dict = criterion(pred, target, weights)
        assert loss_dict["loss"].item() > 0


class TestCombinedPoseLoss:
    """测试组合损失。"""

    def test_output_keys(self):
        """测试输出字典的键。"""
        criterion = CombinedPoseLoss()
        pred = torch.rand(2, 17, 32, 32)
        target = torch.rand(2, 17, 32, 32)
        loss_dict = criterion(pred, target)
        assert "loss" in loss_dict
        assert "mse_loss" in loss_dict
        assert "ohkm_loss" in loss_dict

    def test_total_loss(self):
        """测试总损失是各分项之和。"""
        criterion = CombinedPoseLoss(mse_weight=1.0, ohkm_weight=0.5)
        pred = torch.rand(2, 17, 32, 32)
        target = torch.rand(2, 17, 32, 32)
        loss_dict = criterion(pred, target)

        # 总损失应该大于单独的 MSE 损失
        assert loss_dict["loss"].item() >= loss_dict["mse_loss"].item()

    def test_gradient_flow(self):
        """测试梯度流。"""
        criterion = CombinedPoseLoss()
        pred = torch.rand(2, 17, 32, 32, requires_grad=True)
        target = torch.rand(2, 17, 32, 32)
        loss = criterion(pred, target)["loss"]
        loss.backward()
        assert pred.grad is not None
