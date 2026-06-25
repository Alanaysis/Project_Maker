"""
实际应用场景
============

提供模拟滤波器在音频处理和信号调理中的实际应用。

应用场景:
1. 音频处理
   - 低音增强 (低通)
   - 高音增强 (高通)
   - 均衡器 (带通组合)
   - 噪声消除 (带阻/陷波)

2. 信号调理
   - 抗混叠滤波 (低通)
   - 直流偏移去除 (高通)
   - 带宽限制 (带通)
   - 工频干扰消除 (50/60Hz 陷波)
"""

import numpy as np
from typing import Tuple, Optional

from .lowpass import RCLowPass
from .highpass import RCHighPass
from .bandpass import RLCBandPass
from .bandstop import RLCBandStop


class AudioCrossover:
    """音频分频器

    将音频信号分为低频和高频两个通道，用于音箱系统。

    Parameters
    ----------
    crossover_freq : float
        分频频率 (Hz)
    R : float
        电阻值 (欧姆), 默认 1000
    """

    def __init__(self, crossover_freq: float, R: float = 1000.0):
        self.crossover_freq = crossover_freq
        self.R = R

        # 计算电容值: fc = 1 / (2π * R * C)
        self.C = 1.0 / (2.0 * np.pi * R * crossover_freq)

        self.lowpass = RCLowPass(R, self.C)
        self.highpass = RCHighPass(R, self.C)

    def process(self, signal: np.ndarray, t: np.ndarray,
                channel: str = 'low') -> np.ndarray:
        """处理信号

        Parameters
        ----------
        signal : np.ndarray
            输入信号
        t : np.ndarray
            时间数组 (秒)
        channel : str
            通道选择: 'low' 或 'high'

        Returns
        -------
        np.ndarray
            处理后的信号
        """
        if channel == 'low':
            return self._apply_filter(signal, t, self.lowpass)
        elif channel == 'high':
            return self._apply_filter(signal, t, self.highpass)
        else:
            raise ValueError("channel 必须为 'low' 或 'high'")

    def _apply_filter(self, signal: np.ndarray, t: np.ndarray,
                      filter_obj) -> np.ndarray:
        """应用滤波器到时域信号 (使用频率域方法)

        Parameters
        ----------
        signal : np.ndarray
            输入信号
        t : np.ndarray
            时间数组
        filter_obj
            滤波器对象

        Returns
        -------
        np.ndarray
            滤波后的信号
        """
        dt = t[1] - t[0]
        n = len(signal)

        # FFT
        S = np.fft.rfft(signal)
        freqs = np.fft.rfftfreq(n, dt)

        # 应用滤波器
        H = filter_obj.transfer_function(freqs)
        S_filtered = S * H

        # IFFT
        return np.fft.irfft(S_filtered, n=n)


class NotchFilter:
    """陷波滤波器

    用于消除特定频率的干扰，如 50/60Hz 工频干扰。

    Parameters
    ----------
    notch_freq : float
        陷波频率 (Hz), 如 50 或 60
    Q : float
        品质因数, 越大带宽越窄, 默认 30
    """

    def __init__(self, notch_freq: float, Q: float = 30.0):
        self.notch_freq = notch_freq
        self.Q = Q

        # 设计 RLC 参数
        # 选择合适的 L 和 C 值
        # f0 = 1 / (2π√(LC)), Q = (1/R)√(L/C)
        self.L = 1.0  # 1H
        self.C = 1.0 / ((2.0 * np.pi * notch_freq) ** 2 * self.L)
        self.R = (1.0 / Q) * np.sqrt(self.L / self.C)

        self.bandstop = RLCBandStop(self.R, self.L, self.C)

    def process(self, signal: np.ndarray, t: np.ndarray) -> np.ndarray:
        """处理信号，消除陷波频率

        Parameters
        ----------
        signal : np.ndarray
            输入信号
        t : np.ndarray
            时间数组 (秒)

        Returns
        -------
        np.ndarray
            处理后的信号
        """
        dt = t[1] - t[0]
        n = len(signal)

        S = np.fft.rfft(signal)
        freqs = np.fft.rfftfreq(n, dt)

        H = self.bandstop.transfer_function(freqs)
        S_filtered = S * H

        return np.fft.irfft(S_filtered, n=n)


