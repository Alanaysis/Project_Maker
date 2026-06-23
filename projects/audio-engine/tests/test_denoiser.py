"""
降噪模块测试
"""

import pytest
import numpy as np
from src.audio_signal import AudioSignal
from src.denoiser import Denoiser


class TestDenoiser:
    """降噪器测试"""

    def test_basic_denoising(self):
        """测试基本降噪"""
        sample_rate = 44100

        # 创建纯净信号
        t = np.linspace(0, 1, sample_rate, endpoint=False)
        clean_signal = np.sin(2 * np.pi * 440 * t)

        # 添加噪声
        noise = np.random.randn(sample_rate) * 0.3
        noisy_signal = clean_signal + noise

        signal = AudioSignal(noisy_signal, sample_rate)

        # 降噪
        denoiser = Denoiser(noise_factor=1.5, spectral_floor=0.3, sample_rate=sample_rate)
        denoised = denoiser.apply(signal)

        # 降噪后应该产生输出
        assert len(denoised) == len(signal)
        # 输出不应该全为零
        assert np.any(denoised.data != 0)

    def test_estimate_noise(self):
        """测试噪声估计"""
        sample_rate = 44100

        # 创建纯噪声信号
        noise = np.random.randn(sample_rate) * 0.1
        signal = AudioSignal(noise, sample_rate)

        denoiser = Denoiser(sample_rate=sample_rate)

        # 噪声频谱应该未初始化
        assert denoiser.noise_spectrum is None

        # 估计噪声
        denoiser.estimate_noise(signal, noise_duration=0.5)

        # 噪声频谱应该已初始化
        assert denoiser.noise_spectrum is not None
        assert len(denoiser.noise_spectrum) > 0

    def test_estimate_noise_from_segment(self):
        """测试从片段估计噪声"""
        sample_rate = 44100

        # 创建噪声片段
        noise_segment = np.random.randn(sample_rate // 2) * 0.1

        denoiser = Denoiser(sample_rate=sample_rate)
        denoiser.estimate_noise_from_segment(noise_segment)

        assert denoiser.noise_spectrum is not None

    def test_auto_noise_estimation(self):
        """测试自动噪声估计"""
        sample_rate = 44100

        # 创建信号，开头是噪声
        noise = np.random.randn(1000) * 0.1
        signal_data = np.zeros(sample_rate)
        signal_data[:1000] = noise
        signal_data[1000:] = np.sin(2 * np.pi * 440 * np.arange(sample_rate - 1000) / sample_rate)

        signal = AudioSignal(signal_data, sample_rate)

        denoiser = Denoiser(sample_rate=sample_rate)

        # 应用时应该自动估计噪声
        denoised = denoiser.apply(signal)

        # 噪声频谱应该被估计
        assert denoiser.noise_spectrum is not None

    def test_simple_denoising(self):
        """测试简单降噪"""
        sample_rate = 44100

        # 创建信号
        t = np.linspace(0, 1, sample_rate, endpoint=False)
        clean = np.sin(2 * np.pi * 440 * t)
        noise = np.random.randn(sample_rate) * 0.2
        noisy = clean + noise

        signal = AudioSignal(noisy, sample_rate)

        denoiser = Denoiser(sample_rate=sample_rate)
        denoiser.estimate_noise(signal, noise_duration=0.1)

        denoised = denoiser.apply_simple(signal)

        # 应该产生输出
        assert len(denoised) == len(signal)

    def test_preserve_speech(self):
        """测试保留语音"""
        sample_rate = 44100

        # 创建语音-like 信号
        t = np.linspace(0, 1, sample_rate, endpoint=False)
        speech = np.sin(2 * np.pi * 300 * t) + 0.5 * np.sin(2 * np.pi * 600 * t)

        # 添加轻微噪声
        noise = np.random.randn(sample_rate) * 0.05
        noisy = speech + noise

        signal = AudioSignal(noisy, sample_rate)

        denoiser = Denoiser(noise_factor=1.5, spectral_floor=0.2, sample_rate=sample_rate)
        denoiser.estimate_noise(signal, noise_duration=0.1)

        denoised = denoiser.apply(signal)

        # 语音成分应该保留
        # 检查 300 Hz 分量
        spectrum = np.abs(np.fft.fft(denoised.data))
        freqs = np.fft.fftfreq(sample_rate, 1.0 / sample_rate)

        idx_300 = np.argmin(np.abs(freqs - 300))
        idx_noise = np.argmin(np.abs(freqs - 10000))  # 高频噪声

        # 300 Hz 应该比高频噪声大
        assert spectrum[idx_300] > spectrum[idx_noise]

    def test_noise_factor(self):
        """测试噪声因子影响"""
        sample_rate = 44100

        t = np.linspace(0, 1, sample_rate, endpoint=False)
        clean = np.sin(2 * np.pi * 440 * t)
        noise = np.random.randn(sample_rate) * 0.3
        noisy = clean + noise

        signal = AudioSignal(noisy, sample_rate)

        # 低噪声因子
        denoiser_low = Denoiser(noise_factor=1.0, sample_rate=sample_rate)
        denoiser_low.estimate_noise(signal, noise_duration=0.1)
        result_low = denoiser_low.apply(signal)

        # 高噪声因子
        denoiser_high = Denoiser(noise_factor=3.0, sample_rate=sample_rate)
        denoiser_high.estimate_noise(signal, noise_duration=0.1)
        result_high = denoiser_high.apply(signal)

        # 高因子应该去除更多噪声
        noise_energy_low = np.sum(result_low.data[:1000] ** 2)
        noise_energy_high = np.sum(result_high.data[:1000] ** 2)

        assert noise_energy_high < noise_energy_low

    def test_spectral_floor(self):
        """测试谱下限"""
        sample_rate = 44100

        t = np.linspace(0, 0.5, sample_rate // 2, endpoint=False)
        signal_data = np.sin(2 * np.pi * 440 * t) + np.random.randn(sample_rate // 2) * 0.1
        signal = AudioSignal(signal_data, sample_rate)

        # 低谱下限
        denoiser_low = Denoiser(noise_factor=2.0, spectral_floor=0.01, sample_rate=sample_rate)
        denoiser_low.estimate_noise(signal, noise_duration=0.1)
        result_low = denoiser_low.apply(signal)

        # 高谱下限
        denoiser_high = Denoiser(noise_factor=2.0, spectral_floor=0.5, sample_rate=sample_rate)
        denoiser_high.estimate_noise(signal, noise_duration=0.1)
        result_high = denoiser_high.apply(signal)

        # 高谱下限应该保留更多原始信号
        diff_low = np.sum(np.abs(result_low.data - signal.data))
        diff_high = np.sum(np.abs(result_high.data - signal.data))

        # 低谱下限应该有更大的变化（去除更多）
        assert diff_low > diff_high
