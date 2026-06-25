"""
位置编码测试
============

测试 PositionalEncoding 模块的功能。
"""

import pytest
import torch
import numpy as np
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.positional_encoding import PositionalEncoding


class TestPositionalEncoding:
    """位置编码测试类"""

    def test_output_shape(self):
        """测试输出形状是否正确"""
        # 3D 位置编码，10 个频率
        pe = PositionalEncoding(input_dim=3, num_freqs=10, include_input=True)
        # 输出维度 = 3 + 10 * 2 * 3 = 63
        assert pe.output_dim == 63

        # 测试不同输入形状
        x = torch.randn(10, 3)
        encoded = pe(x)
        assert encoded.shape == (10, 63)

        x = torch.randn(5, 10, 3)
        encoded = pe(x)
        assert encoded.shape == (5, 10, 63)

    def test_output_shape_without_input(self):
        """测试不包含原始输入时的输出形状"""
        pe = PositionalEncoding(input_dim=3, num_freqs=10, include_input=False)
        assert pe.output_dim == 60  # 10 * 2 * 3

        x = torch.randn(10, 3)
        encoded = pe(x)
        assert encoded.shape == (10, 60)

    def test_direction_encoding(self):
        """测试方向编码（2D 输入）"""
        pe = PositionalEncoding(input_dim=2, num_freqs=6, include_input=True)
        # 输出维度 = 2 + 6 * 2 * 2 = 26
        assert pe.output_dim == 26

        directions = torch.randn(10, 2)
        encoded = pe(directions)
        assert encoded.shape == (10, 26)

    def test_encoding_values(self):
        """测试编码值是否正确"""
        pe = PositionalEncoding(input_dim=1, num_freqs=3, include_input=False)

        # 单点输入
        x = torch.tensor([[0.5]])
        encoded = pe(x)

        # 验证 sin 和 cos 值
        expected_sin = torch.sin(torch.tensor([1.0, 2.0, 4.0]) * np.pi * 0.5)
        expected_cos = torch.cos(torch.tensor([1.0, 2.0, 4.0]) * np.pi * 0.5)

        assert encoded.shape == (1, 6)
        # 检查 sin 值
        assert torch.allclose(encoded[0, 0::2], expected_sin, atol=1e-6)
        # 检查 cos 值
        assert torch.allclose(encoded[0, 1::2], expected_cos, atol=1e-6)

    def test_include_input_flag(self):
        """测试 include_input 标志"""
        # 包含原始输入
        pe_with = PositionalEncoding(input_dim=3, num_freqs=5, include_input=True)
        assert pe_with.output_dim == 3 + 5 * 2 * 3

        # 不包含原始输入
        pe_without = PositionalEncoding(input_dim=3, num_freqs=5, include_input=False)
        assert pe_without.output_dim == 5 * 2 * 3

        # 验证前 3 维是否为原始输入
        x = torch.randn(10, 3)
        encoded = pe_with(x)
        assert torch.allclose(encoded[:, :3], x, atol=1e-6)

    def test_log_sampling(self):
        """测试对数采样频率"""
        pe = PositionalEncoding(input_dim=3, num_freqs=4, log_sampling=True)

        # 验证频率是 2 的幂
        expected_freqs = torch.tensor([1.0, 2.0, 4.0, 8.0])
        assert torch.allclose(pe.freq_bands, expected_freqs, atol=1e-6)

    def test_linear_sampling(self):
        """测试线性采样频率"""
        pe = PositionalEncoding(input_dim=3, num_freqs=4, log_sampling=False)

        # 验证频率是线性间隔
        expected_freqs = torch.tensor([1.0, 3.0 / 3 * 2 + 1, 2.0 + 2.0, 8.0])
        assert len(pe.freq_bands) == 4
        assert pe.freq_bands[0] == 1.0
        assert pe.freq_bands[-1] == 8.0

    def test_batch_independence(self):
        """测试批次独立性"""
        pe = PositionalEncoding(input_dim=3, num_freqs=10)

        # 不同批次应该独立编码
        x = torch.randn(5, 3)
        encoded = pe(x)

        # 单独编码应该得到相同结果
        for i in range(5):
            single_encoded = pe(x[i:i+1])
            assert torch.allclose(encoded[i:i+1], single_encoded, atol=1e-6)

    def test_gradient_flow(self):
        """测试梯度流"""
        pe = PositionalEncoding(input_dim=3, num_freqs=10)
        x = torch.randn(10, 3, requires_grad=True)

        encoded = pe(x)
        loss = encoded.sum()
        loss.backward()

        assert x.grad is not None
        assert x.grad.shape == x.shape

    def test_device_compatibility(self):
        """测试设备兼容性"""
        if torch.cuda.is_available():
            pe = PositionalEncoding(input_dim=3, num_freqs=10).cuda()
            x = torch.randn(10, 3).cuda()
            encoded = pe(x)
            assert encoded.is_cuda

    def test_different_num_freqs(self):
        """测试不同频率层数"""
        for num_freqs in [1, 5, 10, 20]:
            pe = PositionalEncoding(input_dim=3, num_freqs=num_freqs, include_input=True)
            expected_dim = 3 + num_freqs * 2 * 3
            assert pe.output_dim == expected_dim

            x = torch.randn(10, 3)
            encoded = pe(x)
            assert encoded.shape == (10, expected_dim)


class TestPositionalEncodingEdgeCases:
    """边界情况测试"""

    def test_zero_input(self):
        """测试零输入"""
        pe = PositionalEncoding(input_dim=3, num_freqs=10)
        x = torch.zeros(5, 3)
        encoded = pe(x)

        # sin(0) = 0, cos(0) = 1
        # 前 3 维是原始输入 (0)
        assert torch.allclose(encoded[:, :3], torch.zeros(5, 3), atol=1e-6)

    def test_one_input(self):
        """测试单位输入"""
        pe = PositionalEncoding(input_dim=3, num_freqs=3, include_input=False)
        x = torch.ones(1, 3)
        encoded = pe(x)

        # 验证编码后的值
        assert not torch.isnan(encoded).any()
        assert not torch.isinf(encoded).any()

    def test_large_input(self):
        """测试大输入值"""
        pe = PositionalEncoding(input_dim=3, num_freqs=10)
        x = torch.randn(5, 3) * 100  # 大值
        encoded = pe(x)

        # 不应该有 NaN 或 Inf
        assert not torch.isnan(encoded).any()
        assert not torch.isinf(encoded).any()

    def test_negative_input(self):
        """测试负输入"""
        pe = PositionalEncoding(input_dim=3, num_freqs=10)
        x = -torch.ones(5, 3)
        encoded = pe(x)

        # sin(-x) = -sin(x), cos(-x) = cos(x)
        assert not torch.isnan(encoded).any()
        assert not torch.isinf(encoded).any()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
