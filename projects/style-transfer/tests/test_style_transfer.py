"""风格迁移测试

测试风格迁移的核心功能。
"""

import pytest
import torch
import tempfile
from pathlib import Path

from src.style_transfer import StyleTransfer
from src.utils import create_noise_image, get_device


class TestStyleTransfer:
    """风格迁移类测试"""

    @pytest.fixture
    def style_transfer(self):
        """创建风格迁移实例"""
        return StyleTransfer(
            content_layers=["conv4_2"],
            style_layers=["conv1_1", "conv2_1", "conv3_1"],
            content_weight=1.0,
            style_weight=1e6,
            tv_weight=1e-5,
            device="cpu",
        )

    @pytest.fixture
    def content_image(self):
        """创建内容图像"""
        return torch.randn(1, 3, 64, 64)

    @pytest.fixture
    def style_image(self):
        """创建风格图像"""
        return torch.randn(1, 3, 64, 64)

    def test_style_transfer_init(self, style_transfer):
        """测试风格迁移初始化"""
        assert style_transfer.content_layers == ["conv4_2"]
        assert style_transfer.style_layers == ["conv1_1", "conv2_1", "conv3_1"]
        assert style_transfer.content_weight == 1.0
        assert style_transfer.style_weight == 1e6
        assert style_transfer.tv_weight == 1e-5

    def test_style_transfer_model_build(self, style_transfer):
        """测试模型构建"""
        assert style_transfer.model is not None
        assert len(style_transfer.content_losses) > 0
        assert len(style_transfer.style_losses) > 0

    def test_style_transfer_set_targets(self, style_transfer, content_image, style_image):
        """测试设置目标特征"""
        style_transfer._set_targets(content_image, style_image)

        # 检查目标是否被设置
        for loss in style_transfer.content_losses:
            assert loss.target is not None

        for loss in style_transfer.style_losses:
            assert loss.target_gram is not None

    def test_style_transfer_forward(self, style_transfer, content_image, style_image):
        """测试前向传播"""
        style_transfer._set_targets(content_image, style_image)

        # 前向传播
        output = style_transfer.model(content_image)

        # 输出应该存在
        assert output is not None
        assert output.shape[0] == 1

    def test_style_transfer_content_init(self, style_transfer, content_image, style_image):
        """测试内容初始化方法"""
        output = style_transfer.transfer(
            content_image=content_image,
            style_image=style_image,
            num_steps=5,
            init_method="content",
        )

        assert output.shape == content_image.shape

    def test_style_transfer_noise_init(self, style_transfer, content_image, style_image):
        """测试噪声初始化方法"""
        output = style_transfer.transfer(
            content_image=content_image,
            style_image=style_image,
            num_steps=5,
            init_method="noise",
            noise_ratio=0.6,
        )

        assert output.shape == content_image.shape

    def test_style_transfer_random_init(self, style_transfer, content_image, style_image):
        """测试随机初始化方法"""
        output = style_transfer.transfer(
            content_image=content_image,
            style_image=style_image,
            num_steps=5,
            init_method="random",
        )

        assert output.shape == content_image.shape

    def test_style_transfer_callback(self, style_transfer, content_image, style_image):
        """测试回调函数"""
        callback_calls = []

        def callback(step, loss_dict):
            callback_calls.append((step, loss_dict))

        style_transfer.transfer(
            content_image=content_image,
            style_image=style_image,
            num_steps=20,
            callback=callback,
        )

        # 应该有回调调用
        assert len(callback_calls) > 0

        # 检查回调参数
        for step, loss_dict in callback_calls:
            assert isinstance(step, int)
            assert "total_loss" in loss_dict
            assert "content_loss" in loss_dict
            assert "style_loss" in loss_dict
            assert "tv_loss" in loss_dict

    def test_style_transfer_lbfgs_optimizer(self, style_transfer, content_image, style_image):
        """测试 L-BFGS 优化器"""
        output = style_transfer.transfer(
            content_image=content_image,
            style_image=style_image,
            num_steps=5,
            optimizer_type="lbfgs",
        )

        assert output is not None

    def test_style_transfer_adam_optimizer(self, style_transfer, content_image, style_image):
        """测试 Adam 优化器"""
        output = style_transfer.transfer(
            content_image=content_image,
            style_image=style_image,
            num_steps=5,
            optimizer_type="adam",
            learning_rate=0.01,
        )

        assert output is not None

    def test_style_transfer_invalid_optimizer(self, style_transfer, content_image, style_image):
        """测试无效优化器"""
        with pytest.raises(ValueError, match="未知的优化器类型"):
            style_transfer.transfer(
                content_image=content_image,
                style_image=style_image,
                num_steps=5,
                optimizer_type="invalid",
            )

    def test_style_transfer_invalid_init(self, style_transfer, content_image, style_image):
        """测试无效初始化方法"""
        with pytest.raises(ValueError, match="未知的初始化方法"):
            style_transfer.transfer(
                content_image=content_image,
                style_image=style_image,
                num_steps=5,
                init_method="invalid",
            )

    def test_style_transfer_get_loss_summary(self, style_transfer, content_image, style_image):
        """测试获取损失摘要"""
        style_transfer.transfer(
            content_image=content_image,
            style_image=style_image,
            num_steps=5,
        )

        loss_dict = style_transfer.get_loss_summary()

        assert "content_loss" in loss_dict
        assert "style_loss" in loss_dict
        assert "tv_loss" in loss_dict


class TestCreateNoiseImage:
    """噪声图像创建测试"""

    def test_noise_ratio_zero(self):
        """测试噪声比例为 0"""
        content = torch.randn(1, 3, 32, 32)
        noise_image = create_noise_image(content, noise_ratio=0.0)

        # 应该完全等于内容图像
        assert torch.allclose(noise_image, content)

    def test_noise_ratio_one(self):
        """测试噪声比例为 1"""
        content = torch.randn(1, 3, 32, 32)
        noise_image = create_noise_image(content, noise_ratio=1.0)

        # 应该不等于内容图像
        assert not torch.allclose(noise_image, content)

    def test_noise_ratio_half(self):
        """测试噪声比例为 0.5"""
        content = torch.randn(1, 3, 32, 32)
        noise_image = create_noise_image(content, noise_ratio=0.5)

        # 应该在内容和噪声之间
        assert noise_image.shape == content.shape


class TestGetDevice:
    """设备获取测试"""

    def test_cpu_device(self):
        """测试 CPU 设备"""
        device = get_device("cpu")
        assert device == torch.device("cpu")

    def test_auto_device(self):
        """测试自动设备选择"""
        device = get_device("auto")
        assert device in [torch.device("cpu"), torch.device("cuda"), torch.device("mps")]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
