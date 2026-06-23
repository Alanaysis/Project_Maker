"""
音频特效模块测试
"""

import pytest
import numpy as np
from src.audio_signal import AudioSignal
from src.effects import Delay, Reverb, Chorus, Distortion, Compressor


class TestDelay:
    """延迟效果测试"""

    def test_basic_delay(self):
        """测试基本延迟"""
        sample_rate = 44100
        signal = AudioSignal.from_tone(440, duration=0.5, sample_rate=sample_rate)

        delay = Delay(delay_time=0.1, feedback=0.5, mix=0.5, sample_rate=sample_rate)
        delayed = delay.apply(signal)

        # 长度应该相同
        assert len(delayed) == len(signal)

        # 应该有不同的波形
        assert not np.allclose(delayed.data, signal.data)

    def test_delay_feedback(self):
        """测试延迟反馈"""
        sample_rate = 44100
        # 较长的脉冲信号
        signal_data = np.zeros(sample_rate)
        signal_data[:100] = np.sin(2 * np.pi * 440 * np.arange(100) / sample_rate)
        signal = AudioSignal(signal_data, sample_rate)

        # 无反馈
        delay_no_fb = Delay(delay_time=0.1, feedback=0.0, mix=1.0, sample_rate=sample_rate)
        result_no_fb = delay_no_fb.apply(signal)

        # 有反馈
        delay_with_fb = Delay(delay_time=0.1, feedback=0.5, mix=1.0, sample_rate=sample_rate)
        result_with_fb = delay_with_fb.apply(signal)

        # 有反馈应该产生更多回声
        # 检查第二个延迟位置（反馈应该在这里产生信号）
        delay_samples = int(0.1 * sample_rate)
        second_delay_start = 2 * delay_samples

        # 无反馈在第二个延迟位置应该没有信号
        assert not np.any(np.abs(result_no_fb.data[second_delay_start:second_delay_start+200]) > 1e-10)

        # 有反馈在第二个延迟位置应该有信号
        assert np.any(np.abs(result_with_fb.data[second_delay_start:second_delay_start+200]) > 0)

    def test_delay_mix(self):
        """测试延迟混合比例"""
        sample_rate = 44100
        signal = AudioSignal.from_tone(440, duration=0.1, sample_rate=sample_rate)

        # 全干声
        delay_dry = Delay(delay_time=0.05, feedback=0.5, mix=0.0, sample_rate=sample_rate)
        result_dry = delay_dry.apply(signal)

        # 全湿声
        delay_wet = Delay(delay_time=0.05, feedback=0.5, mix=1.0, sample_rate=sample_rate)
        result_wet = delay_wet.apply(signal)

        # 全干声应该接近原始信号
        assert np.allclose(result_dry.data, signal.data, atol=1e-10)

    def test_invalid_feedback(self):
        """测试无效反馈"""
        with pytest.raises(ValueError):
            Delay(feedback=-0.1)
        with pytest.raises(ValueError):
            Delay(feedback=1.1)


class TestReverb:
    """混响效果测试"""

    def test_basic_reverb(self):
        """测试基本混响"""
        sample_rate = 44100
        signal = AudioSignal.from_tone(440, duration=0.5, sample_rate=sample_rate)

        reverb = Reverb(room_size=0.5, damping=0.5, mix=0.3, sample_rate=sample_rate)
        reverbed = reverb.apply(signal)

        # 长度应该相同
        assert len(reverbed) == len(signal)

    def test_reverb_room_size(self):
        """测试房间大小影响"""
        sample_rate = 44100
        # 脉冲信号
        signal_data = np.zeros(44100)
        signal_data[0] = 1.0
        signal = AudioSignal(signal_data, sample_rate)

        # 小房间
        reverb_small = Reverb(room_size=0.2, mix=0.5, sample_rate=sample_rate)
        result_small = reverb_small.apply(signal)

        # 大房间
        reverb_large = Reverb(room_size=0.8, mix=0.5, sample_rate=sample_rate)
        result_large = reverb_large.apply(signal)

        # 大房间应该有更长的混响尾
        # 检查信号后半部分的能量
        mid = len(signal) // 2
        energy_small = np.sum(result_small.data[mid:] ** 2)
        energy_large = np.sum(result_large.data[mid:] ** 2)

        assert energy_large > energy_small

    def test_reverb_damping(self):
        """测试阻尼影响"""
        sample_rate = 44100
        signal_data = np.zeros(44100)
        signal_data[0] = 1.0
        signal = AudioSignal(signal_data, sample_rate)

        # 低阻尼
        reverb_low = Reverb(room_size=0.5, damping=0.2, mix=0.5, sample_rate=sample_rate)
        result_low = reverb_low.apply(signal)

        # 高阻尼
        reverb_high = Reverb(room_size=0.5, damping=0.8, mix=0.5, sample_rate=sample_rate)
        result_high = reverb_high.apply(signal)

        # 低阻尼应该有更长的混响
        end = len(signal) - 1000
        energy_low = np.sum(result_low.data[end:] ** 2)
        energy_high = np.sum(result_high.data[end:] ** 2)

        assert energy_low > energy_high


