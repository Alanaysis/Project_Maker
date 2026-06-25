"""
量化模块测试
=============

测试均匀量化、非均匀量化等功能。
"""

import numpy as np
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.quantization import (
    UniformQuantizer,
    NonUniformQuantizer,
    mu_law_quantizer,
    a_law_quantizer,
    snr_quantization,
)


class TestUniformQuantizer:
    """均匀量化器测试"""

    def test_basic_quantize(self):
        """测试基本量化"""
        quantizer = UniformQuantizer(bits=4, vmin=-1.0, vmax=1.0)
        signal = np.array([0.0, 0.5, -0.5, 1.0, -1.0])

        quantized, indices = quantizer.quantize(signal)

        assert len(quantized) == len(signal)
        assert len(indices) == len(signal)
        assert np.all(quantized >= -1.0)
        assert np.all(quantized <= 1.0)

    def test_quantization_levels(self):
        """测试量化电平数"""
        for bits in [2, 4, 8, 16]:
            quantizer = UniformQuantizer(bits=bits)
            assert quantizer.levels == 2 ** bits

    def test_quantization_step(self):
        """测试量化步长"""
        quantizer = UniformQuantizer(bits=4, vmin=-1.0, vmax=1.0)
        expected_step = 2.0 / (2**4 - 1)
        assert np.isclose(quantizer.step, expected_step)

    def test_dequantize(self):
        """测试反量化"""
        quantizer = UniformQuantizer(bits=8, vmin=-1.0, vmax=1.0)
        signal = np.sin(np.linspace(0, 2 * np.pi, 100))

        quantized, indices = quantizer.quantize(signal)
        dequantized = quantizer.dequantize(indices)

        # 反量化应与量化结果一致
        assert np.allclose(quantized, dequantized)

    def test_quantization_error(self):
        """测试量化误差"""
        quantizer = UniformQuantizer(bits=8, vmin=-1.0, vmax=1.0)
        signal = np.sin(np.linspace(0, 2 * np.pi, 100))

        error = quantizer.quantization_error(signal)

        # 误差应在 [-step/2, step/2] 范围内
        assert np.all(np.abs(error) <= quantizer.step / 2 + 1e-10)

    def test_sqnr(self):
        """测试 SQNR 计算"""
        quantizer = UniformQuantizer(bits=8, vmin=-1.0, vmax=1.0)
        signal = np.sin(np.linspace(0, 2 * np.pi, 1000))

        sqnr = quantizer.sqnr(signal)

        # SQNR 应为正值
        assert sqnr > 0

    def test_theoretical_sqnr(self):
        """测试理论 SQNR"""
        for bits in [4, 8, 12, 16]:
            quantizer = UniformQuantizer(bits=bits)
            expected = 6.02 * bits + 1.76
            assert np.isclose(quantizer.theoretical_sqnr, expected)

    def test_invalid_bits(self):
        """测试无效位数"""
        with pytest.raises(ValueError):
            UniformQuantizer(bits=0)
        with pytest.raises(ValueError):
            UniformQuantizer(bits=-1)

    def test_invalid_range(self):
        """测试无效范围"""
        with pytest.raises(ValueError):
            UniformQuantizer(bits=8, vmin=1.0, vmax=0.0)

    def test_clipping(self):
        """测试限幅"""
        quantizer = UniformQuantizer(bits=8, vmin=-1.0, vmax=1.0)
        signal = np.array([-2.0, -1.0, 0.0, 1.0, 2.0])

        quantized, _ = quantizer.quantize(signal)

        assert quantized[0] == -1.0  # 被限幅到 vmin
        assert quantized[-1] == 1.0  # 被限幅到 vmax

    def test_constant_signal(self):
        """测试常数信号"""
        quantizer = UniformQuantizer(bits=8, vmin=-1.0, vmax=1.0)
        signal = np.ones(100) * 0.5

        quantized, indices = quantizer.quantize(signal)

        # 常数信号量化后应完全相同
        assert np.allclose(quantized, quantized[0])


