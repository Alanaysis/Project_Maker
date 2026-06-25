"""损失函数测试

测试内容损失、风格损失和全变分损失。
"""

import pytest
import torch

from src.losses import ContentLoss, StyleLoss, TotalVariationLoss, StyleTransferLoss


class TestContentLoss:
    """内容损失测试"""

    def test_content_loss_zero(self):
        """测试相同特征的内容损失应该为 0"""
        loss_layer = ContentLoss(weight=1.0)
        features = torch.randn(1, 64, 32, 32)

        loss_layer.set_target(features)
        output = loss_layer(features)

        # 输出应该等于输入
        assert torch.allclose(output, features)
        # 损失应该接近 0
        assert torch.allclose(loss_layer.get_loss(), torch.tensor(0.0), atol=1e-6)

    def test_content_loss_positive(self):
        """测试不同特征的内容损失应该大于 0"""
        loss_layer = ContentLoss(weight=1.0)
        features1 = torch.randn(1, 64, 32, 32)
        features2 = torch.randn(1, 64, 32, 32)

        loss_layer.set_target(features1)
        loss_layer(features2)

        assert loss_layer.get_loss() > 0

    def test_content_loss_weight(self):
        """测试内容损失的权重"""
        features1 = torch.randn(1, 64, 32, 32)
        features2 = torch.randn(1, 64, 32, 32)

        loss1 = ContentLoss(weight=1.0)
        loss1.set_target(features1)
        loss1(features2)

        loss2 = ContentLoss(weight=2.0)
        loss2.set_target(features1)
        loss2(features2)

        # 权重加倍，损失应该加倍
        assert torch.allclose(loss2.get_loss(), loss1.get_loss() * 2.0, atol=1e-6)

    def test_content_loss_gradient(self):
        """测试内容损失的梯度传播"""
        loss_layer = ContentLoss(weight=1.0)
        target = torch.randn(1, 64, 32, 32)
        features = torch.randn(1, 64, 32, 32, requires_grad=True)

        loss_layer.set_target(target)
        output = loss_layer(features)
        loss = loss_layer.get_loss()
        loss.backward()

        assert features.grad is not None

    def test_content_loss_set_target_detaches(self):
        """测试 set_target 会分离梯度"""
        loss_layer = ContentLoss(weight=1.0)
        target = torch.randn(1, 64, 32, 32, requires_grad=True)

        loss_layer.set_target(target)

        # 目标应该被分离
        assert not loss_layer.target.requires_grad

    def test_content_loss_no_target_error(self):
        """测试未设置目标时的错误"""
        loss_layer = ContentLoss(weight=1.0)
        features = torch.randn(1, 64, 32, 32)

        with pytest.raises(ValueError, match="请先调用 set_target"):
            loss_layer(features)


class TestStyleLoss:
    """风格损失测试"""

    def test_style_loss_zero(self):
        """测试相同特征的风格损失应该接近 0"""
        loss_layer = StyleLoss(weight=1.0)
        features = torch.randn(1, 64, 32, 32)

        loss_layer.set_target(features)
        loss_layer(features)

        assert torch.allclose(loss_layer.get_loss(), torch.tensor(0.0), atol=1e-5)

    def test_style_loss_positive(self):
        """测试不同特征的风格损失应该大于 0"""
        loss_layer = StyleLoss(weight=1.0)
        features1 = torch.randn(1, 64, 32, 32)
        features2 = torch.randn(1, 64, 32, 32)

        loss_layer.set_target(features1)
        loss_layer(features2)

        assert loss_layer.get_loss() > 0

    def test_style_loss_weight(self):
        """测试风格损失的权重"""
        features1 = torch.randn(1, 64, 32, 32)
        features2 = torch.randn(1, 64, 32, 32)

        loss1 = StyleLoss(weight=1.0)
        loss1.set_target(features1)
        loss1(features2)

        loss2 = StyleLoss(weight=2.0)
        loss2.set_target(features1)
        loss2(features2)

        assert torch.allclose(loss2.get_loss(), loss1.get_loss() * 2.0, atol=1e-6)

    def test_style_loss_scale_covariance(self):
        """测试风格损失的缩放协变性"""
        loss_layer = StyleLoss(weight=1.0)
        features1 = torch.randn(1, 64, 32, 32)
        features2 = features1 * 2.0  # 缩放版本

        loss_layer.set_target(features1)
        loss_layer(features2)

        # Gram(kF) = k^2 * Gram(F)，所以缩放后损失不为 0
        assert loss_layer.get_loss() > 0

    def test_style_loss_gradient(self):
        """测试风格损失的梯度传播"""
        loss_layer = StyleLoss(weight=1.0)
        target = torch.randn(1, 64, 32, 32)
        features = torch.randn(1, 64, 32, 32, requires_grad=True)

        loss_layer.set_target(target)
        loss_layer(features)
        loss = loss_layer.get_loss()
        loss.backward()

        assert features.grad is not None

    def test_style_loss_no_target_error(self):
        """测试未设置目标时的错误"""
        loss_layer = StyleLoss(weight=1.0)
        features = torch.randn(1, 64, 32, 32)

        with pytest.raises(ValueError, match="请先调用 set_target"):
            loss_layer(features)


