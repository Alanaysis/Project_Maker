"""
Multi-Head Self-Attention 测试

测试注意力机制的正确性：
1. 输出形状
2. 注意力权重
3. 多头机制
4. 梯度传播
"""

import pytest
import torch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.attention import MultiHeadSelfAttention, Attention


class TestMultiHeadSelfAttention:
    """MultiHeadSelfAttention 测试类"""

    def test_output_shape(self):
        """测试输出形状"""
        model = MultiHeadSelfAttention(embed_dim=768, num_heads=12)
        x = torch.randn(2, 197, 768)  # (batch, seq_len, embed_dim)
        out, attn = model(x)

        assert out.shape == (2, 197, 768)
        assert attn.shape == (2, 12, 197, 197)  # (B, H, N, N)

    def test_output_shape_different_heads(self):
        """测试不同头数的输出形状"""
        for num_heads in [1, 3, 6, 12]:
            model = MultiHeadSelfAttention(embed_dim=768, num_heads=num_heads)
            x = torch.randn(1, 50, 768)
            out, attn = model(x)

            assert out.shape == (1, 50, 768)
            assert attn.shape == (1, num_heads, 50, 50)

    def test_attention_weights_sum_to_one(self):
        """测试注意力权重之和为 1（softmax 归一化）"""
        model = MultiHeadSelfAttention(embed_dim=64, num_heads=4)
        x = torch.randn(1, 10, 64)
        _, attn = model(x)

        # 每行的注意力权重之和应该为 1
        row_sums = attn.sum(dim=-1)
        assert torch.allclose(row_sums, torch.ones_like(row_sums), atol=1e-5)

    def test_attention_weights_non_negative(self):
        """测试注意力权重非负"""
        model = MultiHeadSelfAttention(embed_dim=64, num_heads=4)
        x = torch.randn(1, 10, 64)
        _, attn = model(x)

        assert (attn >= 0).all()

    def test_gradient_flow(self):
        """测试梯度传播"""
        model = MultiHeadSelfAttention(embed_dim=64, num_heads=4)
        x = torch.randn(1, 10, 64, requires_grad=True)
        out, attn = model(x)
        loss = out.sum()
        loss.backward()

        assert x.grad is not None
        for name, param in model.named_parameters():
            assert param.grad is not None, f"Parameter {name} has no gradient"

    def test_head_dimension(self):
        """测试每个头的维度"""
        model = MultiHeadSelfAttention(embed_dim=768, num_heads=12)
        assert model.head_dim == 64  # 768 / 12

    def test_scale_factor(self):
        """测试缩放因子"""
        model = MultiHeadSelfAttention(embed_dim=768, num_heads=12)
        expected_scale = (768 // 12) ** -0.5  # 1/sqrt(64)
        assert abs(model.scale - expected_scale) < 1e-6

    def test_embed_dim_divisible_by_heads(self):
        """测试嵌入维度必须能被头数整除"""
        with pytest.raises(AssertionError):
            MultiHeadSelfAttention(embed_dim=768, num_heads=7)  # 768 / 7 不是整数

    def test_batch_independence(self):
        """测试批次中的样本独立"""
        model = MultiHeadSelfAttention(embed_dim=64, num_heads=4)
        x = torch.randn(2, 10, 64)
        out, attn = model(x)

        assert not torch.allclose(out[0], out[1])


class TestAttention:
    """简化版 Attention 测试类"""

    def test_output_shape(self):
        """测试输出形状"""
        model = Attention(dim=64)
        x = torch.randn(2, 10, 64)
        out = model(x)

        assert out.shape == (2, 10, 64)

    def test_gradient_flow(self):
        """测试梯度传播"""
        model = Attention(dim=64)
        x = torch.randn(1, 10, 64, requires_grad=True)
        out = model(x)
        loss = out.sum()
        loss.backward()

        assert x.grad is not None