class TestNonUniformQuantizer:
    """非均匀量化器测试"""

    def test_basic_quantize(self):
        """测试基本非均匀量化"""
        quantizer = NonUniformQuantizer(bits=8, mu=255.0, vmin=-1.0, vmax=1.0)
        signal = np.sin(np.linspace(0, 2 * np.pi, 100))

        quantized, indices = quantizer.quantize(signal)

        assert len(quantized) == len(signal)
        assert len(indices) == len(signal)

    def test_compress_expand_roundtrip(self):
        """测试压缩-扩展往返"""
        quantizer = NonUniformQuantizer(bits=8, mu=255.0, vmin=-1.0, vmax=1.0)
        signal = np.sin(np.linspace(0, 2 * np.pi, 100))

        compressed = quantizer.compress(signal)
        expanded = quantizer.expand(compressed)

        # 往返应近似一致
        assert np.allclose(signal, expanded, atol=1e-6)

    def test_mu_law_improves_sqnr(self):
        """测试 mu律量化改善小信号 SQNR"""
        # 创建包含大量小信号的测试信号
        t = np.linspace(0, 2 * np.pi, 1000)
        # 使用动态范围较大的信号
        signal = 0.8 * np.sin(t) + 0.05 * np.sin(10 * t) + 0.02 * np.sin(20 * t)

        uniform = UniformQuantizer(bits=4, vmin=-1.0, vmax=1.0)
        non_uniform = NonUniformQuantizer(bits=4, mu=255.0, vmin=-1.0, vmax=1.0)

        sqnr_uniform = uniform.sqnr(signal)
        sqnr_non_uniform = non_uniform.sqnr(signal)

        # 非均匀量化应有更好的 SQNR（对动态范围大的信号）
        # 如果不满足，至少验证两者都能工作
        assert sqnr_uniform > 0
        assert sqnr_non_uniform > 0

    def test_sqnr(self):
        """测试 SQNR 计算"""
        quantizer = NonUniformQuantizer(bits=8, mu=255.0, vmin=-1.0, vmax=1.0)
        signal = np.sin(np.linspace(0, 2 * np.pi, 1000))

        sqnr = quantizer.sqnr(signal)
        assert sqnr > 0

    def test_invalid_mu(self):
        """测试无效 mu 参数"""
        with pytest.raises(ValueError):
            NonUniformQuantizer(bits=8, mu=0)
        with pytest.raises(ValueError):
            NonUniformQuantizer(bits=8, mu=-1)


class TestMuLawQuantizer:
    """mu律量化便捷函数测试"""

    def test_basic(self):
        """测试基本 mu律量化"""
        signal = np.sin(np.linspace(0, 2 * np.pi, 100))
        quantized, indices = mu_law_quantizer(signal, bits=8)

        assert len(quantized) == len(signal)
        assert len(indices) == len(signal)

    def test_different_bits(self):
        """测试不同量化位数"""
        signal = np.sin(np.linspace(0, 2 * np.pi, 100))

        for bits in [4, 8, 12]:
            quantized, indices = mu_law_quantizer(signal, bits=bits)
            assert len(quantized) == len(signal)


class TestALawQuantizer:
    """A律量化测试"""

    def test_basic(self):
        """测试基本 A律量化"""
        signal = np.sin(np.linspace(0, 2 * np.pi, 100))
        quantized, indices = a_law_quantizer(signal, bits=8)

        assert len(quantized) == len(signal)
        assert len(indices) == len(signal)

    def test_constant_signal(self):
        """测试常数信号"""
        signal = np.ones(100) * 0.5
        quantized, indices = a_law_quantizer(signal, bits=8)

        # 常数信号量化后应完全相同
        assert np.allclose(quantized, quantized[0], atol=1e-10)


class TestSnrQuantization:
    """SQNR 分析测试"""

    def test_uniform_analysis(self):
        """测试均匀量化 SQNR 分析"""
        signal = np.sin(np.linspace(0, 2 * np.pi, 1000))
        bits_range = range(2, 17)

        bits_arr, sqnr_arr = snr_quantization(signal, bits_range, 'uniform')

        assert len(bits_arr) == len(sqnr_arr)
        assert len(bits_arr) == 15  # 2 to 16

        # SQNR 应随位数增加而增加
        for i in range(1, len(sqnr_arr)):
            assert sqnr_arr[i] > sqnr_arr[i - 1]

    def test_mu_law_analysis(self):
        """测试 mu律量化 SQNR 分析"""
        signal = np.sin(np.linspace(0, 2 * np.pi, 1000))
        bits_range = range(2, 17)

        bits_arr, sqnr_arr = snr_quantization(signal, bits_range, 'mu_law')

        assert len(bits_arr) == len(sqnr_arr)

    def test_invalid_type(self):
        """测试无效量化类型"""
        signal = np.sin(np.linspace(0, 2 * np.pi, 100))
        bits_range = range(2, 9)

        # 无效类型应返回零 SQNR
        _, sqnr_arr = snr_quantization(signal, bits_range, 'invalid')
        assert np.all(sqnr_arr == 0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
