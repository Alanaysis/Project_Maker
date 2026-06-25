"""
采样模块测试
=============

测试奈奎斯特采样、过采样、欠采样等功能。
"""

import numpy as np
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.sampling import (
    SamplingConfig,
    nyquist_sample,
    oversample,
    undersample,
    sample_signal,
    calculate_nyquist_rate,
    get_sampling_info,
)


class TestSamplingConfig:
    """采样配置测试"""

    def test_basic_config(self):
        """测试基本配置"""
        config = SamplingConfig(fs=8000, duration=1.0, f_signal=1000)
        assert config.fs == 8000
        assert config.duration == 1.0
        assert config.f_signal == 1000

    def test_nyquist_rate(self):
        """测试奈奎斯特率计算"""
        config = SamplingConfig(fs=8000, duration=1.0, f_signal=1000)
        assert config.nyquist_rate == 2000.0

    def test_oversampling_ratio(self):
        """测试过采样率"""
        config = SamplingConfig(fs=8000, duration=1.0, f_signal=1000)
        assert config.oversampling_ratio == 4.0

    def test_nyquist_satisfied(self):
        """测试奈奎斯特条件"""
        config_ok = SamplingConfig(fs=4000, duration=1.0, f_signal=1000)
        assert config_ok.is_nyquist_satisfied is True

        config_bad = SamplingConfig(fs=1000, duration=1.0, f_signal=1000)
        assert config_bad.is_nyquist_satisfied is False


class TestCalculateNyquistRate:
    """奈奎斯特率计算测试"""

    def test_basic(self):
        """测试基本计算"""
        assert calculate_nyquist_rate(1000) == 2000.0
        assert calculate_nyquist_rate(44100) == 88200.0

    def test_invalid_input(self):
        """测试无效输入"""
        with pytest.raises(ValueError):
            calculate_nyquist_rate(-100)
        with pytest.raises(ValueError):
            calculate_nyquist_rate(0)


class TestNyquistSample:
    """奈奎斯特采样测试"""

    def test_basic_sampling(self):
        """测试基本采样"""
        f_signal = 100
        fs = 1000
        duration = 0.1

        signal_func = lambda t: np.sin(2 * np.pi * f_signal * t)
        t_sampled, samples = nyquist_sample(signal_func, f_signal, fs, duration)

        assert len(t_sampled) == int(fs * duration)
        assert len(samples) == int(fs * duration)
        assert np.allclose(samples, np.sin(2 * np.pi * f_signal * t_sampled), atol=1e-10)

    def test_nyquist_rate_sampling(self):
        """测试奈奎斯特率采样"""
        f_signal = 100
        fs = 200  # 恰好等于奈奎斯特率
        duration = 0.1

        signal_func = lambda t: np.sin(2 * np.pi * f_signal * t)
        t_sampled, samples = nyquist_sample(signal_func, f_signal, fs, duration)

        assert len(t_sampled) == int(fs * duration)

    def test_below_nyquist_raises(self):
        """测试低于奈奎斯特率应抛出异常"""
        f_signal = 100
        fs = 100  # 低于奈奎斯特率

        signal_func = lambda t: np.sin(2 * np.pi * f_signal * t)

        with pytest.raises(ValueError):
            nyquist_sample(signal_func, f_signal, fs, 0.1)


class TestOversample:
    """过采样测试"""

    def test_basic_oversampling(self):
        """测试基本过采样"""
        f_signal = 100
        oversampling_factor = 4
        duration = 0.1

        signal_func = lambda t: np.sin(2 * np.pi * f_signal * t)
        t_sampled, samples, fs = oversample(signal_func, f_signal, oversampling_factor, duration)

        expected_fs = 2 * f_signal * oversampling_factor
        assert fs == expected_fs
        assert len(t_sampled) == int(fs * duration)

    def test_oversampling_factor_1(self):
        """测试过采样倍数为 1 (奈奎斯特率)"""
        f_signal = 100
        oversampling_factor = 1
        duration = 0.1

        signal_func = lambda t: np.sin(2 * np.pi * f_signal * t)
        t_sampled, samples, fs = oversample(signal_func, f_signal, oversampling_factor, duration)

        assert fs == 200  # 2 * 100

    def test_invalid_factor(self):
        """测试无效过采样倍数"""
        signal_func = lambda t: np.sin(2 * np.pi * 100 * t)

        with pytest.raises(ValueError):
            oversample(signal_func, 100, 0, 0.1)


class TestUndersample:
    """欠采样测试"""

    def test_basic_undersampling(self):
        """测试基本欠采样"""
        f_signal = 100
        fs = 80  # 低于奈奎斯特率
        duration = 0.1

        signal_func = lambda t: np.sin(2 * np.pi * f_signal * t)
        t_sampled, samples, alias_freq = undersample(signal_func, f_signal, fs, duration)

        assert len(t_sampled) == int(fs * duration)
        # 混叠频率应为 20 Hz (100 - 80)
        assert abs(alias_freq - 20) < 1e-10

    def test_above_nyquist_raises(self):
        """测试高于奈奎斯特率应抛出异常"""
        f_signal = 100
        fs = 300  # 高于奈奎斯特率

        signal_func = lambda t: np.sin(2 * np.pi * f_signal * t)

        with pytest.raises(ValueError):
            undersample(signal_func, f_signal, fs, 0.1)


class TestSampleSignal:
    """信号采样测试"""

    def test_basic_sample(self):
        """测试基本采样"""
        t = np.linspace(0, 1, 1001)
        signal = np.sin(2 * np.pi * 10 * t)
        fs = 100

        t_sampled, samples = sample_signal(t, signal, fs)

        # 采样点数约为 fs * duration，由于步长取整可能有微小偏差
        assert abs(len(t_sampled) - 100) <= 2
        assert len(t_sampled) == len(samples)

    def test_sample_preserves_values(self):
        """测试采样保留正确值"""
        t = np.linspace(0, 1, 1001)
        signal = np.sin(2 * np.pi * 10 * t)
        fs = 100

        t_sampled, samples = sample_signal(t, signal, fs)

        # 验证采样值与原始信号一致
        dt = t[1] - t[0]
        for i, ts in enumerate(t_sampled):
            idx = int(round(ts / dt))
            idx = min(idx, len(signal) - 1)
            assert np.isclose(samples[i], signal[idx], atol=1e-10)


class TestGetSamplingInfo:
    """采样信息测试"""

    def test_info_output(self):
        """测试信息输出"""
        config = SamplingConfig(fs=44100, duration=1.0, f_signal=20000)
        info = get_sampling_info(config)

        assert "采样频率" in info
        assert "信号频率" in info
        assert "奈奎斯特率" in info
        assert "过采样率" in info
        assert "是否满足奈奎斯特" in info
        assert info["是否满足奈奎斯特"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
