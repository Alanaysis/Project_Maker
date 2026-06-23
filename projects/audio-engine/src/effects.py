"""
音频特效模块

实现常见音频效果：混响、延迟、合唱、失真。
"""

import numpy as np
from typing import Optional, List
from .audio_signal import AudioSignal


class AudioEffect:
    """音频特效基类"""

    def apply(self, signal: AudioSignal) -> AudioSignal:
        """应用特效（子类实现）

        Args:
            signal: 输入音频信号

        Returns:
            处理后的音频信号
        """
        raise NotImplementedError


class Delay(AudioEffect):
    """延迟效果

    将原始信号与延迟后的信号混合，产生回声效果。

    原理:
    - 将信号延迟一定时间
    - 将延迟后的信号与原始信号混合
    - 可以添加多次延迟（反馈延迟）

    参数:
    - delay_time: 延迟时间（秒）
    - feedback: 反馈量（0-1，控制衰减速度）
    - mix: 混合比例（0=干声，1=全湿声）
    """

    def __init__(self, delay_time: float = 0.3, feedback: float = 0.5,
                 mix: float = 0.5, sample_rate: int = 44100):
        """初始化延迟效果

        Args:
            delay_time: 延迟时间（秒）
            feedback: 反馈量（0-1）
            mix: 混合比例（0-1）
            sample_rate: 采样率
        """
        if not 0 <= feedback <= 1:
            raise ValueError("反馈量必须在 0-1 之间")
        if not 0 <= mix <= 1:
            raise ValueError("混合比例必须在 0-1 之间")

        self.delay_time = delay_time
        self.feedback = feedback
        self.mix = mix
        self.sample_rate = sample_rate

    def apply(self, signal: AudioSignal) -> AudioSignal:
        """应用延迟效果

        Args:
            signal: 输入音频信号

        Returns:
            带延迟效果的音频信号
        """
        data = signal.data.copy()
        delay_samples = int(self.delay_time * self.sample_rate)

        # 创建延迟缓冲区（包含多次延迟的空间）
        max_delay = min(int(3.0 / self.delay_time) + 1, 10)  # 最多3秒或10次
        output = np.zeros(len(data) + delay_samples * max_delay)
        output[:len(data)] = data

        # 第一次延迟（总是添加，即使 feedback=0）
        start = delay_samples
        end = start + len(data)
        if end <= len(output):
            output[start:end] += data

        # 应用反馈延迟
        for i in range(2, max_delay + 1):
            gain = self.feedback ** (i - 1)
            if gain < 0.001:  # 衰减到足够小就停止
                break

            start = i * delay_samples
            end = start + len(data)
            if end <= len(output):
                output[start:end] += gain * data

        # 截取到原始长度
        output = output[:len(data)]

        # 混合干湿信号
        result = (1 - self.mix) * data + self.mix * output

        return AudioSignal(result, signal.sample_rate, signal.channels)


