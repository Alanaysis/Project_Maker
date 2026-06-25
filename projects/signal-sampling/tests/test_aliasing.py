"""
混叠模块测试
=============

测试混叠演示、抗混叠滤波等功能。
"""

import numpy as np
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.aliasing import (
    demonstrate_aliasing,
    anti_aliasing_filter,
    compute_spectrum,
    show_aliasing_effect,
    create_anti_aliasing_demo,
)


class TestDemonstrateAliasing:
    """混叠演示测试"""

    def test_basic(self):
        """测试基本混叠演示"""
        result = demonstrate_aliasing(f_signal=100, fs=80, duration=0.1)

        assert "t_continuous" in result
        assert "signal_continuous" in result
        assert "t_sampled" in result
        assert "samples" in result
        assert "alias_freq" in result
        assert "alias_signal" in result

    def test_alias_frequency(self):
        """测试混叠频率计算"""
        # f=100, fs=80 -> alias = |100 - 80| = 20
        result = demonstrate_aliasing(f_signal=100, fs=80, duration=0.1)
        assert np.isclose(result["alias_freq"], 20)

        # f=150, fs=100 -> alias = |150 - 100| = 50
        result = demonstrate_aliasing(f_signal=150, fs=100, duration=0.1)
        assert np.isclose(result["alias_freq"], 50)

        # f=250, fs=100 -> alias = |250 - 200| = 50
        result = demonstrate_aliasing(f_signal=250, fs=100, duration=0.1)
        assert np.isclose(result["alias_freq"], 50)

    def test_no_aliasing(self):
        """测试无混叠情况 (信号频率低于采样频率)"""
        # fs=1000, f=100 -> 无混叠，但混叠公式不会返回0
        # 混叠频率计算: |f - round(f/fs)*fs| = |100 - 0*1000| = 100
        # 这不是真正意义上的混叠，因为 fs >= 2*f
        result = demonstrate_aliasing(f_signal=100, fs=1000, duration=0.01)
        # 当 fs >= 2*f 时，混叠公式给出的结果等于原始频率
        # 这意味着没有"真正的"混叠发生
        assert result["alias_freq"] == 100  # 混叠频率等于原始频率，没有混叠

    def test_sample_count(self):
        """测试采样点数"""
        fs = 100
        duration = 0.5
        result = demonstrate_aliasing(f_signal=10, fs=fs, duration=duration)
        assert len(result["t_sampled"]) == int(fs * duration)

    def test_invalid_fs(self):
        """测试无效采样率"""
        with pytest.raises(ValueError):
            demonstrate_aliasing(f_signal=100, fs=0, duration=0.1)
        with pytest.raises(ValueError):
            demonstrate_aliasing(f_signal=100, fs=-100, duration=0.1)


class TestAntiAliasingFilter:
    """抗混叠滤波器测试"""

    def test_basic(self):
        """测试基本滤波"""
        fs = 1000
        t = np.linspace(0, 1, fs)
        # 低频 + 高频信号
        signal = np.sin(2 * np.pi * 50 * t) + np.sin(2 * np.pi * 200 * t)

        filtered = anti_aliasing_filter(signal, fs=fs, cutoff_freq=100)

        assert len(filtered) == len(signal)

    def test_removes_high_frequency(self):
        """测试去除高频分量"""
        fs = 1000
        t = np.linspace(0, 1, fs)
        signal = np.sin(2 * np.pi * 50 * t) + np.sin(2 * np.pi * 200 * t)

        filtered = anti_aliasing_filter(signal, fs=fs, cutoff_freq=100)

        # 滤波后高频分量应被衰减
        spectrum_orig = np.abs(np.fft.fft(signal))
        spectrum_filt = np.abs(np.fft.fft(filtered))

        freqs = np.fft.fftfreq(fs, 1.0 / fs)
        high_freq_mask = np.abs(freqs) > 150

        # 高频部分应显著衰减
        assert np.mean(spectrum_filt[high_freq_mask]) < np.mean(spectrum_orig[high_freq_mask])

    def test_preserves_low_frequency(self):
        """测试保留低频分量"""
        fs = 1000
        t = np.linspace(0, 1, fs)
        signal = np.sin(2 * np.pi * 50 * t)

        filtered = anti_aliasing_filter(signal, fs=fs, cutoff_freq=100)

        # 低频信号应基本保留
        # 在信号内部比较
        assert np.corrcoef(signal[100:-100], filtered[100:-100])[0, 1] > 0.9

    def test_invalid_cutoff(self):
        """测试无效截止频率"""
        signal = np.ones(100)

        with pytest.raises(ValueError):
            anti_aliasing_filter(signal, fs=100, cutoff_freq=60)  # > Nyquist


