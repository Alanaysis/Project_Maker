"""
音频信号模块测试
"""

import pytest
import numpy as np
import tempfile
import os
from src.audio_signal import AudioSignal


class TestAudioSignal:
    """AudioSignal 类测试"""

    def test_basic_creation(self):
        """测试基本创建"""
        data = np.sin(np.linspace(0, 2 * np.pi * 440, 44100))
        signal = AudioSignal(data, sample_rate=44100)

        assert signal.sample_rate == 44100
        assert signal.channels == 1
        assert len(signal) == 44100
        assert abs(signal.duration - 1.0) < 0.01

    def test_invalid_sample_rate(self):
        """测试无效采样率"""
        data = np.zeros(100)
        with pytest.raises(ValueError):
            AudioSignal(data, sample_rate=0)
        with pytest.raises(ValueError):
            AudioSignal(data, sample_rate=-1)

    def test_invalid_channels(self):
        """测试无效通道数"""
        data = np.zeros(100)
        with pytest.raises(ValueError):
            AudioSignal(data, channels=0)
        with pytest.raises(ValueError):
            AudioSignal(data, channels=3)

    def test_from_tone(self):
        """测试生成音调"""
        signal = AudioSignal.from_tone(440, duration=1.0, sample_rate=44100)

        assert signal.sample_rate == 44100
        assert abs(signal.duration - 1.0) < 0.01
        assert len(signal) == 44100

        # 应该是正弦波
        t = np.linspace(0, 1.0, 44100, endpoint=False)
        expected = np.sin(2 * np.pi * 440 * t)
        assert np.allclose(signal.data, expected, atol=1e-10)

    def test_from_tone_amplitude(self):
        """测试音调振幅"""
        signal = AudioSignal.from_tone(440, duration=0.1, amplitude=0.5)
        assert np.max(np.abs(signal.data)) <= 0.5 + 1e-10

    def test_from_noise(self):
        """测试生成噪声"""
        signal = AudioSignal.from_noise(duration=1.0, sample_rate=44100)

        assert signal.sample_rate == 44100
        assert len(signal) == 44100

        # 应该有非零值
        assert np.any(signal.data != 0)

    def test_nyquist_freq(self):
        """测试奈奎斯特频率"""
        signal = AudioSignal(np.zeros(100), sample_rate=44100)
        assert signal.nyquist_freq == 22050.0

    def test_get_spectrum(self):
        """测试获取频谱"""
        # 创建 440 Hz 正弦波
        signal = AudioSignal.from_tone(440, duration=0.1, sample_rate=44100)
        freqs, magnitude = signal.get_spectrum()

        # 找到峰值频率
        peak_idx = np.argmax(magnitude)
        peak_freq = freqs[peak_idx]

        # 应该在 440 Hz 附近
        assert abs(peak_freq - 440) < 10  # 允许一定误差

    def test_normalize(self):
        """测试归一化"""
        data = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        signal = AudioSignal(data, sample_rate=44100)
        normalized = signal.normalize(target_level=0.9)

        assert np.max(np.abs(normalized.data)) <= 0.9 + 1e-10

    def test_normalize_silent(self):
        """测试静音归一化"""
        data = np.zeros(100)
        signal = AudioSignal(data, sample_rate=44100)
        normalized = signal.normalize()

        # 静音信号归一化后仍为静音
        assert np.all(normalized.data == 0)

    def test_mix(self):
        """测试混合"""
        signal1 = AudioSignal(np.ones(100), sample_rate=44100)
        signal2 = AudioSignal(np.zeros(100), sample_rate=44100)

        mixed = signal1.mix(signal2, ratio=0.5)
        assert np.allclose(mixed.data, 0.5)

    def test_mix_different_length(self):
        """测试不同长度混合"""
        signal1 = AudioSignal(np.ones(100), sample_rate=44100)
        signal2 = AudioSignal(np.zeros(50), sample_rate=44100)

        mixed = signal1.mix(signal2, ratio=0.5)
        assert len(mixed) == 50

    def test_mix_sample_rate_mismatch(self):
        """测试采样率不匹配"""
        signal1 = AudioSignal(np.ones(100), sample_rate=44100)
        signal2 = AudioSignal(np.zeros(100), sample_rate=48000)

        with pytest.raises(ValueError):
            signal1.mix(signal2)

    def test_apply_gain(self):
        """测试增益"""
        data = np.ones(100)
        signal = AudioSignal(data, sample_rate=44100)

        # 增加 6 dB
        amplified = signal.apply_gain(6.0)
        expected_gain = 10 ** (6.0 / 20.0)
        assert np.allclose(amplified.data, expected_gain)

    def test_apply_gain_negative(self):
        """测试负增益（衰减）"""
        data = np.ones(100)
        signal = AudioSignal(data, sample_rate=44100)

        # 衰减 6 dB
        attenuated = signal.apply_gain(-6.0)
        expected_gain = 10 ** (-6.0 / 20.0)
        assert np.allclose(attenuated.data, expected_gain)

    def test_trim(self):
        """测试裁剪"""
        data = np.arange(44100, dtype=float)
        signal = AudioSignal(data, sample_rate=44100)

        # 裁剪前0.5秒
        trimmed = signal.trim(start=0.0, end=0.5)
        assert abs(trimmed.duration - 0.5) < 0.01

    def test_trim_default(self):
        """测试默认裁剪"""
        data = np.arange(44100, dtype=float)
        signal = AudioSignal(data, sample_rate=44100)

        # 裁剪从0.5秒到末尾
        trimmed = signal.trim(start=0.5)
        assert abs(trimmed.duration - 0.5) < 0.01

    def test_wav_roundtrip(self):
        """测试 WAV 文件读写"""
        # 创建测试信号
        signal = AudioSignal.from_tone(440, duration=0.1, sample_rate=44100)

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            filepath = f.name

        try:
            # 写入
            signal.to_wav(filepath)

            # 读取
            loaded = AudioSignal.from_wav(filepath)

            # 检查
            assert loaded.sample_rate == 44100
            assert abs(len(loaded) - len(signal)) < 10  # 允许小误差
        finally:
            os.unlink(filepath)

    def test_add_operator(self):
        """测试加法运算符"""
        signal1 = AudioSignal(np.ones(100), sample_rate=44100)
        signal2 = AudioSignal(np.ones(100), sample_rate=44100)

        combined = signal1 + signal2
        assert np.allclose(combined.data, 1.0)

    def test_repr(self):
        """测试字符串表示"""
        signal = AudioSignal.from_tone(440, duration=1.0)
        repr_str = repr(signal)

        assert "AudioSignal" in repr_str
        assert "44100Hz" in repr_str
        assert "1.00s" in repr_str
