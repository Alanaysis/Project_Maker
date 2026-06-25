"""
信号生成测试
"""

import numpy as np
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.signals import (
    sine_wave,
    cosine_wave,
    composite_signal,
    square_wave,
    sawtooth_wave,
    triangle_wave,
    white_noise,
    chirp_signal,
    impulse_train,
    gaussian_pulse,
)
from src.fft import fft
from src.spectrum import magnitude_spectrum


class TestSineWave:
    """正弦波测试"""

    def test_frequency(self):
        """频率正确性"""
        sample_rate = 1000.0
        freq = 100.0
        signal = sine_wave(freq, sample_rate, 1.0)
        X = fft(signal)
        N = len(signal)
        mag = magnitude_spectrum(X[:N//2])

        # 峰值应该在 100 Hz 处
        peak_idx = np.argmax(mag)
        peak_freq = peak_idx * sample_rate / N
        assert abs(peak_freq - freq) < sample_rate / N + 3

    def test_amplitude(self):
        """幅度正确性"""
        signal = sine_wave(100, 1000, 1.0, amplitude=2.0)
        assert np.isclose(np.max(signal), 2.0, atol=0.1)

    def test_duration(self):
        """持续时间"""
        sample_rate = 1000.0
        duration = 0.5
        signal = sine_wave(100, sample_rate, duration)
        assert len(signal) == int(sample_rate * duration)

    def test_phase(self):
        """相位"""
        signal_0 = sine_wave(100, 1000, 1.0, phase=0.0)
        signal_pi = sine_wave(100, 1000, 1.0, phase=np.pi)
        # 相位差 π 应该是反相
        assert np.isclose(signal_0[0], -signal_pi[0], atol=1e-10)


class TestCosineWave:
    """余弦波测试"""

    def test_starts_at_amplitude(self):
        """余弦波从幅度值开始"""
        signal = cosine_wave(100, 1000, 1.0, amplitude=3.0)
        assert np.isclose(signal[0], 3.0, atol=0.01)

    def test_orthogonal_to_sine(self):
        """正弦和余弦正交"""
        sample_rate = 1000.0
        duration = 1.0
        sin_sig = sine_wave(100, sample_rate, duration)
        cos_sig = cosine_wave(100, sample_rate, duration)

        # 内积应该接近 0
        dot = np.dot(sin_sig, cos_sig) / len(sin_sig)
        assert abs(dot) < 0.01


class TestCompositeSignal:
    """复合信号测试"""

    def test_multiple_frequencies(self):
        """多频率叠加"""
        sample_rate = 1024.0
        signal = composite_signal(
            [100, 200, 300], [1.0, 0.5, 0.25], sample_rate, 1.0
        )
        X = fft(signal)
        N_padded = len(X)  # FFT may pad to power of 2
        mag = magnitude_spectrum(X[:N_padded//2])

        # 验证 FFT 检测到的能量在正确频率附近
        for target_freq in [100, 200, 300]:
            idx = int(target_freq * N_padded / sample_rate)
            # 检查峰值附近有明显能量
            peak_nearby = np.max(mag[max(0, idx-2):idx+3])
            assert peak_nearby > 0.01 * np.max(mag)

    def test_default_phases(self):
        """默认相位为 0"""
        signal = composite_signal([100], [1.0], 1000, 1.0)
        expected = sine_wave(100, 1000, 1.0)
        assert np.allclose(signal, expected, atol=1e-10)


class TestSquareWave:
    """方波测试"""

    def test_values(self):
        """只有 +1 和 -1"""
        signal = square_wave(10, 1000, 0.1)
        unique = np.unique(signal)
        assert set(unique).issubset({1.0, -1.0})

    def test_duty_cycle(self):
        """占空比"""
        signal = square_wave(10, 1000, 0.5, duty_cycle=0.25)
        # 25% 占空比
        ratio = np.mean(signal > 0)
        assert abs(ratio - 0.25) < 0.05


class TestOtherSignals:
    """其他信号测试"""

    def test_sawtooth_range(self):
        """锯齿波范围 [-1, 1]"""
        signal = sawtooth_wave(100, 1000, 0.1)
        assert np.min(signal) >= -1.0 - 1e-10
        assert np.max(signal) <= 1.0 + 1e-10

    def test_triangle_range(self):
        """三角波范围 [-1, 1]"""
        signal = triangle_wave(100, 1000, 0.1)
        assert np.min(signal) >= -1.0 - 1e-10
        assert np.max(signal) <= 1.0 + 1e-10

    def test_white_noise_randomness(self):
        """白噪声的统计特性"""
        signal = white_noise(1000, 10.0)
        assert len(signal) == 10000
        # 均值接近 0
        assert abs(np.mean(signal)) < 0.1
        # 标准差接近 1
        assert abs(np.std(signal) - 1.0) < 0.1

    def test_chirp_sweep(self):
        """Chirp 信号频率扫描"""
        signal = chirp_signal(10, 100, 1000, 1.0)
        assert len(signal) == 1000

    def test_impulse_train(self):
        """脉冲序列"""
        signal = impulse_train(10, 100)
        assert signal[0] == 1.0
        assert signal[10] == 1.0
        assert signal[5] == 0.0

    def test_gaussian_pulse(self):
        """高斯脉冲"""
        signal = gaussian_pulse(0.5, 0.1, 1000, 1.0)
        # 在中心处最大
        center_idx = 500
        assert np.argmax(signal) == center_idx
        # 形状对称
        assert np.isclose(signal[400], signal[600], atol=1e-10)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
