"""Gram 矩阵测试

测试 Gram 矩阵计算的正确性。
"""

import pytest
import torch

from src.gram_matrix import gram_matrix, GramMatrix, gram_loss


class TestGramMatrix:
    """Gram 矩阵函数测试"""

    def test_gram_matrix_shape(self):
        """测试 Gram 矩阵的输出形状"""
        batch_size = 2
        channels = 64
        height = 32
        width = 32

        features = torch.randn(batch_size, channels, height, width)
        gram = gram_matrix(features)

        assert gram.shape == (batch_size, channels, channels)

    def test_gram_matrix_single_batch(self):
        """测试单 batch 的 Gram 矩阵"""
        features = torch.randn(1, 16, 8, 8)
        gram = gram_matrix(features)

        assert gram.shape == (1, 16, 16)

    def test_gram_matrix_symmetric(self):
        """测试 Gram 矩阵的对称性"""
        features = torch.randn(1, 32, 16, 16)
        gram = gram_matrix(features)

        # Gram 矩阵应该是对称的
        assert torch.allclose(gram, gram.transpose(1, 2), atol=1e-6)

    def test_gram_matrix_positive_semidefinite(self):
        """测试 Gram 矩阵是半正定的"""
        features = torch.randn(1, 16, 8, 8)
        gram = gram_matrix(features)

        # 计算特征值
        eigenvalues = torch.linalg.eigvalsh(gram)

        # 所有特征值应该非负
        assert torch.all(eigenvalues >= -1e-6)

    def test_gram_matrix_normalize(self):
        """测试 Gram 矩阵归一化"""
        features = torch.randn(1, 16, 8, 8)

        gram_normalized = gram_matrix(features, normalize=True)
        gram_unnormalized = gram_matrix(features, normalize=False)

        # 归一化后的应该更小
        num_elements = 8 * 8
        assert torch.allclose(gram_normalized * num_elements, gram_unnormalized, atol=1e-6)

    def test_gram_matrix_identity_features(self):
        """测试单位特征的 Gram 矩阵"""
        # 创建单位特征：每个通道只有一个非零元素
        channels = 4
        features = torch.zeros(1, channels, 1, channels)
        for i in range(channels):
            features[0, i, 0, i] = 1.0

        gram = gram_matrix(features, normalize=False)

        # 应该是单位矩阵
        expected = torch.eye(channels).unsqueeze(0)
        assert torch.allclose(gram, expected, atol=1e-6)

    def test_gram_matrix_zero_features(self):
        """测试零特征的 Gram 矩阵"""
        features = torch.zeros(1, 16, 8, 8)
        gram = gram_matrix(features)

        # 应该是零矩阵
        assert torch.allclose(gram, torch.zeros_like(gram))

    def test_gram_matrix_different_sizes(self):
        """测试不同大小的特征图"""
        for height, width in [(4, 4), (8, 16), (16, 8), (32, 32)]:
            features = torch.randn(1, 16, height, width)
            gram = gram_matrix(features)

            assert gram.shape == (1, 16, 16)

    def test_gram_matrix_gradient(self):
        """测试 Gram 矩阵的梯度计算"""
        features = torch.randn(1, 16, 8, 8, requires_grad=True)
        gram = gram_matrix(features)
        loss = gram.sum()
        loss.backward()

        assert features.grad is not None
        assert features.grad.shape == features.shape


class TestGramMatrixModule:
    """Gram 矩阵模块测试"""

    def test_module_forward(self):
        """测试模块前向传播"""
        module = GramMatrix(normalize=True)
        features = torch.randn(1, 32, 16, 16)

        gram = module(features)

        assert gram.shape == (1, 32, 32)

    def test_module_normalize_flag(self):
        """测试模块的归一化标志"""
        module_normalized = GramMatrix(normalize=True)
        module_unnormalized = GramMatrix(normalize=False)

        features = torch.randn(1, 16, 8, 8)

        gram1 = module_normalized(features)
        gram2 = module_unnormalized(features)

        # 归一化的应该更小
        assert gram1.abs().mean() < gram2.abs().mean()

    def test_module_parameters(self):
        """测试模块没有可训练参数"""
        module = GramMatrix()
        params = list(module.parameters())

        assert len(params) == 0


class TestGramLoss:
    """Gram 矩阵损失测试"""

    def test_gram_loss_same_features(self):
        """测试相同特征的损失应该是 0"""
        features = torch.randn(1, 16, 8, 8)
        loss = gram_loss(features, features)

        assert torch.allclose(loss, torch.tensor(0.0), atol=1e-6)

    def test_gram_loss_different_features(self):
        """测试不同特征的损失应该大于 0"""
        features1 = torch.randn(1, 16, 8, 8)
        features2 = torch.randn(1, 16, 8, 8)
        loss = gram_loss(features1, features2)

        assert loss > 0

    def test_gram_loss_symmetry(self):
        """测试损失的对称性"""
        features1 = torch.randn(1, 16, 8, 8)
        features2 = torch.randn(1, 16, 8, 8)

        loss1 = gram_loss(features1, features2)
        loss2 = gram_loss(features2, features1)

        assert torch.allclose(loss1, loss2, atol=1e-6)

    def test_gram_loss_scale_covariance(self):
        """测试损失的缩放协变性（归一化后）"""
        features1 = torch.randn(1, 16, 8, 8)
        features2 = features1 * 2.0

        # 归一化后的 Gram 矩阵：Gram(kF) = k^2 * Gram(F)
        # 所以缩放后损失不为 0，而是 (k^2 - 1)^2 * loss
        loss_original = gram_loss(features1, features1)
        loss_scaled = gram_loss(features1, features2)

        # 相同特征损失应为 0
        assert torch.allclose(loss_original, torch.tensor(0.0), atol=1e-6)
        # 缩放后损失应大于 0（因为 Gram(kF) = k^2 * Gram(F)）
        assert loss_scaled > 0

    def test_gram_loss_gradient(self):
        """测试损失的梯度计算"""
        features1 = torch.randn(1, 16, 8, 8, requires_grad=True)
        features2 = torch.randn(1, 16, 8, 8)

        loss = gram_loss(features1, features2)
        loss.backward()

        assert features1.grad is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