class TestComputeSpectrum:
    """频谱计算测试"""

    def test_basic(self):
        """测试基本频谱计算"""
        fs = 1000
        t = np.linspace(0, 1, fs, endpoint=False)
        signal = np.sin(2 * np.pi * 100 * t)

        freqs, magnitude = compute_spectrum(signal, fs)

        assert len(freqs) == len(magnitude)
        assert freqs[0] == 0

    def test_peak_frequency(self):
        """测试峰值频率"""
        fs = 1000
        f_signal = 100
        t = np.linspace(0, 1, fs, endpoint=False)
        signal = np.sin(2 * np.pi * f_signal * t)

        freqs, magnitude = compute_spectrum(signal, fs)

        peak_idx = np.argmax(magnitude)
        peak_freq = freqs[peak_idx]

        # 峰值应接近信号频率
        assert np.isclose(peak_freq, f_signal, atol=fs / len(signal) + 1)

    def test_multiple_frequencies(self):
        """测试多频率信号"""
        fs = 1000
        t = np.linspace(0, 1, fs, endpoint=False)
        signal = (
            np.sin(2 * np.pi * 100 * t) +
            np.sin(2 * np.pi * 200 * t) +
            np.sin(2 * np.pi * 300 * t)
        )

        freqs, magnitude = compute_spectrum(signal, fs)

        # 应有三个明显的峰值
        # 找到局部最大值
        from scipy.signal import find_peaks
        peaks, _ = find_peaks(magnitude, height=np.max(magnitude) * 0.5)

        assert len(peaks) >= 3


class TestShowAliasingEffect:
    """混叠效果展示测试"""

    def test_basic(self):
        """测试基本展示"""
        result = show_aliasing_effect(
            f_signal=100,
            fs_list=[50, 80, 100, 200, 1000],
            duration=0.05,
        )

        assert "reference" in result
        assert len(result) > 1

    def test_aliasing_detected(self):
        """测试混叠检测"""
        result = show_aliasing_effect(
            f_signal=100,
            fs_list=[50, 80],
            duration=0.05,
        )

        # fs=50 和 fs=80 都应产生混叠
        for key in result:
            if key != "reference":
                assert result[key]["is_aliasing"] is True

    def test_no_aliasing_detected(self):
        """测试无混叠检测"""
        result = show_aliasing_effect(
            f_signal=100,
            fs_list=[300, 1000],
            duration=0.05,
        )

        # fs=300 和 fs=1000 不应产生混叠
        for key in result:
            if key != "reference":
                assert result[key]["is_aliasing"] is False


class TestCreateAntiAliasingDemo:
    """抗混叠演示测试"""

    def test_basic(self):
        """测试基本演示"""
        result = create_anti_aliasing_demo(
            f_high=200,
            f_low=30,
            fs=100,
            duration=0.1,
        )

        assert "t_continuous" in result
        assert "signal_mixed" in result
        assert "t_sampled" in result
        assert "samples_direct" in result
        assert "samples_filtered" in result

    def test_sample_counts(self):
        """测试采样点数"""
        fs = 100
        duration = 0.5
        result = create_anti_aliasing_demo(
            f_high=200,
            f_low=30,
            fs=fs,
            duration=duration,
        )

        assert len(result["t_sampled"]) == int(fs * duration)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
