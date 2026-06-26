"""
重建滤波器测试
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import pytest

from src.reconstruction import (
    zero_order_hold,
    ideal_reconstruction,
    reconstruct_with_filter,
    compute_zoh_frequency_response,
)


class TestZeroOrderHold:
    """测试零阶保持"""

    def test_zoh_basic(self):
        """基本 ZOH 测试"""
        samples = np.array([0.0, 0.5, 1.0, 0.5, 0.0])
        times = np.array([0.0, 0.1, 0.2, 0.3, 0.4])

        result = zero_order_hold(samples, times, 0, 0.5, 100)

        assert len(result["signal"]) > 0
        assert len(result["times"]) == len(result["signal"])
        assert result["signal"][0] == 0.0  # 第一个采样值

    def test_zoh_output_resolution(self):
        """ZOH 输出分辨率"""
        samples = np.array([0.0, 1.0])
        times = np.array([0.0, 1.0])

        result = zero_order_hold(samples, times, 0, 1, 10)

        assert len(result["times"]) == 10

    def test_zoh_constant(self):
        """ZOH 常数保持"""
        samples = np.array([0.5])
        times = np.array([0.0])

        result = zero_order_hold(samples, times, 0, 0.1, 100)

        assert np.allclose(result["signal"], 0.5, atol=1e-10)


class TestIdealReconstruction:
    """测试理想重建"""

    def test_ideal_reconstruction_basic(self):
        """基本理想重建"""
        samples = np.array([0.0, 1.0, 0.0])
        times = np.array([0.0, 0.5, 1.0])

        result = ideal_reconstruction(samples, times, 0, 1, 100)

        assert len(result["signal"]) > 0
        assert len(result["times"]) == len(result["signal"])

    def test_ideal_reconstruction_dc(self):
        """直流信号重建"""
        samples = np.ones(10)
        times = np.linspace(0, 1, 10)

        result = ideal_reconstruction(samples, times, 0, 1, 100)

        # 理想重建应该接近原始信号
        assert np.mean(result["signal"]) == pytest.approx(1.0, abs=0.1)


class TestReconstructWithFilter:
    """测试滤波重建"""

    def test_filter_reconstruction(self):
        """滤波重建"""
        samples = np.array([0.0, 0.5, 1.0, 0.5, 0.0])
        times = np.array([0.0, 0.1, 0.2, 0.3, 0.4])

        result = reconstruct_with_filter(samples, times, 0, 0.5, 100, cutoff_freq=10)

        assert "signal" in result
        assert "cutoff_freq" in result
        assert result["cutoff_freq"] == 10


class TestZOHFrequencyResponse:
    """测试 ZOH 频率响应"""

    def test_zoh_frequency_response(self):
        """ZOH 频率响应"""
        result = compute_zoh_frequency_response(fs=1000, num_points=1024)

        assert len(result["frequencies"]) == 1024
        assert len(result["magnitude_db"]) == 1024
        assert len(result["phase_deg"]) == 1024

    def test_zoh_dc_response(self):
        """ZOH 直流响应"""
        result = compute_zoh_frequency_response(fs=1000)

        # 直流处幅度应为 Ts (即 0.001), 转换为 dB 约为 -60 dB
        # |H(0)| = Ts = 0.001, 20*log10(0.001) = -60 dB
        assert result["magnitude_db"][0] == pytest.approx(-60, abs=1)

    def test_zoh_nyquist_response(self):
        """ZOH 奈奎斯特频率响应"""
        result = compute_zoh_frequency_response(fs=1000)

        # 奈奎斯特频率处增益应接近 -3.92 dB
        nyquist_idx = len(result["frequencies"]) // 2
        # sinc(pi) = 0, 所以增益应接近 -inf
        assert result["magnitude_db"][nyquist_idx] < -10  # 至少衰减 10 dB
