"""
FFT 模块测试
"""

import pytest
import numpy as np
from src.fft import FFT, IFFT


class TestFFT:
    """FFT 变换测试"""

    def test_basic_transform(self):
        """测试基本 FFT 变换"""
        # 创建简单的正弦信号
        N = 64
        t = np.linspace(0, 1, N, endpoint=False)
        freq = 5  # 5 Hz
        signal = np.sin(2 * np.pi * freq * t)

        # FFT 变换
        spectrum = FFT.transform(signal)

        # 检查长度
        assert len(spectrum) == N

        # 检查对称性（实数信号的 FFT 具有共轭对称性）
        assert np.allclose(spectrum[1:N//2], np.conj(spectrum[N-1:N//2:-1]))

    def test_power_of_two(self):
        """测试2的幂次长度"""
        for n in [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024]:
            signal = np.random.randn(n)
            spectrum = FFT.transform(signal)
            assert len(spectrum) == n

    def test_non_power_of_two_padding(self):
        """测试非2的幂次长度（自动填充）"""
        signal = np.random.randn(100)  # 不是2的幂次
        spectrum = FFT.transform(signal)
        # 应该填充到128
        assert len(spectrum) == 128

    def test_single_frequency_detection(self):
        """测试单频率检测"""
        N = 256
        sample_rate = 256
        freq = 32  # 32 Hz

        t = np.linspace(0, 1, N, endpoint=False)
        signal = np.sin(2 * np.pi * freq * t)

        spectrum = FFT.transform(signal)
        magnitude = np.abs(spectrum) * 2.0 / N

        # 找到最大幅度对应的频率
        freqs = np.fft.fftfreq(N, 1.0 / sample_rate)
        peak_idx = np.argmax(magnitude[:N//2])
        peak_freq = freqs[peak_idx]

        # 应该检测到32 Hz
        assert abs(peak_freq - freq) < sample_rate / N

    def test_magnitude_spectrum(self):
        """测试幅度谱计算"""
        N = 128
        signal = np.ones(N)  # DC 信号

        magnitude = FFT.magnitude_spectrum(signal)

        # DC 分量应该为1
        assert abs(magnitude[0] - 1.0) < 1e-10

        # 其他分量应该接近0
        assert np.all(magnitude[1:] < 1e-10)

    def test_power_spectrum(self):
        """测试功率谱计算"""
        N = 64
        signal = np.random.randn(N)

        power = FFT.power_spectrum(signal)

        # 功率谱应该是非负的
        assert np.all(power >= 0)

        # 长度应该是 N/2
        assert len(power) == N // 2

    def test_phase_spectrum(self):
        """测试相位谱计算"""
        N = 64
        signal = np.random.randn(N)

        phase = FFT.phase_spectrum(signal)

        # 相位应该在 [-π, π] 范围内
        assert np.all(phase >= -np.pi - 1e-10)
        assert np.all(phase <= np.pi + 1e-10)

    def test_empty_input(self):
        """测试空输入"""
        with pytest.raises(ValueError):
            FFT.transform(np.array([]))

    def test_invalid_input(self):
        """测试无效输入"""
        with pytest.raises(ValueError):
            FFT.transform([1, 2, 3])  # 不是 numpy 数组


class TestIFFT:
    """IFFT 变换测试"""

    def test_basic_transform(self):
        """测试基本 IFFT 变换"""
        # 创建频域信号
        N = 64
        spectrum = np.zeros(N, dtype=complex)
        spectrum[5] = N  # 放大 N 倍以抵消 IFFT 的 1/N 归一化

        # IFFT
        signal = IFFT.transform(spectrum)

        # 当只有一个频率分量为 N 时，IFFT 产生余弦波（幅度为1）
        n = np.arange(N)
        expected = np.cos(2 * np.pi * 5 * n / N)

        assert len(signal) == N
        assert np.allclose(np.real(signal), expected, atol=1e-10)

    def test_fft_ifft_roundtrip(self):
        """测试 FFT -> IFFT 往返变换"""
        signal = np.random.randn(128)

        # FFT -> IFFT
        spectrum = FFT.transform(signal)
        reconstructed = IFFT.transform_real(spectrum)

        # 应该恢复原始信号
        assert np.allclose(signal, reconstructed, atol=1e-10)

    def test_transform_real(self):
        """测试实数 IFFT"""
        spectrum = np.zeros(64, dtype=complex)
        spectrum[10] = 1.0
        spectrum[54] = 1.0  # 共轭对称

        signal = IFFT.transform_real(spectrum)

        # 应该是实数
        assert np.allclose(np.imag(signal), 0, atol=1e-10)

    def test_empty_input(self):
        """测试空输入"""
        with pytest.raises(ValueError):
            IFFT.transform(np.array([]))


class TestFFTFundamentals:
    """FFT 基础概念测试"""

    def test_linearity(self):
        """测试线性性质: FFT(a*x + b*y) = a*FFT(x) + b*FFT(y)"""
        N = 64
        x = np.random.randn(N)
        y = np.random.randn(N)
        a, b = 2.0, 3.0

        # 直接计算
        direct = FFT.transform(a * x + b * y)

        # 线性组合
        linear = a * FFT.transform(x) + b * FFT.transform(y)

        assert np.allclose(direct, linear, atol=1e-10)

    def test_parseval_theorem(self):
        """测试帕塞瓦尔定理: 时域能量 = 频域能量"""
        N = 128
        signal = np.random.randn(N)

        # 时域能量
        time_energy = np.sum(signal ** 2)

        # 频域能量
        spectrum = FFT.transform(signal)
        freq_energy = np.sum(np.abs(spectrum) ** 2) / N

        assert abs(time_energy - freq_energy) < 1e-10

    def test_time_shift_property(self):
        """测试时移性质: 时域延迟 = 频域相位旋转"""
        N = 128
        signal = np.random.randn(N)

        # 时移
        shift = 10
        shifted = np.roll(signal, shift)

        # 频域
        spectrum_original = FFT.transform(signal)
        spectrum_shifted = FFT.transform(shifted)

        # 相位差应该是线性的
        freqs = np.fft.fftfreq(N)
        expected_phase_diff = -2 * np.pi * freqs * shift

        phase_original = np.angle(spectrum_original)
        phase_shifted = np.angle(spectrum_shifted)
        phase_diff = phase_shifted - phase_original

        # 相位差应该接近期望值（考虑相位缠绕）
        assert np.allclose(np.exp(1j * phase_diff),
                          np.exp(1j * expected_phase_diff), atol=1e-10)

    def test_frequency_resolution(self):
        """测试频率分辨率"""
        N = 256
        sample_rate = 256  # 采样率 = 256 Hz
        freq_resolution = sample_rate / N  # = 1 Hz

        # 创建两个频率相差1Hz的信号
        t = np.linspace(0, 1, N, endpoint=False)
        signal = np.sin(2 * np.pi * 10 * t) + np.sin(2 * np.pi * 11 * t)

        spectrum = FFT.transform(signal)
        magnitude = np.abs(spectrum[:N//2])
        freqs = np.fft.fftfreq(N, 1.0 / sample_rate)[:N//2]

        # 应该能分辨出两个峰
        peaks = np.argsort(magnitude)[-2:]
        peak_freqs = freqs[peaks]

        assert abs(peak_freqs[0] - 10) < freq_resolution
        assert abs(peak_freqs[1] - 11) < freq_resolution
