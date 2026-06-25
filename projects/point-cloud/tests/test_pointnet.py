"""
PointNet 模型测试
"""

import pytest
import torch

from src.pointnet import (
    TNet,
    SharedMLP,
    GlobalFeatureExtractor,
    PointNetClassifier,
    PointNetSegmentor,
    pointnet_loss,
)


class TestTNet:
    """TNet 测试"""

    def test_output_shape(self):
        """测试输出形状"""
        batch_size = 4
        k = 3
        num_points = 1024

        tnet = TNet(k=k)
        x = torch.randn(batch_size, k, num_points)
        output = tnet(x)

        assert output.shape == (batch_size, k, k)

    def test_different_k(self):
        """测试不同的 k 值"""
        batch_size = 4
        num_points = 512

        for k in [3, 64]:
            tnet = TNet(k=k)
            x = torch.randn(batch_size, k, num_points)
            output = tnet(x)
            assert output.shape == (batch_size, k, k)

    def test_identity_initialization(self):
        """测试初始化接近单位矩阵"""
        tnet = TNet(k=3)
        # 检查最后一层的偏置初始化为 0
        assert tnet.fc3.bias is not None


class TestSharedMLP:
    """SharedMLP 测试"""

    def test_output_shape(self):
        """测试输出形状"""
        batch_size = 4
        in_channels = 3
        out_channels = 64
        num_points = 1024

        mlp = SharedMLP(in_channels, out_channels)
        x = torch.randn(batch_size, in_channels, num_points)
        output = mlp(x)

        assert output.shape == (batch_size, out_channels, num_points)

    def test_without_batchnorm(self):
        """测试不使用 BatchNorm"""
        mlp = SharedMLP(3, 64, use_bn=False)
        x = torch.randn(4, 3, 512)
        output = mlp(x)
        assert output.shape == (4, 64, 512)


class TestGlobalFeatureExtractor:
    """全局特征提取器测试"""

    def test_output_shapes(self):
        """测试输出形状"""
        batch_size = 4
        num_points = 1024

        extractor = GlobalFeatureExtractor(use_tnet=True)
        x = torch.randn(batch_size, 3, num_points)

        global_feat, local_feat, trans_input, trans_feat = extractor(x)

        assert global_feat.shape == (batch_size, 1024)
        assert local_feat.shape == (batch_size, 64, num_points)
        assert trans_input.shape == (batch_size, 3, 3)
        assert trans_feat.shape == (batch_size, 64, 64)

    def test_without_tnet(self):
        """测试不使用 TNet"""
        extractor = GlobalFeatureExtractor(use_tnet=False)
        x = torch.randn(4, 3, 512)

        global_feat, local_feat, trans_input, trans_feat = extractor(x)

        assert global_feat.shape == (4, 1024)
        assert local_feat.shape == (4, 64, 512)
        assert trans_input is None
        assert trans_feat is None


class TestPointNetClassifier:
    """PointNet 分类器测试"""

    def test_output_shape(self):
        """测试输出形状"""
        batch_size = 4
        num_points = 1024
        num_classes = 10

        model = PointNetClassifier(num_classes=num_classes)
        x = torch.randn(batch_size, 3, num_points)

        logits, trans_input, trans_feat = model(x)

        assert logits.shape == (batch_size, num_classes)

    def test_different_num_classes(self):
        """测试不同的类别数"""
        for num_classes in [2, 5, 10, 40]:
            model = PointNetClassifier(num_classes=num_classes)
            x = torch.randn(2, 3, 256)
            logits, _, _ = model(x)
            assert logits.shape == (2, num_classes)

    def test_parameter_count(self):
        """测试参数数量"""
        model = PointNetClassifier(num_classes=10)
        param_count = sum(p.numel() for p in model.parameters())
        # PointNet 应该有大约 3-4M 参数
        assert param_count > 1_000_000
        assert param_count < 10_000_000


class TestPointNetSegmentor:
    """PointNet 分割器测试"""

    def test_output_shape(self):
        """测试输出形状"""
        batch_size = 4
        num_points = 1024
        num_classes = 10

        model = PointNetSegmentor(num_classes=num_classes)
        x = torch.randn(batch_size, 3, num_points)

        logits, trans_input, trans_feat = model(x)

        assert logits.shape == (batch_size, num_points, num_classes)

    def test_different_num_classes(self):
        """测试不同的类别数"""
        for num_classes in [2, 5, 10]:
            model = PointNetSegmentor(num_classes=num_classes)
            x = torch.randn(2, 3, 256)
            logits, _, _ = model(x)
            assert logits.shape == (2, 256, num_classes)


class TestPointNetLoss:
    """PointNet 损失函数测试"""

    def test_classification_loss(self):
        """测试分类损失"""
        batch_size = 4
        num_classes = 10

        logits = torch.randn(batch_size, num_classes)
        targets = torch.randint(0, num_classes, (batch_size,))

        loss = pointnet_loss(logits, targets)
        assert loss.dim() == 0  # 标量
        assert loss.item() > 0

    def test_with_regularization(self):
        """测试带正则化的损失"""
        batch_size = 4
        num_classes = 10

        logits = torch.randn(batch_size, num_classes)
        targets = torch.randint(0, num_classes, (batch_size,))
        trans_feat = torch.randn(batch_size, 64, 64)

        loss = pointnet_loss(logits, targets, trans_feat, alpha=0.001)
        assert loss.dim() == 0

    def test_segmentation_loss(self):
        """测试分割损失"""
        batch_size = 2
        num_points = 64
        num_classes = 4

        logits = torch.randn(batch_size * num_points, num_classes)
        targets = torch.randint(0, num_classes, (batch_size * num_points,))

        loss = pointnet_loss(logits, targets)
        assert loss.item() > 0


class TestGradientFlow:
    """梯度流测试"""

    def test_classifier_gradients(self):
        """测试分类器梯度流"""
        model = PointNetClassifier(num_classes=10)
        x = torch.randn(2, 3, 256)
        targets = torch.randint(0, 10, (2,))

        logits, _, trans_feat = model(x)
        loss = pointnet_loss(logits, targets, trans_feat)
        loss.backward()

        # 检查所有参数都有梯度
        for name, param in model.named_parameters():
            if param.requires_grad:
                assert param.grad is not None, f"{name} 没有梯度"

    def test_segmentor_gradients(self):
        """测试分割器梯度流"""
        model = PointNetSegmentor(num_classes=4)
        x = torch.randn(2, 3, 64)
        targets = torch.randint(0, 4, (2, 64))

        logits, _, trans_feat = model(x)
        logits_flat = logits.reshape(-1, 4)
        targets_flat = targets.reshape(-1)
        loss = pointnet_loss(logits_flat, targets_flat, trans_feat)
        loss.backward()

        for name, param in model.named_parameters():
            if param.requires_grad:
                assert param.grad is not None, f"{name} 没有梯度"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
