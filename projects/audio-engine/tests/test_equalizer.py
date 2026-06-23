"""
均衡器模块测试
"""

import pytest
import numpy as np
from src.audio_signal import AudioSignal
from src.equalizer import Equalizer, GraphicEqualizer, EQBand


class TestEQBand:
    """EQBand 类测试"""

    def test_basic_band(self):
        """测试基本频段"""
        band = EQBand(frequency=1000, gain_db=6.0, q_factor=2.0)

        assert band.frequency == 1000
        assert band.gain_db == 6.0
        assert band.q_factor == 2.0

    def test_bandwidth(self):
        """测试带宽计算"""
        band = EQBand(frequency=1000, q_factor=2.0)
        assert band.bandwidth == 500  # 1000 / 2

    def test_gain_linear(self):
        """测试线性增益"""
        band = EQBand(frequency=1000, gain_db=6.0)
        expected = 10 ** (6.0 / 20.0)
        assert abs(band.gain_linear - expected) < 1e-10

    def test_negative_gain(self):
        """测试负增益"""
        band = EQBand(frequency=1000, gain_db=-6.0)
        expected = 10 ** (-6.0 / 20.0)
        assert abs(band.gain_linear - expected) < 1e-10


class TestEqualizer:
    """参数均衡器测试"""

    def test_basic_equalization(self):
        """测试基本均衡"""
        sample_rate = 44100
        signal = AudioSignal.from_tone(440, duration=0.1, sample_rate=sample_rate)

        eq = Equalizer(sample_rate=sample_rate)
        eq.add_band(440, gain_db=6.0, q_factor=2.0)

        equalized = eq.apply(signal)

        # 应该产生输出
        assert len(equalized) == len(signal)

    def test_no_bands(self):
        """测试无频段"""
        sample_rate = 44100
        signal = AudioSignal.from_tone(440, duration=0.1, sample_rate=sample_rate)

        eq = Equalizer(sample_rate=sample_rate)
        equalized = eq.apply(signal)

        # 无频段应该返回原始信号
        assert np.allclose(equalized.data, signal.data)

    def test_boost_frequency(self):
        """测试提升特定频率"""
        sample_rate = 44100
        t = np.linspace(0, 0.5, sample_rate // 2, endpoint=False)
        # 包含两个频率
        signal_data = np.sin(2 * np.pi * 440 * t) + np.sin(2 * np.pi * 1000 * t)
        signal = AudioSignal(signal_data, sample_rate)

        eq = Equalizer(sample_rate=sample_rate)
        eq.add_band(440, gain_db=6.0, q_factor=2.0)  # 提升 440 Hz

        equalized = eq.apply(signal)

        # 440 Hz 应该被提升
        spectrum_orig = np.abs(np.fft.fft(signal.data))
        spectrum_eq = np.abs(np.fft.fft(equalized.data))
        freqs = np.fft.fftfreq(len(signal.data), 1.0 / sample_rate)

        idx_440 = np.argmin(np.abs(freqs - 440))
        idx_1000 = np.argmin(np.abs(freqs - 1000))

        # 440 Hz 的增益应该比 1000 Hz 大
        gain_440 = spectrum_eq[idx_440] / spectrum_orig[idx_440]
        gain_1000 = spectrum_eq[idx_1000] / spectrum_orig[idx_1000]

        assert gain_440 > gain_1000

    def test_cut_frequency(self):
        """测试衰减特定频率"""
        sample_rate = 44100
        t = np.linspace(0, 0.5, sample_rate // 2, endpoint=False)
        signal_data = np.sin(2 * np.pi * 440 * t) + np.sin(2 * np.pi * 1000 * t)
        signal = AudioSignal(signal_data, sample_rate)

        eq = Equalizer(sample_rate=sample_rate)
        eq.add_band(1000, gain_db=-6.0, q_factor=2.0)  # 衰减 1000 Hz

        equalized = eq.apply(signal)

        spectrum_orig = np.abs(np.fft.fft(signal.data))
        spectrum_eq = np.abs(np.fft.fft(equalized.data))
        freqs = np.fft.fftfreq(len(signal.data), 1.0 / sample_rate)

        idx_1000 = np.argmin(np.abs(freqs - 1000))
        gain_1000 = spectrum_eq[idx_1000] / spectrum_orig[idx_1000]

        # 应该衰减
        assert gain_1000 < 1.0

    def test_multiple_bands(self):
        """测试多频段"""
        sample_rate = 44100
        signal = AudioSignal.from_tone(440, duration=0.1, sample_rate=sample_rate)

        eq = Equalizer(sample_rate=sample_rate)
        eq.add_band(100, gain_db=3.0, q_factor=1.0)
        eq.add_band(440, gain_db=6.0, q_factor=2.0)
        eq.add_band(8000, gain_db=-3.0, q_factor=1.0)

        equalized = eq.apply(signal)

        # 应该有三个频段
        assert len(eq.bands) == 3
        assert len(equalized) == len(signal)

    def test_remove_band(self):
        """测试移除频段"""
        eq = Equalizer()
        eq.add_band(440, gain_db=6.0)
        eq.add_band(1000, gain_db=-3.0)

        assert len(eq.bands) == 2

        eq.remove_band(0)
        assert len(eq.bands) == 1
        assert eq.bands[0].frequency == 1000

    def test_set_band_gain(self):
        """测试设置频段增益"""
        eq = Equalizer()
        idx = eq.add_band(440, gain_db=0.0)

        eq.set_band_gain(idx, 6.0)
        assert eq.bands[idx].gain_db == 6.0

    def test_set_band_frequency(self):
        """测试设置频段频率"""
        eq = Equalizer()
        idx = eq.add_band(440, gain_db=0.0)

        eq.set_band_frequency(idx, 880)
        assert eq.bands[idx].frequency == 880

    def test_set_band_q(self):
        """测试设置频段 Q 值"""
        eq = Equalizer()
        idx = eq.add_band(440, q_factor=1.0)

        eq.set_band_q(idx, 2.0)
        assert eq.bands[idx].q_factor == 2.0

    def test_frequency_response(self):
        """测试频率响应"""
        eq = Equalizer(sample_rate=44100)
        eq.add_band(1000, gain_db=6.0, q_factor=2.0)

        freqs, response = eq.get_frequency_response(1024)

        # 在 1000 Hz 附近应该有提升
        idx_1000 = np.argmin(np.abs(freqs - 1000))
        assert response[idx_1000] > 1.0

    def test_band_management(self):
        """测试频段管理"""
        eq = Equalizer()

        # 添加频段
        idx1 = eq.add_band(100, gain_db=3.0)
        idx2 = eq.add_band(1000, gain_db=-3.0)
        idx3 = eq.add_band(8000, gain_db=6.0)

        assert len(eq.bands) == 3
        assert idx1 == 0
        assert idx2 == 1
        assert idx3 == 2

        # 移除中间频段
        eq.remove_band(1)
        assert len(eq.bands) == 2
        assert eq.bands[0].frequency == 100
        assert eq.bands[1].frequency == 8000


class TestGraphicEqualizer:
    """图示均衡器测试"""

    def test_basic_creation(self):
        """测试基本创建"""
        geq = GraphicEqualizer(sample_rate=44100)

        # 应该有 10 个标准频段
        assert len(geq.frequencies) == 10
        assert len(geq.gains) == 10

        # 所有增益初始为 0
        assert all(g == 0.0 for g in geq.gains)

    def test_custom_frequencies(self):
        """测试自定义频率"""
        freqs = [100, 500, 2000, 8000]
        geq = GraphicEqualizer(frequencies=freqs, sample_rate=44100)

        assert len(geq.frequencies) == 4
        assert geq.frequencies == freqs

    def test_set_gain(self):
        """测试设置增益"""
        geq = GraphicEqualizer(sample_rate=44100)

        geq.set_gain(0, 3.0)  # 31.5 Hz
        geq.set_gain(5, -6.0)  # 1000 Hz

        assert geq.gains[0] == 3.0
        assert geq.gains[5] == -6.0

    def test_set_gains(self):
        """测试批量设置增益"""
        geq = GraphicEqualizer(sample_rate=44100)

        gains = [3, 2, 0, -1, -2, 0, 1, 2, 3, 4]
        geq.set_gains(gains)

        assert geq.get_gains() == gains

    def test_set_gains_wrong_length(self):
        """测试错误长度的增益列表"""
        geq = GraphicEqualizer(sample_rate=44100)

        with pytest.raises(ValueError):
            geq.set_gains([1, 2, 3])  # 应该是 10 个

    def test_reset(self):
        """测试重置"""
        geq = GraphicEqualizer(sample_rate=44100)

        geq.set_gains([3, 2, 0, -1, -2, 0, 1, 2, 3, 4])
        geq.reset()

        assert all(g == 0.0 for g in geq.gains)

    def test_apply(self):
        """测试应用均衡"""
        sample_rate = 44100
        signal = AudioSignal.from_tone(440, duration=0.1, sample_rate=sample_rate)

        geq = GraphicEqualizer(sample_rate=sample_rate)
        geq.set_gain(5, 6.0)  # 提升 1000 Hz

        equalized = geq.apply(signal)

        assert len(equalized) == len(signal)

    def test_frequency_response(self):
        """测试频率响应"""
        geq = GraphicEqualizer(sample_rate=44100)
        geq.set_gains([3, 2, 0, -1, -2, 0, 1, 2, 3, 4])

        freqs, response = geq.get_frequency_response(1024)

        # 应该有输出
        assert len(freqs) > 0
        assert len(response) > 0

    def test_standard_frequencies(self):
        """测试标准频率"""
        expected = [31.5, 63, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]
        assert GraphicEqualizer.STANDARD_FREQUENCIES == expected
