"""
音频采样模块测试
================

测试音频采样、量化、重采样等功能。
"""

import numpy as np
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.audio_sampling import (
    AudioSampler,
    resample_audio,
    demonstrate_audio_quantization,
    generate_test_tone,
)


class TestAudioSampler:
    """音频采样器测试"""

    def test_basic_creation(self):
        """测试基本创建"""
        sampler = AudioSampler(fs=44100, bits=16, channels=2)
        assert sampler.fs == 44100
        assert sampler.bits == 16
        assert sampler.channels == 2

    def test_from_preset(self):
        """测试从预设创建"""
        sampler = AudioSampler.from_preset('cd')
        assert sampler.fs == 44100
        assert sampler.channels == 2

        sampler = AudioSampler.from_preset('telephone')
        assert sampler.fs == 8000
        assert sampler.channels == 1

    def test_invalid_preset(self):
        """测试无效预设"""
        with pytest.raises(ValueError):
            AudioSampler.from_preset('invalid')

    def test_sample(self):
        """测试采样"""
        sampler = AudioSampler(fs=100, bits=16)
        t = np.linspace(0, 1, 1001)
        signal = np.sin(2 * np.pi * 10 * t)

        t_sampled, samples = sampler.sample(signal, t)

        # 采样点数约为 fs * duration，由于步长取整可能有微小偏差
        assert abs(len(t_sampled) - 100) <= 2
        assert len(t_sampled) == len(samples)

    def test_quantize(self):
        """测试量化"""
        sampler = AudioSampler(fs=44100, bits=8)
        samples = np.sin(np.linspace(0, 2 * np.pi, 1000))

        quantized, indices = sampler.quantize(samples)

        assert len(quantized) == len(samples)
        assert len(indices) == len(samples)

    def test_encode_decode(self):
        """测试编码解码"""
        sampler = AudioSampler(fs=44100, bits=16)
        samples = np.sin(np.linspace(0, 2 * np.pi, 100))

        pcm = sampler.encode(samples)
        decoded = sampler.decode(pcm)

        # 编码解码应近似一致
        assert len(decoded) == len(samples)

    def test_nyquist_frequency(self):
        """测试奈奎斯特频率"""
        sampler = AudioSampler(fs=44100)
        assert sampler.nyquist_frequency == 22050

    def test_bit_rate(self):
        """测试比特率"""
        sampler = AudioSampler(fs=44100, bits=16, channels=2)
        expected = 44100 * 16 * 2
        assert sampler.bit_rate == expected

    def test_info(self):
        """测试信息获取"""
        sampler = AudioSampler(fs=44100, bits=16, channels=2)
        info = sampler.info

        assert "采样频率" in info
        assert "量化位数" in info
        assert "声道数" in info
        assert "比特率" in info
        assert "奈奎斯特频率" in info

    def test_invalid_fs(self):
        """测试无效采样率"""
        with pytest.raises(ValueError):
            AudioSampler(fs=0)
        with pytest.raises(ValueError):
            AudioSampler(fs=-100)

    def test_invalid_bits(self):
        """测试无效量化位数"""
        with pytest.raises(ValueError):
            AudioSampler(fs=44100, bits=0)

    def test_invalid_channels(self):
        """测试无效声道数"""
        with pytest.raises(ValueError):
            AudioSampler(fs=44100, channels=3)


class TestResampleAudio:
    """音频重采样测试"""

    def test_same_rate(self):
        """测试相同采样率"""
        samples = np.sin(np.linspace(0, 2 * np.pi, 100))
        resampled, fs = resample_audio(samples, 44100, 44100)

        assert np.allclose(samples, resampled, atol=1e-6)
        assert fs == 44100

    def test_downsample(self):
        """测试降采样"""
        samples = np.sin(np.linspace(0, 2 * np.pi, 44100))
        resampled, fs = resample_audio(samples, 44100, 22050)

        assert len(resampled) == 22050
        assert fs == 22050

    def test_upsample(self):
        """测试上采样"""
        samples = np.sin(np.linspace(0, 2 * np.pi, 22050))
        resampled, fs = resample_audio(samples, 22050, 44100)

        assert len(resampled) == 44100
        assert fs == 44100

    def test_invalid_fs(self):
        """测试无效采样率"""
        samples = np.ones(100)

        with pytest.raises(ValueError):
            resample_audio(samples, 0, 44100)
        with pytest.raises(ValueError):
            resample_audio(samples, 44100, 0)


class TestDemonstrateAudioQuantization:
    """音频量化演示测试"""

    def test_basic(self):
        """测试基本演示"""
        result = demonstrate_audio_quantization(duration=0.1, fs=1000, freq=100)

        assert "t" in result
        assert "signal" in result
        assert "quantization_results" in result

    def test_quantization_results(self):
        """测试量化结果"""
        result = demonstrate_audio_quantization(duration=0.1, fs=1000, freq=100)
        qr = result["quantization_results"]

        assert "4bit" in qr
        assert "8bit" in qr
        assert "12bit" in qr
        assert "16bit" in qr
        assert "24bit" in qr

    def test_sqnr_increases_with_bits(self):
        """测试 SQNR 随位数增加"""
        result = demonstrate_audio_quantization(duration=0.1, fs=1000, freq=100)
        qr = result["quantization_results"]

        sqnr_values = [qr[f"{b}bit"]["sqnr"] for b in [4, 8, 12, 16, 24]]

        # SQNR 应随位数增加
        for i in range(1, len(sqnr_values)):
            assert sqnr_values[i] > sqnr_values[i - 1]


class TestGenerateTestTone:
    """测试音调生成测试"""

    def test_basic(self):
        """测试基本生成"""
        t, signal = generate_test_tone(440, 1.0, 44100)

        assert len(t) == 44100
        assert len(signal) == 44100

    def test_frequency(self):
        """测试频率正确性"""
        freq = 440
        fs = 44100
        duration = 0.1

        t, signal = generate_test_tone(freq, duration, fs)

        # 验证频率
        spectrum = np.fft.fft(signal)
        freqs = np.fft.fftfreq(len(signal), 1.0 / fs)
        peak_idx = np.argmax(np.abs(spectrum[1:len(spectrum)//2])) + 1
        peak_freq = freqs[peak_idx]

        assert np.isclose(peak_freq, freq, atol=fs / len(signal))

    def test_amplitude(self):
        """测试幅度"""
        t, signal = generate_test_tone(440, 1.0, 44100, amplitude=0.5)

        assert np.max(np.abs(signal)) <= 0.5 + 1e-10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
