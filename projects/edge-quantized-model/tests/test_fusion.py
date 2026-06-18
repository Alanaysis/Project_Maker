"""
算子融合测试

测试算子融合相关的功能
"""

import pytest
import numpy as np
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.operators.fusion import (
    fuse_conv_bn,
    fuse_conv_bn_relu,
    fuse_linear_relu,
    OperatorFusion,
)


class TestConvBNFusion:
    """Conv+BN 融合测试"""

    def test_basic_fusion(self):
        """测试基本融合"""
        # 创建测试数据
        out_channels = 16
        in_channels = 3
        kh, kw = 3, 3

        conv_weight = np.random.randn(out_channels, in_channels, kh, kw).astype(np.float32) * 0.1
        conv_bias = np.zeros(out_channels, dtype=np.float32)

        bn_mean = np.zeros(out_channels, dtype=np.float32)
        bn_var = np.ones(out_channels, dtype=np.float32)
        bn_weight = np.ones(out_channels, dtype=np.float32)
        bn_bias = np.zeros(out_channels, dtype=np.float32)

        # 执行融合
        fused_weight, fused_bias = fuse_conv_bn(
            conv_weight, conv_bias, bn_mean, bn_var, bn_weight, bn_bias
        )

        # 验证形状
        assert fused_weight.shape == conv_weight.shape
        assert fused_bias.shape == conv_bias.shape

    def test_fusion_with_real_params(self):
        """测试使用真实参数的融合"""
        out_channels = 16
        in_channels = 3
        kh, kw = 3, 3

        conv_weight = np.random.randn(out_channels, in_channels, kh, kw).astype(np.float32) * 0.1
        conv_bias = np.random.randn(out_channels).astype(np.float32) * 0.1

        bn_mean = np.random.randn(out_channels).astype(np.float32) * 0.1
        bn_var = np.abs(np.random.randn(out_channels).astype(np.float32)) + 0.1
        bn_weight = np.random.randn(out_channels).astype(np.float32) * 0.1
        bn_bias = np.random.randn(out_channels).astype(np.float32) * 0.1

        # 执行融合
        fused_weight, fused_bias = fuse_conv_bn(
            conv_weight, conv_bias, bn_mean, bn_var, bn_weight, bn_bias
        )

        # 验证融合结果
        scale = bn_weight / np.sqrt(bn_var + 1e-5)
        expected_weight = conv_weight * scale.reshape(-1, 1, 1, 1)
        expected_bias = (conv_bias - bn_mean) * scale + bn_bias

        np.testing.assert_allclose(fused_weight, expected_weight, rtol=1e-5)
        np.testing.assert_allclose(fused_bias, expected_bias, rtol=1e-5)

    def test_fusion_without_bias(self):
        """测试没有偏置的融合"""
        out_channels = 16
        in_channels = 3
        kh, kw = 3, 3

        conv_weight = np.random.randn(out_channels, in_channels, kh, kw).astype(np.float32) * 0.1
        conv_bias = None

        bn_mean = np.zeros(out_channels, dtype=np.float32)
        bn_var = np.ones(out_channels, dtype=np.float32)
        bn_weight = np.ones(out_channels, dtype=np.float32)
        bn_bias = np.zeros(out_channels, dtype=np.float32)

        # 执行融合
        fused_weight, fused_bias = fuse_conv_bn(
            conv_weight, conv_bias, bn_mean, bn_var, bn_weight, bn_bias
        )

        # 验证形状
        assert fused_weight.shape == conv_weight.shape
        assert fused_bias.shape == (out_channels,)


class TestConvBNReLUFusion:
    """Conv+BN+ReLU 融合测试"""

    def test_basic_fusion(self):
        """测试基本融合"""
        out_channels = 16
        in_channels = 3
        kh, kw = 3, 3

        conv_weight = np.random.randn(out_channels, in_channels, kh, kw).astype(np.float32) * 0.1
        conv_bias = np.zeros(out_channels, dtype=np.float32)

        bn_mean = np.zeros(out_channels, dtype=np.float32)
        bn_var = np.ones(out_channels, dtype=np.float32)
        bn_weight = np.ones(out_channels, dtype=np.float32)
        bn_bias = np.zeros(out_channels, dtype=np.float32)

        # 执行融合
        fused_weight, fused_bias, has_relu = fuse_conv_bn_relu(
            conv_weight, conv_bias, bn_mean, bn_var, bn_weight, bn_bias
        )

        # 验证
        assert fused_weight.shape == conv_weight.shape
        assert fused_bias.shape == conv_bias.shape
        assert has_relu == True


class TestLinearReLUFusion:
    """Linear+ReLU 融合测试"""

    def test_basic_fusion(self):
        """测试基本融合"""
        out_features = 10
        in_features = 100

        linear_weight = np.random.randn(out_features, in_features).astype(np.float32) * 0.1
        linear_bias = np.zeros(out_features, dtype=np.float32)

        # 执行融合
        fused_weight, fused_bias, has_relu = fuse_linear_relu(linear_weight, linear_bias)

        # 验证
        np.testing.assert_array_equal(fused_weight, linear_weight)
        np.testing.assert_array_equal(fused_bias, linear_bias)
        assert has_relu == True


class TestOperatorFusion:
    """算子融合器测试"""

    def test_fusion_stats(self):
        """测试融合统计"""
        fusion = OperatorFusion()
        stats = fusion.get_fusion_stats()

        assert isinstance(stats, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
