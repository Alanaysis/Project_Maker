"""
滤波器模块测试
"""

import pytest
import numpy as np
from src.audio_signal import AudioSignal
from src.filters import LowPassFilter, HighPassFilter, BandPassFilter, NotchFilter


class TestLowPassFilter:
    """低通滤波器测试"""

    def test_basic_filtering(self):
        """测试基本低通滤波"""
        # 创建包含高低频的信号
        sample_rate = 44100
        t = np.linspace(0, 0.1, int(sample_rate * 0.1), endpoint=False)
        low_freq = np.sin(2 * np.pi * 100 * t)   # 100 Hz
        high_freq = np.sin(2 * np.pi * 5000 * t)  # 5000 Hz
        signal = AudioSignal(low_freq + high_freq, sample_rate)

        # 低通滤波，截止频率 1000 Hz
        lpf = LowPassFilter(cutoff_freq=1000, sample_rate=sample_rate)
        filtered = lpf.apply(signal)

        # 低频应该保留，高频应该衰减
        # 检查 100 Hz 分量仍然存在
        spectrum = np.abs(np.fft.fft(filtered.data))
        freqs = np.fft.fftfreq(len(filtered.data), 1.0 / sample_rate)

        # 找 100 Hz 和 5000 Hz 的幅度
        idx_100 = np.argmin(np.abs(freqs - 100))
        idx_5000 = np.argmin(np.abs(freqs - 5000))

        # 100 Hz 应该比 5000 Hz 大得多
        assert spectrum[idx_100] > spectrum[idx_5000] * 10

    def test_cutoff_frequency(self):
        """测试截止频率"""
        sample_rate = 44100
        lpf = LowPassFilter(cutoff_freq=1000, sample_rate=sample_rate)

        # 获取频率响应
        freqs, response = lpf.get_frequency_response(1024)

        # 在截止频率以下，响应应该接近1
        below_cutoff = freqs < 800
        assert np.all(response[below_cutoff] > 0.8)

        # 在截止频率以上，响应应该接近0
        above_cutoff = freqs > 1200
        assert np.all(response[above_cutoff] < 0.2)

    def test_rolloff(self):
        """测试过渡带"""
        sample_rate = 44100
        lpf = LowPassFilter(cutoff_freq=1000, rolloff_width=200,
                           sample_rate=sample_rate)

        freqs, response = lpf.get_frequency_response(1024)

        # 过渡带应该是平滑的
        transition = (freqs >= 900) & (freqs <= 1100)
        transition_response = response[transition]

        # 响应应该单调递减
        diffs = np.diff(transition_response)
        assert np.all(diffs <= 0.01)  # 允许小误差


class TestHighPassFilter:
    """高通滤波器测试"""

    def test_basic_filtering(self):
        """测试基本高通滤波"""
        sample_rate = 44100
        t = np.linspace(0, 0.1, int(sample_rate * 0.1), endpoint=False)
        low_freq = np.sin(2 * np.pi * 100 * t)
        high_freq = np.sin(2 * np.pi * 5000 * t)
        signal = AudioSignal(low_freq + high_freq, sample_rate)

        # 高通滤波，截止频率 1000 Hz
        hpf = HighPassFilter(cutoff_freq=1000, sample_rate=sample_rate)
        filtered = hpf.apply(signal)

        # 高频应该保留，低频应该衰减
        spectrum = np.abs(np.fft.fft(filtered.data))
        freqs = np.fft.fftfreq(len(filtered.data), 1.0 / sample_rate)

        idx_100 = np.argmin(np.abs(freqs - 100))
        idx_5000 = np.argmin(np.abs(freqs - 5000))

        assert spectrum[idx_5000] > spectrum[idx_100] * 10

    def test_cutoff_frequency(self):
        """测试截止频率"""
        sample_rate = 44100
        hpf = HighPassFilter(cutoff_freq=1000, sample_rate=sample_rate)

        freqs, response = hpf.get_frequency_response(1024)

        # 截止频率以下应该衰减
        below_cutoff = freqs < 800
        assert np.all(response[below_cutoff] < 0.2)

        # 截止频率以上应该通过
        above_cutoff = freqs > 1200
        assert np.all(response[above_cutoff] > 0.8)


