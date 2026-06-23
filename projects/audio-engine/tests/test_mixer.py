"""
混音器模块测试
"""

import pytest
import numpy as np
from src.audio_signal import AudioSignal
from src.mixer import Mixer, MixerTrack


class TestMixerTrack:
    """混音轨道测试"""

    def test_basic_track(self):
        """测试基本轨道"""
        signal = AudioSignal.from_tone(440, duration=0.1)
        track = MixerTrack(signal, name="Test", volume=0.8, pan=0.0)

        assert track.name == "Test"
        assert track.volume == 0.8
        assert track.pan == 0.0
        assert not track.mute
        assert not track.solo

    def test_stereo_panning(self):
        """测试声像定位"""
        signal = AudioSignal(np.ones(100), sample_rate=44100)

        # 完全左
        track_left = MixerTrack(signal, pan=-1.0)
        left, right = track_left.get_stereo_signal()
        assert np.allclose(left, 1.0)
        assert np.allclose(right, 0.0, atol=1e-10)

        # 完全右
        track_right = MixerTrack(signal, pan=1.0)
        left, right = track_right.get_stereo_signal()
        assert np.allclose(left, 0.0, atol=1e-10)
        assert np.allclose(right, 1.0)

        # 中间
        track_center = MixerTrack(signal, pan=0.0)
        left, right = track_center.get_stereo_signal()
        # 中间时左右应该相等
        assert np.allclose(left, right, atol=1e-10)

    def test_mute(self):
        """测试静音"""
        signal = AudioSignal(np.ones(100), sample_rate=44100)
        track = MixerTrack(signal, mute=True)

        left, right = track.get_stereo_signal()
        assert np.all(left == 0)
        assert np.all(right == 0)

    def test_volume(self):
        """测试音量控制"""
        signal = AudioSignal(np.ones(100), sample_rate=44100)

        track_half = MixerTrack(signal, volume=0.5, pan=0.0)
        left, right = track_half.get_stereo_signal()

        # 音量减半
        assert np.allclose(left, 0.5 * np.cos(np.pi/4), atol=1e-10)


class TestMixer:
    """混音器测试"""

    def test_basic_mixing(self):
        """测试基本混音"""
        mixer = Mixer(sample_rate=44100)

        signal1 = AudioSignal.from_tone(440, duration=0.1)
        signal2 = AudioSignal.from_tone(880, duration=0.1)

        mixer.add_track(signal1, name="Track 1")
        mixer.add_track(signal2, name="Track 2")

        left, right = mixer.render()

        # 应该产生输出
        assert len(left) > 0
        assert len(right) > 0

    def test_empty_mixer(self):
        """测试空混音器"""
        mixer = Mixer()
        with pytest.raises(ValueError):
            mixer.render()

    def test_track_management(self):
        """测试轨道管理"""
        mixer = Mixer()
        signal = AudioSignal.from_tone(440, duration=0.1)

        # 添加轨道
        idx = mixer.add_track(signal, name="Test")
        assert idx == 0

        # 获取轨道
        track = mixer.get_track(idx)
        assert track.name == "Test"

        # 设置音量
        mixer.set_track_volume(idx, 0.5)
        assert track.volume == 0.5

        # 设置声像
        mixer.set_track_pan(idx, -0.5)
        assert track.pan == -0.5

        # 静音
        mixer.mute_track(idx, True)
        assert track.mute

        # 独奏
        mixer.solo_track(idx, True)
        assert track.solo

        # 移除轨道
        mixer.remove_track(idx)
        assert mixer.get_track(idx) is None

    def test_solo(self):
        """测试独奏功能"""
        mixer = Mixer(sample_rate=44100)

        signal1 = AudioSignal(np.ones(44100), sample_rate=44100)
        signal2 = AudioSignal(np.ones(44100) * 0.5, sample_rate=44100)

        mixer.add_track(signal1, name="Track 1")
        idx2 = mixer.add_track(signal2, name="Track 2")

        # 独奏第二个轨道
        mixer.solo_track(idx2, True)

        mono = mixer.render_to_mono()

        # 应该只听到第二个轨道
        # 中间声像时，左右各 0.5*cos(45°) ≈ 0.354
        # mono = (left + right) / 2 ≈ 0.354
        expected_level = 0.5 * np.sqrt(2) / 2  # ≈ 0.354
        assert np.allclose(mono.data[:100], expected_level, atol=0.05)

    def test_render_to_stereo(self):
        """测试立体声渲染"""
        mixer = Mixer(sample_rate=44100)
        signal = AudioSignal.from_tone(440, duration=0.1)
        mixer.add_track(signal, name="Mono")

        stereo = mixer.render_to_stereo()

        assert stereo.channels == 2
        assert len(stereo) == len(signal) * 2

    def test_render_to_mono(self):
        """测试单声道渲染"""
        mixer = Mixer(sample_rate=44100)
        signal = AudioSignal.from_tone(440, duration=0.1)
        mixer.add_track(signal, name="Mono")

        mono = mixer.render_to_mono()

        assert mono.channels == 1
        assert len(mono) == len(signal)

    def test_master_volume(self):
        """测试主音量"""
        mixer = Mixer(sample_rate=44100)
        # 使用较小的信号避免软限幅的影响
        signal = AudioSignal(np.ones(44100) * 0.1, sample_rate=44100)
        mixer.add_track(signal, pan=0.0)

        # 正常音量
        mono_normal = mixer.render_to_mono()

        # 减半音量
        mixer.set_master_volume(0.5)
        mono_half = mixer.render_to_mono()

        # 应该减半（在软限幅影响不大的范围内）
        assert np.allclose(mono_half.data, mono_normal.data * 0.5, atol=1e-2)

    def test_clear(self):
        """测试清空"""
        mixer = Mixer()
        mixer.add_track(AudioSignal.from_tone(440, duration=0.1))
        mixer.add_track(AudioSignal.from_tone(880, duration=0.1))

        assert len(mixer.tracks) == 2

        mixer.clear()
        assert len(mixer.tracks) == 0

    def test_get_track_names(self):
        """测试获取轨道名称"""
        mixer = Mixer()
        mixer.add_track(AudioSignal.from_tone(440, duration=0.1), name="Vocal")
        mixer.add_track(AudioSignal.from_tone(880, duration=0.1), name="Drums")

        names = mixer.get_track_names()
        assert names == ["Vocal", "Drums"]

    def test_invalid_volume(self):
        """测试无效音量"""
        mixer = Mixer()
        mixer.add_track(AudioSignal.from_tone(440, duration=0.1))
        mixer.set_track_volume(0, 1.5)
        assert mixer.get_track(0).volume == 1.0  # 应该被限制

    def test_invalid_pan(self):
        """测试无效声像"""
        mixer = Mixer()
        mixer.add_track(AudioSignal.from_tone(440, duration=0.1))
        mixer.set_track_pan(0, -2.0)
        assert mixer.get_track(0).pan == -1.0  # 应该被限制
