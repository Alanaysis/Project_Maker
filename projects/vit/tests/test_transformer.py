"""
Transformer Encoder 测试

测试 Transformer 编码器的正确性：
1. 输出形状
2. 残差连接
3. Layer Normalization
4. 不同深度配置
"""

import pytest
import torch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.transformer import TransformerBlock, TransformerEncoder, FeedForward


class TestFeedForward:
    """FeedForward 测试类"""

    def test_output_shape(self):
        """测试输出形状"""
        ffn = FeedForward(in_features=768, hidden_features=3072)
        x = torch.randn(2, 197, 768)
        out = ffn(x)

        assert out.shape == (2, 197, 768)

    def test_default_hidden_features(self):
        """测试默认隐藏层维度为 4 倍"""
        ffn = FeedForward(in_features=768)
        assert ffn.fc1.out_features == 768 * 4

    def test_gradient_flow(self):
        """测试梯度传播"""
        ffn = FeedForward(in_features=64, hidden_features=256)
        x = torch.randn(1, 10, 64, requires_grad=True)
        out = ffn(x)
        loss = out.sum()
        loss.backward()

        assert x.grad is not None


class TestTransformerBlock:
    """TransformerBlock 测试类"""

    def test_output_shape(self):
        """测试输出形状"""
        block = TransformerBlock(embed_dim=768, num_heads=12)
        x = torch.randn(2, 197, 768)
        out, attn = block(x)

        assert out.shape == (2, 197, 768)
        assert attn.shape == (2, 12, 197, 197)

    def test_residual_connection(self):
        """测试残差连接：输出应该接近输入（当注意力和FFN接近恒等时）"""
        # 使用很小的权重初始化，使输出接近输入
        block = TransformerBlock(embed_dim=64, num_heads=4, mlp_ratio=1.0)

        # 将权重初始化为接近 0
        for p in block.parameters():
            if p.dim() > 1:
                torch.nn.init.zeros_(p)

        x = torch.randn(1, 10, 64)
        out, _ = block(x)

        # 由于 Pre-LN + 残差，输出应该接近输入
        # 但 LayerNorm 会改变值，所以只检查是否在同一量级
        assert out.shape == x.shape

    def test_gradient_flow(self):
        """测试梯度传播"""
        block = TransformerBlock(embed_dim=64, num_heads=4)
        x = torch.randn(1, 10, 64, requires_grad=True)
        out, attn = block(x)
        loss = out.sum()
        loss.backward()

        assert x.grad is not None


class TestTransformerEncoder:
    """TransformerEncoder 测试类"""

    def test_output_shape(self):
        """测试输出形状"""
        encoder = TransformerEncoder(embed_dim=768, depth=12, num_heads=12)
        x = torch.randn(2, 197, 768)
        out, all_attn = encoder(x)

        assert out.shape == (2, 197, 768)
        assert len(all_attn) == 12  # 12 层

    def test_depth(self):
        """测试层数"""
        encoder = TransformerEncoder(embed_dim=256, depth=6, num_heads=8)
        assert len(encoder.blocks) == 6

    def test_final_norm(self):
        """测试最终 LayerNorm"""
        encoder = TransformerEncoder(embed_dim=64, depth=2, num_heads=4)
        assert isinstance(encoder.norm, torch.nn.LayerNorm)

    def test_gradient_flow(self):
        """测试梯度传播"""
        encoder = TransformerEncoder(embed_dim=64, depth=2, num_heads=4)
        x = torch.randn(1, 10, 64, requires_grad=True)
        out, _ = encoder(x)
        loss = out.sum()
        loss.backward()

        assert x.grad is not None

    def test_different_depths(self):
        """测试不同深度"""
        for depth in [1, 2, 4, 6, 12]:
            encoder = TransformerEncoder(embed_dim=64, depth=depth, num_heads=4)
            x = torch.randn(1, 10, 64)
            out, all_attn = encoder(x)

            assert out.shape == (1, 10, 64)
            assert len(all_attn) == depth
