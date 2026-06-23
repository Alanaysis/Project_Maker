"""
混音器模块 - 多轨音频混合

实现多轨音频的混合、音量控制和声像定位。
"""

import numpy as np
from typing import List, Optional, Tuple
from .audio_signal import AudioSignal


class MixerTrack:
    """混音轨道

    表示混音器中的一个轨道，包含音频信号和控制参数。
    """

    def __init__(self, signal: AudioSignal, name: str = "",
                 volume: float = 1.0, pan: float = 0.0,
                 mute: bool = False, solo: bool = False):
        """初始化混音轨道

        Args:
            signal: 音频信号
            name: 轨道名称
            volume: 音量（0-1）
            pan: 声像（-1=左，0=中，1=右）
            mute: 是否静音
            solo: 是否独奏
        """
        self.signal = signal
        self.name = name
        self.volume = volume
        self.pan = pan
        self.mute = mute
        self.solo = solo

    def get_stereo_signal(self) -> Tuple[np.ndarray, np.ndarray]:
        """获取立体声信号

        Returns:
            (左声道, 右声道) 元组
        """
        if self.mute:
            n = len(self.signal.data)
            return np.zeros(n), np.zeros(n)

        data = self.signal.data * self.volume

        # 声像定位（使用正弦定律）
        # pan: -1 (左) -> 0 (中) -> 1 (右)
        angle = (self.pan + 1) / 2 * np.pi / 2  # 映射到 0-π/2
        left = data * np.cos(angle)
        right = data * np.sin(angle)

        return left, right


class Mixer:
    """混音器

    将多个音频轨道混合成一个立体声输出。

    功能:
    - 多轨混合
    - 音量控制
    - 声像定位
    - 静音/独奏
    - 总线效果

    用法:
    ```python
    mixer = Mixer(sample_rate=44100)

    # 添加轨道
    mixer.add_track(vocal_signal, name="Vocal", volume=0.8)
    mixer.add_track(drum_signal, name="Drums", volume=0.7)
    mixer.add_track(bass_signal, name="Bass", volume=0.6)

    # 混音
    left, right = mixer.render()
    ```
    """

    def __init__(self, sample_rate: int = 44100):
        """初始化混音器

        Args:
            sample_rate: 采样率
        """
        self.sample_rate = sample_rate
        self.tracks: List[MixerTrack] = []
        self.master_volume = 1.0

    def add_track(self, signal: AudioSignal, name: str = "",
                  volume: float = 1.0, pan: float = 0.0) -> int:
        """添加音频轨道

        Args:
            signal: 音频信号
            name: 轨道名称
            volume: 音量（0-1）
            pan: 声像（-1=左，0=中，1=右）

        Returns:
            轨道索引
        """
        track = MixerTrack(signal, name, volume, pan)
        self.tracks.append(track)
        return len(self.tracks) - 1

    def remove_track(self, index: int) -> None:
        """移除轨道

        Args:
            index: 轨道索引
        """
        if 0 <= index < len(self.tracks):
            self.tracks.pop(index)

    def get_track(self, index: int) -> Optional[MixerTrack]:
        """获取轨道

        Args:
            index: 轨道索引

        Returns:
            MixerTrack 对象或 None
        """
        if 0 <= index < len(self.tracks):
            return self.tracks[index]
        return None

    def set_track_volume(self, index: int, volume: float) -> None:
        """设置轨道音量

        Args:
            index: 轨道索引
            volume: 音量（0-1）
        """
        track = self.get_track(index)
        if track:
            track.volume = max(0.0, min(1.0, volume))

    def set_track_pan(self, index: int, pan: float) -> None:
        """设置轨道声像

        Args:
            index: 轨道索引
            pan: 声像（-1=左，0=中，1=右）
        """
        track = self.get_track(index)
        if track:
            track.pan = max(-1.0, min(1.0, pan))

    def mute_track(self, index: int, mute: bool = True) -> None:
        """静音/取消静音轨道

        Args:
            index: 轨道索引
            mute: 是否静音
        """
        track = self.get_track(index)
        if track:
            track.mute = mute

    def solo_track(self, index: int, solo: bool = True) -> None:
        """独奏/取消独奏轨道

        Args:
            index: 轨道索引
            solo: 是否独奏
        """
        track = self.get_track(index)
        if track:
            track.solo = solo

    def render(self) -> Tuple[AudioSignal, AudioSignal]:
        """渲染混音

        Returns:
            (左声道 AudioSignal, 右声道 AudioSignal)
        """
        if not self.tracks:
            raise ValueError("没有轨道可混合")

        # 检查是否有独奏轨道
        has_solo = any(track.solo for track in self.tracks)

        # 找到最长的轨道长度
        max_length = max(len(track.signal.data) for track in self.tracks)

        # 初始化立体声输出
        left = np.zeros(max_length)
        right = np.zeros(max_length)

        # 混合所有轨道
        for track in self.tracks:
            # 如果有独奏轨道，只播放独奏的
            if has_solo and not track.solo:
                continue

            track_left, track_right = track.get_stereo_signal()

            # 填充到相同长度
            track_len = len(track_left)
            left[:track_len] += track_left
            right[:track_len] += track_right

        # 应用总线音量
        left *= self.master_volume
        right *= self.master_volume

        # 软限幅（避免削波）
        left = self._soft_clip(left)
        right = self._soft_clip(right)

        left_signal = AudioSignal(left, self.sample_rate, 1)
        right_signal = AudioSignal(right, self.sample_rate, 1)

        return left_signal, right_signal

    def render_to_stereo(self) -> AudioSignal:
        """渲染为立体声音频

        Returns:
            立体声 AudioSignal（交错格式：LRLRLR...）
        """
        left, right = self.render()

        # 交错左右声道
        stereo = np.zeros(len(left.data) * 2)
        stereo[0::2] = left.data
        stereo[1::2] = right.data

        return AudioSignal(stereo, self.sample_rate, 2)

    def render_to_mono(self) -> AudioSignal:
        """渲染为单声道

        Returns:
            单声道 AudioSignal
        """
        left, right = self.render()
        mono = (left.data + right.data) / 2
        return AudioSignal(mono, self.sample_rate, 1)

    @staticmethod
    def _soft_clip(x: np.ndarray) -> np.ndarray:
        """软限幅

        使用 tanh 函数进行平滑限幅，避免硬削波产生的失真。
        """
        return np.tanh(x)

    def set_master_volume(self, volume: float) -> None:
        """设置主音量

        Args:
            volume: 音量（0-1）
        """
        self.master_volume = max(0.0, min(1.0, volume))

    def get_track_names(self) -> List[str]:
        """获取所有轨道名称

        Returns:
            轨道名称列表
        """
        return [track.name for track in self.tracks]

    def clear(self) -> None:
        """清空所有轨道"""
        self.tracks.clear()