class TestTotalVariationLoss:
    """全变分损失测试"""

    def test_tv_loss_zero(self):
        """测试平滑图像的全变分损失应该接近 0"""
        loss_layer = TotalVariationLoss(weight=1.0)

        # 创建平滑图像（所有像素相同）
        image = torch.ones(1, 3, 32, 32)
        loss_layer(image)

        assert torch.allclose(loss_layer.get_loss(), torch.tensor(0.0), atol=1e-6)

    def test_tv_loss_positive(self):
        """测试噪声图像的全变分损失应该大于 0"""
        loss_layer = TotalVariationLoss(weight=1.0)

        # 创建噪声图像
        image = torch.randn(1, 3, 32, 32)
        loss_layer(image)

        assert loss_layer.get_loss() > 0

    def test_tv_loss_weight(self):
        """测试全变分损失的权重"""
        image = torch.randn(1, 3, 32, 32)

        loss1 = TotalVariationLoss(weight=1.0)
        loss1(image)

        loss2 = TotalVariationLoss(weight=2.0)
        loss2(image)

        assert torch.allclose(loss2.get_loss(), loss1.get_loss() * 2.0, atol=1e-6)

    def test_tv_loss_gradient(self):
        """测试全变分损失的梯度传播"""
        loss_layer = TotalVariationLoss(weight=1.0)
        image = torch.randn(1, 3, 32, 32, requires_grad=True)

        loss_layer(image)
        loss = loss_layer.get_loss()
        loss.backward()

        assert image.grad is not None

    def test_tv_loss_horizontal(self):
        """测试水平方向的全变分损失"""
        loss_layer = TotalVariationLoss(weight=1.0)

        # 创建只有水平变化的图像
        image = torch.zeros(1, 1, 4, 4)
        image[0, 0, :, 1] = 1.0  # 第二列设为 1

        loss_layer(image)

        # 应该有水平变化
        assert loss_layer.get_loss() > 0

    def test_tv_loss_vertical(self):
        """测试垂直方向的全变分损失"""
        loss_layer = TotalVariationLoss(weight=1.0)

        # 创建只有垂直变化的图像
        image = torch.zeros(1, 1, 4, 4)
        image[0, 0, 1, :] = 1.0  # 第二行设为 1

        loss_layer(image)

        # 应该有垂直变化
        assert loss_layer.get_loss() > 0


class TestStyleTransferLoss:
    """风格迁移总损失测试"""

    def test_add_content_loss(self):
        """测试添加内容损失"""
        loss_module = StyleTransferLoss()
        content_loss = loss_module.add_content_loss(weight=1.0)

        assert isinstance(content_loss, ContentLoss)
        assert len(loss_module.content_losses) == 1

    def test_add_style_loss(self):
        """测试添加风格损失"""
        loss_module = StyleTransferLoss()
        style_loss = loss_module.add_style_loss(weight=1.0)

        assert isinstance(style_loss, StyleLoss)
        assert len(loss_module.style_losses) == 1

    def test_get_total_loss(self):
        """测试计算总损失"""
        loss_module = StyleTransferLoss(
            content_weight=1.0,
            style_weight=1e6,
            tv_weight=1e-5,
        )

        # 添加内容损失
        content_loss = loss_module.add_content_loss()
        target = torch.randn(1, 64, 32, 32)
        content_loss.set_target(target)
        content_loss(torch.randn(1, 64, 32, 32))

        # 添加风格损失
        style_loss = loss_module.add_style_loss()
        style_loss.set_target(target)
        style_loss(torch.randn(1, 64, 32, 32))

        # 设置全变分损失
        loss_module.tv_loss(torch.randn(1, 3, 32, 32))

        # 计算总损失
        total_loss = loss_module.get_total_loss()

        assert total_loss > 0

    def test_get_loss_dict(self):
        """测试获取损失字典"""
        loss_module = StyleTransferLoss(
            content_weight=1.0,
            style_weight=1e6,
            tv_weight=1e-5,
        )

        # 添加损失
        content_loss = loss_module.add_content_loss()
        target = torch.randn(1, 64, 32, 32)
        content_loss.set_target(target)
        content_loss(torch.randn(1, 64, 32, 32))

        style_loss = loss_module.add_style_loss()
        style_loss.set_target(target)
        style_loss(torch.randn(1, 64, 32, 32))

        loss_module.tv_loss(torch.randn(1, 3, 32, 32))

        # 获取损失字典
        loss_dict = loss_module.get_loss_dict()

        assert "content_loss" in loss_dict
        assert "style_loss" in loss_dict
        assert "tv_loss" in loss_dict
        assert "total_loss" in loss_dict

        # 验证总损失等于各项之和
        expected_total = loss_dict["content_loss"] + loss_dict["style_loss"] + loss_dict["tv_loss"]
        assert abs(loss_dict["total_loss"] - expected_total) < 1e-6


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
