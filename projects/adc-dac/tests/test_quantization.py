"""
量化模块测试
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import pytest

from src.quantization import (
    uniform_quantize,
    non_uniform_quantize_a_law,
    non_uniform_quantize_mu_law,
    quantization_noise_analysis,
    calculate_quantization_snr,
    adaptive_quantization,
)


class TestUniformQuantization:
    """测试均匀量化"""

    def test_quantize_basic(self):
        """基本量化测试"""
        signal = np.array([-0.5, 0, 0.5, 1.0])
        result = uniform_quantize(signal, num_bits=8)

        assert result["num_levels"] == 256
        assert result["step_size"] == 2.0 / 256
        assert len(result["quantized"]) == len(signal)

    def test_quantize_different_bits(self):
        """不同位数量化"""
        signal = np.linspace(-1, 1, 100)

        for bits in [4, 8, 12]:
            result = uniform_quantize(signal, num_bits=bits)
            assert result["num_levels"] == 2 ** bits
            assert result["step_size"] == 2.0 / (2 ** bits)

    def test_quantize_range(self):
        """量化范围测试"""
        signal = np.array([0.0])
        result = uniform_quantize(signal, num_bits=8, v_range=(-5.0, 5.0))

        assert result["step_size"] == 10.0 / 256
        assert result["num_levels"] == 256

    def test_quantize_error_bounds(self):
        """量化误差应在合理范围内"""
        signal = np.linspace(-1, 1, 1000)
        result = uniform_quantize(signal, num_bits=8)

        max_error = np.max(np.abs(result["quantization_error"]))
        assert max_error <= result["step_size"]

    def test_quantize_invalid_bits(self):
        """无效位数测试"""
        signal = np.array([0.0])

        with pytest.raises(ValueError):
            uniform_quantize(signal, num_bits=0)

        with pytest.raises(ValueError):
            uniform_quantize(signal, num_bits=33)

    def test_theoretical_snr(self):
        """理论 SNR 测试"""
        signal = np.array([0.0])
        result = uniform_quantize(signal, num_bits=8)

        assert result["snr_theoretical"] == pytest.approx(6.02 * 8 + 1.76, rel=1e-2)


class TestNonUniformQuantization:
    """测试非均匀量化"""

    def test_a_law_quantize(self):
        """A-law 量化测试"""
        signal = np.linspace(-0.9, 0.9, 100)
        result = non_uniform_quantize_a_law(signal, num_bits=8)

        assert len(result["quantized"]) == len(signal)
        assert result["num_levels"] == 256
        assert result["law_type"] == "A-law"
        assert result["A_parameter"] == 87.6

    def test_mu_law_quantize(self):
        """mu-law 量化测试"""
        signal = np.linspace(-0.9, 0.9, 100)
        result = non_uniform_quantize_mu_law(signal, num_bits=8)

        assert len(result["quantized"]) == len(signal)
        assert result["num_levels"] == 256
        assert result["law_type"] == "mu-law"
        assert result["mu_parameter"] == 255

    def test_non_uniform_preserves_range(self):
        """非均匀量化应保持幅度范围"""
        signal = np.linspace(-0.8, 0.8, 100)

        a_law_result = non_uniform_quantize_a_law(signal)
        mu_law_result = non_uniform_quantize_mu_law(signal)

        assert np.max(np.abs(a_law_result["quantized"])) <= 1.0
        assert np.max(np.abs(mu_law_result["quantized"])) <= 1.0


class TestQuantizationNoise:
    """测试量化噪声分析"""

    def test_noise_analysis(self):
        """噪声分析测试"""
        signal = np.linspace(-1, 1, 1000)
        quantized = signal  # 理想情况
        result = quantization_noise_analysis(signal, quantized)

        assert "mean_error" in result
        assert "rms_error" in result
        assert "max_error" in result
        assert result["rms_error"] == 0

    def test_noise_with_error(self):
        """有误差时的噪声分析"""
        signal = np.sin(np.linspace(0, 2 * np.pi, 1000))
        quantized = np.round(signal * 100) / 100
        result = quantization_noise_analysis(signal, quantized)

        assert result["rms_error"] > 0
        assert result["max_error"] > 0

    def test_snr_calculation(self):
        """SNR 计算"""
        signal = np.sin(np.linspace(0, 2 * np.pi, 1000))
        noise = np.zeros_like(signal)
        # When quantized = zeros, noise = signal, so SNR = 10*log10(P_signal/P_noise) = 0 dB
        snr = calculate_quantization_snr(signal, noise)
        assert snr == pytest.approx(0.0, abs=0.1)

    def test_snr_with_noise(self):
        """有噪声时的 SNR"""
        signal = np.sin(np.linspace(0, 2 * np.pi, 1000))
        noise = np.random.randn(1000) * 0.01
        quantized = signal - noise

        snr = calculate_quantization_snr(signal, quantized)
        assert snr > 0


class TestAdaptiveQuantization:
    """测试自适应量化"""

    def test_adaptive_quantize(self):
        """自适应量化测试"""
        signal = np.linspace(-1, 1, 100)
        result = adaptive_quantization(signal, num_bits=8)

        assert len(result["quantized"]) == len(signal)
        assert result["num_levels"] == 256
        assert result["max_amplitude"] == 1.0

    def test_adaptive_small_signal(self):
        """小信号自适应量化"""
        signal = np.linspace(-0.01, 0.01, 100)
        result = adaptive_quantization(signal, num_bits=8)

        assert len(result["quantized"]) == len(signal)
        assert result["max_amplitude"] == 0.01
