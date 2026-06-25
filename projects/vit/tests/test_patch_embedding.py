"""
Patch Embedding 测试

测试 Patch Embedding 层的正确性：
1. 输出形状
2. CLS token 的添加
3. 位置编码
4. 不同参数组合
"""

import pytest
import torch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.patch_embedding import PatchEmbedding


class TestPatchEmbedding:
    """PatchEmbedding 测试类"""

    def test_output_shape_default(self):
        """测试默认参数的输出形状"""
        # 默认：224x224 图像，16x16 patch，768 维嵌入
        # num_patches = (224/16)^2 = 196
        # 输出形状：(B, 196+1, 768) = (B, 197, 768)
        model = PatchEmbedding(img_size=224, patch_size=16, embed_dim=768)
        x = torch.randn(2, 3, 224, 224)
        out = model(x)

        assert out.shape == (2, 197, 768)

    def test_output_shape_small(self):
        """测试小图像的输出形状"""
        # 28x28 图像，7x7 patch -> 4x4 = 16 个 patches
        # 输出形状：(B, 16+1, 128) = (B, 17, 128)
        model = PatchEmbedding(img_size=28, patch_size=7, in_channels=1, embed_dim=128)
        x = torch.randn(4, 1, 28, 28)
        out = model(x)

        assert out.shape == (4, 17, 128)

    def test_num_patches(self):
        """测试 patch 数量计算"""
        # 32x32 图像，4x4 patch -> 64 个 patches
        model = PatchEmbedding(img_size=32, patch_size=4, embed_dim=256)
        assert model.num_patches == 64

    def test_cls_token_in_output(self):
        """测试 CLS token 是否正确添加"""
        model = PatchEmbedding(img_size=8, patch_size=4, embed_dim=32)
        x = torch.randn(1, 3, 8, 8)
        out = model(x)

        # 输出的第一个位置应该是 CLS token + 位置编码
        # 验证 CLS token 存在
        assert out.shape[1] == model.num_patches + 1

    def test_position_embedding_shape(self):
        """测试位置编码形状"""
        model = PatchEmbedding(img_size=16, patch_size=4, embed_dim=64)
        # num_patches = 16, +1 for CLS
        assert model.position_embedding.shape == (1, 17, 64)

    def test_cls_token_shape(self):
        """测试 CLS token 形状"""
        model = PatchEmbedding(img_size=16, patch_size=4, embed_dim=64)
        assert model.cls_token.shape == (1, 1, 64)

    def test_batch_independence(self):
        """测试批次中的样本是否独立"""
        model = PatchEmbedding(img_size=8, patch_size=4, embed_dim=32)
        x = torch.randn(2, 3, 8, 8)
        out = model(x)

        # 两个样本的输出应该不同（因为输入不同）
        assert not torch.allclose(out[0], out[1])

    def test_gradient_flow(self):
        """测试梯度是否能正确传播"""
        model = PatchEmbedding(img_size=8, patch_size=4, embed_dim=32)
        x = torch.randn(1, 3, 8, 8)
        out = model(x)
        loss = out.sum()
        loss.backward()

        # 所有参数都应该有梯度
        for name, param in model.named_parameters():
            assert param.grad is not None, f"Parameter {name} has no gradient"

    def test_invalid_image_size(self):
        """测试图像尺寸不能被 patch_size 整除的情况"""
        with pytest.raises(AssertionError):
            PatchEmbedding(img_size=7, patch_size=4, embed_dim=32)

    def test_single_channel(self):
        """测试单通道图像（灰度图）"""
        # 28x28 图像，7x7 patch -> 4x4 = 16 个 patches + 1 CLS = 17
        model = PatchEmbedding(img_size=28, patch_size=7, in_channels=1, embed_dim=64)
        x = torch.randn(1, 1, 28, 28)
        out = model(x)

        assert out.shape == (1, 17, 64)

    def test_different_patch_sizes(self):
        """测试不同的 patch 大小"""
        for patch_size in [4, 8, 16]:
            img_size = 32
            model = PatchEmbedding(
                img_size=img_size, patch_size=patch_size, embed_dim=64
            )
            x = torch.randn(1, 3, img_size, img_size)
            out = model(x)

            expected_patches = (img_size // patch_size) ** 2
            assert out.shape == (1, expected_patches + 1, 64)

    def test_projection_is_conv2d(self):
        """测试投影层是否为 Conv2d"""
        model = PatchEmbedding(img_size=16, patch_size=4, embed_dim=64)
        assert isinstance(model.projection, torch.nn.Conv2d)