class SignalConditioner:
    """信号调理器

    组合多种滤波功能，用于信号预处理。

    Parameters
    ----------
    fs : float
        采样率 (Hz)
    """

    def __init__(self, fs: float):
        self.fs = fs

    def anti_alias_filter(self, signal: np.ndarray, t: np.ndarray,
                          cutoff_ratio: float = 0.4) -> np.ndarray:
        """抗混叠滤波

        在降采样前使用低通滤波器防止混叠。

        Parameters
        ----------
        signal : np.ndarray
            输入信号
        t : np.ndarray
            时间数组
        cutoff_ratio : float
            截止频率与采样率的比值, 默认 0.4

        Returns
        -------
        np.ndarray
            滤波后的信号
        """
        cutoff = self.fs * cutoff_ratio
        R = 1000.0
        C = 1.0 / (2.0 * np.pi * R * cutoff)
        lpf = RCLowPass(R, C)

        return self._apply_filter_freq(signal, t, lpf)

    def remove_dc_offset(self, signal: np.ndarray, t: np.ndarray,
                         cutoff: float = 1.0) -> np.ndarray:
        """去除直流偏移

        使用高通滤波器去除信号中的直流分量。

        Parameters
        ----------
        signal : np.ndarray
            输入信号
        t : np.ndarray
            时间数组
        cutoff : float
            高通截止频率 (Hz), 默认 1Hz

        Returns
        -------
        np.ndarray
            去除直流后的信号
        """
        R = 10000.0
        C = 1.0 / (2.0 * np.pi * R * cutoff)
        hpf = RCHighPass(R, C)

        return self._apply_filter_freq(signal, t, hpf)

    def band_limit(self, signal: np.ndarray, t: np.ndarray,
                   f_low: float, f_high: float) -> np.ndarray:
        """带宽限制

        使用低通和高通级联实现带通效果。

        Parameters
        ----------
        signal : np.ndarray
            输入信号
        t : np.ndarray
            时间数组
        f_low : float
            下截止频率 (Hz)
        f_high : float
            上截止频率 (Hz)

        Returns
        -------
        np.ndarray
            带限信号
        """
        R = 1000.0

        # 高通部分
        C_hp = 1.0 / (2.0 * np.pi * R * f_low)
        hpf = RCHighPass(R, C_hp)

        # 低通部分
        C_lp = 1.0 / (2.0 * np.pi * R * f_high)
        lpf = RCLowPass(R, C_lp)

        # 级联应用
        signal_hp = self._apply_filter_freq(signal, t, hpf)
        return self._apply_filter_freq(signal_hp, t, lpf)

    def remove_powerline_hum(self, signal: np.ndarray, t: np.ndarray,
                             freq: float = 50.0, Q: float = 30.0) -> np.ndarray:
        """消除工频干扰

        使用陷波滤波器消除 50Hz 或 60Hz 工频干扰。

        Parameters
        ----------
        signal : np.ndarray
            输入信号
        t : np.ndarray
            时间数组
        freq : float
            工频频率 (Hz), 默认 50Hz
        Q : float
            品质因数, 默认 30

        Returns
        -------
        np.ndarray
            去除工频干扰后的信号
        """
        notch = NotchFilter(freq, Q)
        return notch.process(signal, t)

    def _apply_filter_freq(self, signal: np.ndarray, t: np.ndarray,
                           filter_obj) -> np.ndarray:
        """在频域应用滤波器"""
        dt = t[1] - t[0]
        n = len(signal)

        S = np.fft.rfft(signal)
        freqs = np.fft.rfftfreq(n, dt)

        H = filter_obj.transfer_function(freqs)
        S_filtered = S * H

        return np.fft.irfft(S_filtered, n=n)


def demo_audio_crossover():
    """演示音频分频器

    将复合音频信号分为低频和高频通道。
    """
    # 生成测试信号 (低频 + 高频)
    fs = 44100
    duration = 0.1
    t = np.arange(0, duration, 1.0 / fs)

    # 低频信号 200Hz + 高频信号 2000Hz
    signal_low = np.sin(2 * np.pi * 200 * t)
    signal_high = 0.5 * np.sin(2 * np.pi * 2000 * t)
    signal = signal_low + signal_high

    # 创建分频器 (分频频率 1000Hz)
    crossover = AudioCrossover(1000.0)

    # 分频
    low_out = crossover.process(signal, t, 'low')
    high_out = crossover.process(signal, t, 'high')

    return t, signal, low_out, high_out


def demo_noise_removal():
    """演示噪声消除

    从含噪声信号中去除 50Hz 工频干扰。
    """
    fs = 1000
    duration = 1.0
    t = np.arange(0, duration, 1.0 / fs)

    # 有用信号 (10Hz)
    useful = np.sin(2 * np.pi * 10 * t)

    # 工频干扰 (50Hz)
    powerline = 0.3 * np.sin(2 * np.pi * 50 * t)

    # 合成含噪声信号
    noisy = useful + powerline

    # 去除工频干扰
    notch = NotchFilter(50.0, Q=30)
    cleaned = notch.process(noisy, t)

    return t, noisy, cleaned, useful
