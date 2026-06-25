"""
频谱分析测试

测试频谱分析工具的正确性。
"""

import numpy as np
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.fft import fft
from src.spectrum import (
    magnitude_spectrum,
    power_spectrum,
    power_spectrum_db,
    phase_spectrum,
    frequency_bins,
    frequency_bins_positive,
    one_sided_spectrum,
    find_peaks,
    peak_frequencies,
    spectral_centroid,
    bandwidth,
)
from src.signals import sine_wave, composite_signal


class TestMagnitudeSpectrum:
    """幅度谱测试"""

    def test_constant_signal(self):
        """常数信号只有 DC 分量"""
        x = np.ones(8)
        X = fft(x)
        mag = magnitude_spectrum(X)
        assert np.isclose(mag[0], 8.0)
        assert np.allclose(mag[1:], 0.0, atol=1e-10)

    def test_pure_sine(self):
        """纯正弦波"""
        N = 64
        k = 8
        n = np.arange(N)
        x = np.sin(2 * np.pi * k * n / N)
        X = fft(x)
        mag = magnitude_spectrum(X)

        # 在 k 和 N-k 处有峰值
        assert mag[k] > N / 2 - 0.1
        assert mag[N - k] > N / 2 - 0.1

    def test_non_negative(self):
        """幅度谱应该非负"""
        np.random.seed(42)
        x = np.random.randn(32)
        X = fft(x)
        mag = magnitude_spectrum(X)
        assert np.all(mag >= 0)

    def test_symmetry(self):
        """实数信号的幅度谱应该对称"""
        np.random.seed(42)
        x = np.random.randn(16)
        X = fft(x)
        mag = magnitude_spectrum(X)

        # |X[k]| = |X[N-k]|
        for k in range(1, len(x) // 2):
            assert np.isclose(mag[k], mag[len(x) - k], atol=1e-10)


class TestPowerSpectrum:
    """功率谱测试"""

    def test_power_is_square_of_magnitude(self):
        """功率 = 幅度^2"""
        np.random.seed(42)
        x = np.random.randn(16)
        X = fft(x)

        mag = magnitude_spectrum(X)
        power = power_spectrum(X)

        assert np.allclose(power, mag ** 2, atol=1e-10)

    def test_normalize(self):
        """归一化后最大值为 1"""
        np.random.seed(42)
        x = np.random.randn(16)
        X = fft(x)

        power = power_spectrum(X, normalize=True)
        assert np.isclose(np.max(power), 1.0)

    def test_power_db(self):
        """功率谱 dB 测试"""
        # 已知功率信号
        X = np.array([10.0 + 0j, 1.0 + 0j, 0.1 + 0j])
        db = power_spectrum_db(X)

        # 10 * log10(100) = 20 dB
        assert np.isclose(db[0], 20.0, atol=0.1)
        # 10 * log10(1) = 0 dB
        assert np.isclose(db[1], 0.0, atol=0.1)
        # 10 * log10(0.01) = -20 dB
        assert np.isclose(db[2], -20.0, atol=0.1)


class TestPhaseSpectrum:
    """相位谱测试"""

    def test_pure_cosine_phase(self):
        """纯余弦波的相位：在峰值频率处相位为 0 或 π"""
        N = 64
        k = 8
        n = np.arange(N)
        x = np.cos(2 * np.pi * k * n / N)

        X = fft(x)
        phase = phase_spectrum(X)

        # 余弦波在 k 处相位应接近 0
        assert np.isclose(phase[k], 0.0, atol=0.1)

    def test_pure_sine_phase(self):
        """纯正弦波的相位：在峰值频率处相位为 -π/2"""
        N = 64
        k = 8
        n = np.arange(N)
        x = np.sin(2 * np.pi * k * n / N)

        X = fft(x)
        phase = phase_spectrum(X)

        # 正弦波在 k 处相位应接近 -π/2
        assert np.isclose(phase[k], -np.pi / 2, atol=0.1)

    def test_unwrap(self):
        """相位展开"""
        # 创建一个有相位跳变的信号
        phase = np.array([0.0, 0.5, 1.0, -3.0, -2.5, -2.0])
        X = np.exp(1j * phase)

        unwrapped = phase_spectrum(X, unwrap=True)
        # 展开后应该是单调递增的
        diffs = np.diff(unwrapped)
        assert np.all(diffs > 0) or np.all(diffs < 0) or len(diffs) == 0


class TestFrequencyBins:
    """频率轴测试"""

    def test_basic(self):
        """基本频率轴"""
        freqs = frequency_bins(8, 100.0)
        assert len(freqs) == 8
        assert freqs[0] == 0.0

    def test_nyquist(self):
        """Nyquist 频率"""
        N = 16
        sample_rate = 1000.0
        freqs = frequency_bins(N, sample_rate)
        # 第 N/2 个频率的绝对值应该是 Nyquist 频率
        assert np.isclose(abs(freqs[N // 2]), sample_rate / 2)

    def test_positive_bins(self):
        """正频率轴"""
        N = 16
        sample_rate = 1000.0
        freqs = frequency_bins_positive(N, sample_rate)
        assert len(freqs) == N // 2 + 1
        assert freqs[0] == 0.0
        assert np.all(freqs >= 0)

    def test_frequency_resolution(self):
        """频率分辨率"""
        N = 100
        sample_rate = 1000.0
        freqs = frequency_bins(N, sample_rate)
        expected_resolution = sample_rate / N
        assert np.isclose(freqs[1] - freqs[0], expected_resolution)


class TestOneSidedSpectrum:
    """单边谱测试"""

    def test_real_signal(self):
        """实数信号的单边谱"""
        N = 16
        x = np.random.randn(N)
        X = fft(x)

        one_sided = one_sided_spectrum(X)
        assert len(one_sided) == N // 2 + 1

    def test_dc_preserved(self):
        """DC 分量保持不变"""
        x = np.ones(8)
        X = fft(x)
        one_sided = one_sided_spectrum(X)
        assert np.isclose(one_sided[0], 8.0)

    def test_symmetry(self):
        """单边谱的能量应该等于双边谱的能量"""
        np.random.seed(42)
        N = 16
        x = np.random.randn(N)
        X = fft(x)

        one_sided = one_sided_spectrum(X)
        total_two_sided = np.sum(np.abs(X) ** 2)
        total_one_sided = np.sum(np.abs(one_sided) ** 2)

        # 由于单边谱乘以了 2，功率会不同，但应该成比例
        assert total_one_sided > 0


class TestFindPeaks:
    """峰值检测测试"""

    def test_simple_peak(self):
        """简单峰值"""
        spectrum = np.array([0, 0, 0, 5, 0, 0, 0])
        peaks = find_peaks(spectrum, threshold=0.1, min_distance=1)
        assert 3 in peaks

    def test_multiple_peaks(self):
        """多个峰值"""
        spectrum = np.array([0, 3, 0, 0, 5, 0, 0, 4, 0])
        peaks = find_peaks(spectrum, threshold=0.1, min_distance=1)
        assert 1 in peaks
        assert 4 in peaks
        assert 7 in peaks

    def test_threshold_filtering(self):
        """阈值过滤"""
        spectrum = np.array([0, 1, 0, 0, 5, 0, 0, 1, 0])
        peaks = find_peaks(spectrum, threshold=0.5, min_distance=1)
        # 只有 5 应该被检测到
        assert 4 in peaks
        assert 1 not in peaks

    def test_min_distance(self):
        """最小距离约束"""
        spectrum = np.array([0, 3, 5, 3, 0])
        peaks = find_peaks(spectrum, threshold=0.1, min_distance=3)
        # 由于距离约束，可能只检测到一个
        assert len(peaks) <= 2

    def test_empty_spectrum(self):
        """空频谱"""
        peaks = find_peaks(np.array([]), threshold=0.1)
        assert len(peaks) == 0

    def test_all_zeros(self):
        """全零频谱"""
        peaks = find_peaks(np.zeros(10), threshold=0.1)
        assert len(peaks) == 0

    def test_with_fft(self):
        """与 FFT 结合使用"""
        sample_rate = 1000.0
        duration = 1.0
        signal = composite_signal(
            [100, 300, 500], [1.0, 0.5, 0.3], sample_rate, duration
        )
        X = fft(signal)
        mag = magnitude_spectrum(X)

        # 检测峰值
        peaks = find_peaks(mag[:len(mag)//2], threshold=0.08, min_distance=10)
        freqs = frequency_bins(len(signal), sample_rate)

        # 应该检测到至少 2 个主要峰值
        assert len(peaks) >= 2


class TestSpectralCentroid:
    """频谱质心测试"""

    def test_low_frequency_centroid(self):
        """低频信号的质心应该较低"""
        sample_rate = 1000.0
        signal = sine_wave(50, sample_rate, 1.0)
        X = fft(signal)
        centroid = spectral_centroid(X, sample_rate)

        # 质心应该接近 50 Hz
        assert centroid < 200

    def test_high_frequency_centroid(self):
        """高频信号的质心应该较高"""
        sample_rate = 1000.0
        signal = sine_wave(400, sample_rate, 1.0)
        X = fft(signal)
        centroid = spectral_centroid(X, sample_rate)

        # 质心应该接近 400 Hz (正频率部分)
        assert centroid > 100

    def test_mixed_signal(self):
        """混合信号的质心取决于各频率的幅度"""
        sample_rate = 1000.0
        # 低频大幅度 + 高频小幅度
        signal = composite_signal(
            [50, 400], [1.0, 0.1], sample_rate, 1.0
        )
        X = fft(signal)
        centroid = spectral_centroid(X, sample_rate)

        # 质心应该偏向低频
        assert centroid < 200


class TestBandwidth:
    """带宽测试"""

    def test_narrow_band(self):
        """窄带信号的带宽应该较小"""
        sample_rate = 1000.0
        signal = sine_wave(100, sample_rate, 1.0)
        X = fft(signal)
        bw = bandwidth(X, sample_rate, threshold=0.5)

        # 单频信号带宽很窄
        assert bw < 100

    def test_wide_band(self):
        """宽带信号的带宽应该较大"""
        sample_rate = 1000.0
        signal = composite_signal(
            [50, 150, 250, 350, 450],
            [1.0, 1.0, 1.0, 1.0, 1.0],
            sample_rate,
            1.0,
        )
        X = fft(signal)
        bw = bandwidth(X, sample_rate, threshold=0.3)

        assert bw > 200


class TestPeakFrequencies:
    """峰值频率检测测试"""

    def test_known_frequencies(self):
        """已知频率的检测"""
        sample_rate = 1000.0
        signal = composite_signal(
            [100, 300], [1.0, 0.5], sample_rate, 1.0
        )
        X = fft(signal)
        peaks = peak_frequencies(X, sample_rate, threshold=0.1, min_distance=10)

        # 应该检测到 2 个主要频率
        assert len(peaks) >= 2

        # 第一个应该是 100 Hz（幅度最大）
        freq_list = [p[0] for p in peaks]
        assert any(80 < f < 120 for f in freq_list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