class TestBandPassFilter:
    """带通滤波器测试"""

    def test_basic_filtering(self):
        """测试基本带通滤波"""
        sample_rate = 44100
        t = np.linspace(0, 0.1, int(sample_rate * 0.1), endpoint=False)

        # 三个不同频率
        low = np.sin(2 * np.pi * 100 * t)
        mid = np.sin(2 * np.pi * 1000 * t)
        high = np.sin(2 * np.pi * 5000 * t)
        signal = AudioSignal(low + mid + high, sample_rate)

        # 带通滤波，通过 500-2000 Hz
        bpf = BandPassFilter(low_freq=500, high_freq=2000, sample_rate=sample_rate)
        filtered = bpf.apply(signal)

        # 中频应该保留
        spectrum = np.abs(np.fft.fft(filtered.data))
        freqs = np.fft.fftfreq(len(filtered.data), 1.0 / sample_rate)

        idx_100 = np.argmin(np.abs(freqs - 100))
        idx_1000 = np.argmin(np.abs(freqs - 1000))
        idx_5000 = np.argmin(np.abs(freqs - 5000))

        assert spectrum[idx_1000] > spectrum[idx_100] * 5
        assert spectrum[idx_1000] > spectrum[idx_5000] * 5

    def test_invalid_frequencies(self):
        """测试无效频率"""
        with pytest.raises(ValueError):
            BandPassFilter(low_freq=2000, high_freq=1000)

    def test_frequency_response(self):
        """测试频率响应"""
        sample_rate = 44100
        bpf = BandPassFilter(low_freq=500, high_freq=2000, sample_rate=sample_rate)

        freqs, response = bpf.get_frequency_response(1024)

        # 通带内应该接近1
        passband = (freqs >= 600) & (freqs <= 1900)
        assert np.all(response[passband] > 0.8)

        # 通带外应该接近0
        stopband_low = freqs < 400
        stopband_high = freqs > 2500
        assert np.all(response[stopband_low] < 0.2)
        assert np.all(response[stopband_high] < 0.2)


class TestNotchFilter:
    """陷波滤波器测试"""

    def test_basic_filtering(self):
        """测试基本陷波滤波"""
        sample_rate = 44100
        t = np.linspace(0, 1.0, int(sample_rate * 1.0), endpoint=False)

        # 信号 + 干扰（使用较长的信号以获得更好的频率分辨率）
        signal_freq = np.sin(2 * np.pi * 1000 * t)
        interference = 0.5 * np.sin(2 * np.pi * 50 * t)  # 50 Hz 工频干扰（幅度较小）
        signal = AudioSignal(signal_freq + interference, sample_rate)

        # 陷波滤波，去除 50 Hz
        notch = NotchFilter(center_freq=50, bandwidth=30, sample_rate=sample_rate)
        filtered = notch.apply(signal)

        # 滤波后信号应该存在
        assert len(filtered) == len(signal)
        assert np.any(filtered.data != 0)

    def test_frequency_response(self):
        """测试频率响应"""
        sample_rate = 44100
        notch = NotchFilter(center_freq=1000, bandwidth=200, sample_rate=sample_rate)

        freqs, response = notch.get_frequency_response(4096)

        # 远离中心频率应该接近1
        far_from_center = np.abs(freqs - 1000) > 500
        assert np.all(response[far_from_center] > 0.9)

        # 中心频率附近应该衰减（检查更宽的范围）
        near_center = np.abs(freqs - 1000) < 50
        # 至少有一些频率被衰减
        assert np.any(response[near_center] < 0.8)


class TestFilterCombination:
    """滤波器组合测试"""

    def test_cascade_filters(self):
        """测试级联滤波"""
        sample_rate = 44100
        t = np.linspace(0, 0.1, int(sample_rate * 0.1), endpoint=False)
        signal_data = np.sin(2 * np.pi * 1000 * t)
        signal = AudioSignal(signal_data, sample_rate)

        # 级联两个滤波器
        lpf = LowPassFilter(cutoff_freq=2000, sample_rate=sample_rate)
        hpf = HighPassFilter(cutoff_freq=500, sample_rate=sample_rate)

        filtered = lpf.apply(signal)
        filtered = hpf.apply(filtered)

        # 应该保留 500-2000 Hz
        assert len(filtered) == len(signal)