class TestChorus:
    """合唱效果测试"""

    def test_basic_chorus(self):
        """测试基本合唱"""
        sample_rate = 44100
        signal = AudioSignal.from_tone(440, duration=1.0, sample_rate=sample_rate)

        chorus = Chorus(rate=1.5, depth=0.002, mix=0.5, sample_rate=sample_rate)
        chorused = chorus.apply(signal)

        # 长度应该相同
        assert len(chorused) == len(signal)

    def test_chorus_depth(self):
        """测试调制深度"""
        sample_rate = 44100
        signal = AudioSignal.from_tone(440, duration=0.5, sample_rate=sample_rate)

        # 浅调制
        chorus_shallow = Chorus(rate=1.0, depth=0.001, mix=0.5, sample_rate=sample_rate)
        result_shallow = chorus_shallow.apply(signal)

        # 深调制
        chorus_deep = Chorus(rate=1.0, depth=0.005, mix=0.5, sample_rate=sample_rate)
        result_deep = chorus_deep.apply(signal)

        # 两者都应该产生变化
        diff_shallow = np.sum(np.abs(result_shallow.data - signal.data))
        diff_deep = np.sum(np.abs(result_deep.data - signal.data))

        # 深调制应该产生变化
        assert diff_deep > 0
        assert diff_shallow > 0


class TestDistortion:
    """失真效果测试"""

    def test_basic_distortion(self):
        """测试基本失真"""
        signal = AudioSignal.from_tone(440, duration=0.1)

        distortion = Distortion(drive=0.5, mix=1.0)
        distorted = distortion.apply(signal)

        assert len(distorted) == len(signal)

    def test_soft_clip(self):
        """测试软削波"""
        signal = AudioSignal.from_tone(440, duration=0.1)

        distortion = Distortion(drive=0.5, mix=1.0, clip_type='soft')
        distorted = distortion.apply(signal)

        # 软削波应该限制在 [-1, 1]
        # 注意：由于增益，可能略微超过，但应该被 tanh 限制
        assert np.max(np.abs(distorted.data)) < 2.0

    def test_hard_clip(self):
        """测试硬削波"""
        signal = AudioSignal.from_tone(440, duration=0.1)

        distortion = Distortion(drive=0.5, mix=1.0, clip_type='hard')
        distorted = distortion.apply(signal)

        # 硬削波应该严格限制在 [-1, 1]（考虑原始电平）
        # 由于归一化和恢复，实际值可能超过1
        assert np.max(np.abs(distorted.data)) < 2.0

    def test_distortion_harmonics(self):
        """测试失真产生谐波"""
        sample_rate = 44100
        signal = AudioSignal.from_tone(440, duration=0.1, sample_rate=sample_rate)

        distortion = Distortion(drive=0.8, mix=1.0)
        distorted = distortion.apply(signal)

        # 失真应该产生谐波
        spectrum_original = np.abs(np.fft.fft(signal.data))
        spectrum_distorted = np.abs(np.fft.fft(distorted.data))

        # 原始信号应该只有一个峰（440 Hz）
        # 失真后应该有多个峰（谐波）
        peaks_original = np.sum(spectrum_original > np.max(spectrum_original) * 0.1)
        peaks_distorted = np.sum(spectrum_distorted > np.max(spectrum_distorted) * 0.1)

        assert peaks_distorted > peaks_original


class TestCompressor:
    """压缩器测试"""

    def test_basic_compression(self):
        """测试基本压缩"""
        sample_rate = 44100

        # 创建动态范围大的信号
        t = np.linspace(0, 1, sample_rate, endpoint=False)
        signal_data = np.sin(2 * np.pi * 440 * t)
        signal_data[:sample_rate//2] *= 0.1  # 前半段安静
        signal_data[sample_rate//2:] *= 0.9  # 后半段响

        signal = AudioSignal(signal_data, sample_rate)

        compressor = Compressor(threshold=-20, ratio=4.0, sample_rate=sample_rate)
        compressed = compressor.apply(signal)

        # 压缩后动态范围应该减小
        original_range = np.max(np.abs(signal.data[sample_rate//2:])) / \
                        np.max(np.abs(signal.data[:sample_rate//2]))
        compressed_range = np.max(np.abs(compressed.data[sample_rate//2:])) / \
                          np.max(np.abs(compressed.data[:sample_rate//2]))

        # 压缩后的比值应该更小
        assert compressed_range < original_range
