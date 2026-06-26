"""
采样模块测试
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import pytest

from src.sampling import (
    ideal_sampling,
    calculate_nyquist,
    check_aliasing,
    aperture_error,
    aperture_error_rms,
    generate_sample_clock,
    undersampling_demo,
)


class TestIdealSampling:
    """测试理想采样"""

    def test_sampling_basic(self):
        """基本采样测试"""
        t = np.linspace(0, 1, 1000)
        signal = np.sin(2 * np.pi * 1.0 * t)
        result = ideal_sampling(signal, fs=100)

        assert result["num_samples"] > 0
        assert len(result["samples"]) == result["num_samples"]
        assert result["fs"] == 100
        assert result["ts"] == 0.01

    def test_sampling_different_rates(self):
        """不同采样率测试"""
        t = np.linspace(0, 1, 1000)
        signal = np.sin(2 * np.pi * 5.0 * t)

        for fs in [50, 100, 200, 1000]:
            result = ideal_sampling(signal, fs=fs)
            assert result["num_samples"] > 0
            assert result["fs"] == fs

    def test_sampling_time_range(self):
        """不同时间范围测试"""
        t = np.linspace(0, 2, 2000)
        signal = np.sin(2 * np.pi * 1.0 * t)
        result = ideal_sampling(signal, fs=10, t_start=0.5, t_end=1.5)

        assert result["num_samples"] > 0
        assert result["sample_times"][0] >= 0.5
        assert result["sample_times"][-1] <= 1.5


class TestNyquist:
    """测试奈奎斯特相关功能"""

    def test_calculate_nyquist(self):
        """计算奈奎斯特频率"""
        assert calculate_nyquist(100) == 200
        assert calculate_nyquist(1000) == 2000
        assert calculate_nyquist(50) == 100

    def test_check_aliasing_no_aliasing(self):
        """无混叠检测"""
        result = check_aliasing(100, 300)
        assert result["aliased"] is False
        assert result["nyquist_freq"] == 200
        assert result["fs_ratio"] == 3.0

    def test_check_aliasing_with_aliasing(self):
        """混叠检测"""
        result = check_aliasing(100, 150)
        assert result["aliased"] is True
        assert result["nyquist_freq"] == 200
        assert result["fs_ratio"] == 1.5

    def test_check_aliasing_nyquist_boundary(self):
        """奈奎斯特边界测试"""
        result = check_aliasing(100, 200)
        assert result["aliased"] is False  # 刚好等于奈奎斯特频率

    def test_check_aliasing_undersampling(self):
        """欠采样测试"""
        result = check_aliasing(100, 100)
        assert result["aliased"] is True


class TestApertureError:
    """测试孔径误差"""

    def test_aperture_error_positive(self):
        """孔径误差应为正值"""
        error = aperture_error(sigma=1e-9, signal_freq=1000, amplitude=1.0)
        assert error > 0

    def test_aperture_error_scaling(self):
        """孔径误差随参数缩放"""
        error1 = aperture_error(sigma=1e-9, signal_freq=1000, amplitude=1.0)
        error2 = aperture_error(sigma=2e-9, signal_freq=1000, amplitude=1.0)
        assert error2 == 2 * error1

    def test_aperture_error_rms(self):
        """RMS 孔径误差"""
        error_rms = aperture_error_rms(sigma=1e-9, signal_freq=1000, amplitude=1.0)
        error_peak = aperture_error(sigma=1e-9, signal_freq=1000, amplitude=1.0)
        assert error_rms == pytest.approx(error_peak / np.sqrt(2), rel=1e-5)


class TestSampleClock:
    """测试采样时钟"""

    def test_clock_generation(self):
        """时钟生成测试"""
        result = generate_sample_clock(fs=100, duration=0.1)

        assert len(result["clock_times"]) > 0
        assert result["period"] == 0.01
        assert np.all(result["clock_values"] == 1)

    def test_clock_period(self):
        """时钟周期验证"""
        result = generate_sample_clock(fs=1000, duration=0.01)
        if len(result["clock_times"]) > 1:
            dt = np.diff(result["clock_times"])
            assert np.allclose(dt, 0.001)


class TestUndersamplingDemo:
    """测试欠采样演示"""

    def test_undersampling_demo(self):
        """欠采样演示"""
        result = undersampling_demo(signal_freq=100, fs_values=[50, 100, 200, 500])

        assert result["signal_freq"] == 100
        assert len(result["results"]) == 4

        # 检查混叠检测结果
        assert result["results"][0]["aliased"] is True   # 50 Hz < 200 Hz
        assert result["results"][2]["aliased"] is False   # 200 Hz >= 200 Hz