class Reverb(AudioEffect):
    """混响效果

    模拟声音在空间中的反射，增加空间感。

    原理:
    - 使用多个延迟线模拟不同反射路径
    - 每个延迟线有不同的延迟时间和衰减
    - 将所有反射混合在一起

    参数:
    - room_size: 房间大小（0-1，影响混响时间）
    - damping: 高频衰减（0-1）
    - mix: 混合比例（0=干声，1=全湿声）
    """

    def __init__(self, room_size: float = 0.5, damping: float = 0.5,
                 mix: float = 0.3, sample_rate: int = 44100):
        """初始化混响效果

        Args:
            room_size: 房间大小（0-1）
            damping: 高频衰减（0-1）
            mix: 混合比例（0-1）
            sample_rate: 采样率
        """
        self.room_size = room_size
        self.damping = damping
        self.mix = mix
        self.sample_rate = sample_rate

        # 预计算延迟线参数（Schroeder 混响模型）
        # 使用4个并行梳状滤波器 + 2个串联全通滤波器
        self.comb_delays = [0.0297, 0.0371, 0.0411, 0.0437]
        self.comb_gains = [0.75, 0.73, 0.71, 0.69]
        self.allpass_delays = [0.005, 0.0017]
        self.allpass_gains = [0.7, 0.7]

    def _comb_filter(self, data: np.ndarray, delay_time: float,
                     gain: float) -> np.ndarray:
        """梳状滤波器

        Args:
            data: 输入信号
            delay_time: 延迟时间（秒）
            gain: 增益

        Returns:
            滤波后的信号
        """
        delay_samples = int(delay_time * self.sample_rate * self.room_size)
        output = np.zeros(len(data) + delay_samples)

        for i in range(len(data)):
            output[i] = data[i] + gain * output[i - delay_samples] if i >= delay_samples else data[i]

        return output[:len(data)]

    def _allpass_filter(self, data: np.ndarray, delay_time: float,
                        gain: float) -> np.ndarray:
        """全通滤波器

        Args:
            data: 输入信号
            delay_time: 延迟时间（秒）
            gain: 增益

        Returns:
            滤波后的信号
        """
        delay_samples = int(delay_time * self.sample_rate)
        output = np.zeros(len(data))

        for i in range(len(data)):
            if i >= delay_samples:
                output[i] = -gain * data[i] + data[i - delay_samples] + gain * output[i - delay_samples]
            else:
                output[i] = data[i]

        return output

    def apply(self, signal: AudioSignal) -> AudioSignal:
        """应用混响效果

        Args:
            signal: 输入音频信号

        Returns:
            带混响效果的音频信号
        """
        data = signal.data.copy()

        # 并行梳状滤波器
        comb_outputs = []
        for delay, gain in zip(self.comb_delays, self.comb_gains):
            comb_outputs.append(self._comb_filter(data, delay, gain * (1 - self.damping * 0.5)))

        # 混合梳状滤波器输出
        reverb = np.zeros_like(data)
        for output in comb_outputs:
            reverb += output
        reverb /= len(comb_outputs)

        # 串联全通滤波器
        for delay, gain in zip(self.allpass_delays, self.allpass_gains):
            reverb = self._allpass_filter(reverb, delay, gain)

        # 混合干湿信号
        result = (1 - self.mix) * data + self.mix * reverb[:len(data)]

        return AudioSignal(result, signal.sample_rate, signal.channels)


class Chorus(AudioEffect):
    """合唱效果

    通过调制延迟时间，产生多个略微失谐的声音叠加效果。

    原理:
    - 使用 LFO（低频振荡器）调制延迟时间
    - 将原始信号与调制后的信号混合
    - 产生丰富的音色变化

    参数:
    - rate: LFO 频率（Hz）
    - depth: 调制深度（秒）
    - mix: 混合比例
    """

    def __init__(self, rate: float = 1.5, depth: float = 0.002,
                 mix: float = 0.5, sample_rate: int = 44100):
        """初始化合唱效果

        Args:
            rate: LFO 频率（Hz）
            depth: 调制深度（秒）
            mix: 混合比例（0-1）
            sample_rate: 采样率
        """
        self.rate = rate
        self.depth = depth
        self.mix = mix
        self.sample_rate = sample_rate

    def apply(self, signal: AudioSignal) -> AudioSignal:
        """应用合唱效果

        Args:
            signal: 输入音频信号

        Returns:
            带合唱效果的音频信号
        """
        data = signal.data.copy()
        n_samples = len(data)
        t = np.arange(n_samples) / self.sample_rate

        # LFO 调制延迟时间
        lfo = self.depth * np.sin(2 * np.pi * self.rate * t)
        delay_samples = (lfo * self.sample_rate).astype(int)

        # 应用调制延迟
        output = np.zeros(n_samples)
        for i in range(n_samples):
            delay = delay_samples[i]
            if i >= delay:
                # 线性插值
                idx = i - delay
                frac = delay_samples[i] - int(delay_samples[i])
                if idx + 1 < n_samples:
                    output[i] = data[idx] * (1 - frac) + data[idx + 1] * frac
                else:
                    output[i] = data[idx]
            else:
                output[i] = data[i]

        # 混合
        result = (1 - self.mix) * data + self.mix * output

        return AudioSignal(result, signal.sample_rate, signal.channels)


class Distortion(AudioEffect):
    """失真效果

    通过非线性处理增加谐波，产生失真音效。

    原理:
    - 对信号进行非线性削波或压缩
    - 增加谐波成分
    - 常用于电吉他音效

    参数:
    - drive: 驱动量（0-1，控制失真程度）
    - mix: 混合比例
    """

    def __init__(self, drive: float = 0.5, mix: float = 1.0,
                 clip_type: str = 'soft'):
        """初始化失真效果

        Args:
            drive: 驱动量（0-1）
            mix: 混合比例（0-1）
            clip_type: 削波类型（'soft' 或 'hard'）
        """
        self.drive = drive
        self.mix = mix
        self.clip_type = clip_type

    def _soft_clip(self, x: np.ndarray) -> np.ndarray:
        """软削波（tanh）

        使用 tanh 函数进行平滑削波，声音更温暖。
        """
        return np.tanh(x * (1 + self.drive * 10))

    def _hard_clip(self, x: np.ndarray) -> np.ndarray:
        """硬削波

        直接限制在 [-1, 1] 范围内，声音更尖锐。
        """
        gain = 1 + self.drive * 10
        return np.clip(x * gain, -1.0, 1.0)

    def apply(self, signal: AudioSignal) -> AudioSignal:
        """应用失真效果

        Args:
            signal: 输入音频信号

        Returns:
            带失真效果的音频信号
        """
        data = signal.data.copy()

        # 归一化
        max_val = np.max(np.abs(data))
        if max_val > 0:
            data = data / max_val

        # 应用削波
        if self.clip_type == 'soft':
            distorted = self._soft_clip(data)
        else:
            distorted = self._hard_clip(data)

        # 混合
        result = (1 - self.mix) * data + self.mix * distorted

        # 恢复原始电平
        if max_val > 0:
            result = result * max_val

        return AudioSignal(result, signal.sample_rate, signal.channels)


class Compressor(AudioEffect):
    """压缩器

    减小信号的动态范围，使响度更均匀。

    参数:
    - threshold: 阈值（dB）
    - ratio: 压缩比
    - attack: 启动时间（秒）
    - release: 释放时间（秒）
    """

    def __init__(self, threshold: float = -20.0, ratio: float = 4.0,
                 attack: float = 0.01, release: float = 0.1,
                 sample_rate: int = 44100):
        """初始化压缩器

        Args:
            threshold: 阈值（dB）
            ratio: 压缩比
            attack: 启动时间（秒）
            release: 释放时间（秒）
            sample_rate: 采样率
        """
        self.threshold = threshold
        self.ratio = ratio
        self.attack = attack
        self.release = release
        self.sample_rate = sample_rate

    def apply(self, signal: AudioSignal) -> AudioSignal:
        """应用压缩

        Args:
            signal: 输入音频信号

        Returns:
            压缩后的音频信号
        """
        data = signal.data.copy()

        # 计算包络（使用 RMS）
        window_size = int(0.01 * self.sample_rate)  # 10ms 窗口
        envelope = np.zeros(len(data))

        for i in range(len(data)):
            start = max(0, i - window_size)
            envelope[i] = np.sqrt(np.mean(data[start:i+1] ** 2))

        # 转换为 dB
        envelope_db = 20 * np.log10(envelope + 1e-10)

        # 计算增益
        gain_db = np.zeros(len(data))
        for i in range(len(data)):
            if envelope_db[i] > self.threshold:
                # 超过阈值的部分按比例压缩
                gain_db[i] = (envelope_db[i] - self.threshold) * (1 - 1/self.ratio)

        # 应用启动和释放时间
        attack_samples = int(self.attack * self.sample_rate)
        release_samples = int(self.release * self.sample_rate)

        smoothed_gain = np.zeros(len(data))
        for i in range(len(data)):
            if i > 0:
                if gain_db[i] > smoothed_gain[i-1]:
                    # 启动
                    alpha = 1 - np.exp(-1 / attack_samples) if attack_samples > 0 else 1
                else:
                    # 释放
                    alpha = 1 - np.exp(-1 / release_samples) if release_samples > 0 else 1
                smoothed_gain[i] = smoothed_gain[i-1] + alpha * (gain_db[i] - smoothed_gain[i-1])
            else:
                smoothed_gain[i] = gain_db[i]

        # 应用增益
        gain_linear = 10 ** (-smoothed_gain / 20.0)
        result = data * gain_linear

        return AudioSignal(result, signal.sample_rate, signal.channels)
