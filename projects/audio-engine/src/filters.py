"""
滤波器模块 - 音频滤波器实现

实现各种频域滤波器，包括低通、高通、带通滤波器。
"""

import numpy as np
from typing import Optional
from .fft import FFT, IFFT
from .audio_signal import AudioSignal


class Filter:
    """滤波器基类

    所有滤波器都继承此类，实现频域滤波的核心逻辑。
    """

    def __init__(self, sample_rate: int = 44100):
        """初始化滤波器

        Args:
            sample_rate: 采样率
        """
        self.sample_rate = sample_rate

    def _create_filter_mask(self, n_samples: int) -> np.ndarray:
        """创建滤波器掩码（子类实现）

        Args:
            n_samples: 采样点数

        Returns:
            滤波器频率响应（复数数组）
        """
        raise NotImplementedError

    def apply(self, signal: AudioSignal) -> AudioSignal:
        """应用滤波器

        Args:
            signal: 输入音频信号

        Returns:
            滤波后的音频信号
        """
        # FFT 变换
        spectrum = FFT.transform(signal.data)
        N = len(spectrum)

        # 创建滤波器掩码
        filter_mask = self._create_filter_mask(N)

        # 应用滤波器（频域乘法 = 时域卷积）
        filtered_spectrum = spectrum * filter_mask

        # IFFT 变换
        filtered_data = IFFT.transform_real(filtered_spectrum)

        # 确保长度一致
        filtered_data = filtered_data[:len(signal.data)]

        return AudioSignal(filtered_data, signal.sample_rate, signal.channels)

    def get_frequency_response(self, n_points: int = 1024) -> tuple:
        """获取滤波器频率响应

        Args:
            n_points: 频率响应点数

        Returns:
            (频率数组, 响应幅度数组)
        """
        filter_mask = self._create_filter_mask(n_points)
        freqs = np.fft.fftfreq(n_points, 1.0 / self.sample_rate)

        # 只返回正频率部分
        positive_mask = freqs >= 0
        return freqs[positive_mask], np.abs(filter_mask[positive_mask])


class LowPassFilter(Filter):
    """低通滤波器

    允许低频信号通过，衰减高频信号。

    频率响应:
        H(f) = 1,  当 |f| <= cutoff
        H(f) = 0,  当 |f| > cutoff

    应用场景:
    - 去除高频噪声
    - 平滑音频信号
    - 抗混叠滤波
    """

    def __init__(self, cutoff_freq: float, sample_rate: int = 44100,
                 rolloff_width: Optional[float] = None):
        """初始化低通滤波器

        Args:
            cutoff_freq: 截止频率（Hz）
            sample_rate: 采样率
            rolloff_width: 过渡带宽度（Hz），None 则使用硬截止
        """
        super().__init__(sample_rate)
        self.cutoff_freq = cutoff_freq
        self.rolloff_width = rolloff_width

    def _create_filter_mask(self, n_samples: int) -> np.ndarray:
        """创建低通滤波器掩码

        使用理想低通滤波器（矩形窗）或平滑过渡版本。
        """
        # 创建频率轴
        freqs = np.fft.fftfreq(n_samples, 1.0 / self.sample_rate)
        freqs_abs = np.abs(freqs)

        if self.rolloff_width is None:
            # 硬截止（理想低通滤波器）
            mask = (freqs_abs <= self.cutoff_freq).astype(float)
        else:
            # 平滑过渡（使用余弦过渡）
            mask = np.zeros(n_samples)
            for i in range(n_samples):
                f = freqs_abs[i]
                if f <= self.cutoff_freq - self.rolloff_width / 2:
                    mask[i] = 1.0
                elif f >= self.cutoff_freq + self.rolloff_width / 2:
                    mask[i] = 0.0
                else:
                    # 余弦过渡
                    normalized = (f - (self.cutoff_freq - self.rolloff_width / 2)) / self.rolloff_width
                    mask[i] = 0.5 * (1 + np.cos(np.pi * normalized))

        return mask


class HighPassFilter(Filter):
    """高通滤波器

    允许高频信号通过，衰减低频信号。

    频率响应:
        H(f) = 0,  当 |f| < cutoff
        H(f) = 1,  当 |f| >= cutoff

    应用场景:
    - 去除低频噪声（如嗡嗡声）
    - 去除直流偏移
    - 提取音频细节
    """

    def __init__(self, cutoff_freq: float, sample_rate: int = 44100,
                 rolloff_width: Optional[float] = None):
        """初始化高通滤波器

        Args:
            cutoff_freq: 截止频率（Hz）
            sample_rate: 采样率
            rolloff_width: 过渡带宽度（Hz）
        """
        super().__init__(sample_rate)
        self.cutoff_freq = cutoff_freq
        self.rolloff_width = rolloff_width

    def _create_filter_mask(self, n_samples: int) -> np.ndarray:
        """创建高通滤波器掩码"""
        freqs = np.fft.fftfreq(n_samples, 1.0 / self.sample_rate)
        freqs_abs = np.abs(freqs)

        if self.rolloff_width is None:
            mask = (freqs_abs >= self.cutoff_freq).astype(float)
        else:
            mask = np.zeros(n_samples)
            for i in range(n_samples):
                f = freqs_abs[i]
                if f >= self.cutoff_freq + self.rolloff_width / 2:
                    mask[i] = 1.0
                elif f <= self.cutoff_freq - self.rolloff_width / 2:
                    mask[i] = 0.0
                else:
                    normalized = (f - (self.cutoff_freq - self.rolloff_width / 2)) / self.rolloff_width
                    mask[i] = 0.5 * (1 - np.cos(np.pi * normalized))

        return mask


class BandPassFilter(Filter):
    """带通滤波器

    允许特定频段的信号通过，衰减其他频率。

    频率响应:
        H(f) = 1,  当 low_freq <= |f| <= high_freq
        H(f) = 0,  其他

    应用场景:
    - 提取特定频段的音频
    - 电话语音（300Hz-3400Hz）
    - 音乐均衡
    """

    def __init__(self, low_freq: float, high_freq: float,
                 sample_rate: int = 44100, rolloff_width: Optional[float] = None):
        """初始化带通滤波器

        Args:
            low_freq: 下限频率（Hz）
            high_freq: 上限频率（Hz）
            sample_rate: 采样率
            rolloff_width: 过渡带宽度（Hz）
        """
        super().__init__(sample_rate)
        self.low_freq = low_freq
        self.high_freq = high_freq
        self.rolloff_width = rolloff_width

        if low_freq >= high_freq:
            raise ValueError("下限频率必须小于上限频率")

    def _create_filter_mask(self, n_samples: int) -> np.ndarray:
        """创建带通滤波器掩码"""
        freqs = np.fft.fftfreq(n_samples, 1.0 / self.sample_rate)
        freqs_abs = np.abs(freqs)

        # 组合低通和高通
        low_mask = np.zeros(n_samples)
        high_mask = np.zeros(n_samples)

        for i in range(n_samples):
            f = freqs_abs[i]

            # 高通部分（通过低频以上的信号）
            if self.rolloff_width is None:
                high_mask[i] = 1.0 if f >= self.low_freq else 0.0
            else:
                if f >= self.low_freq + self.rolloff_width / 2:
                    high_mask[i] = 1.0
                elif f <= self.low_freq - self.rolloff_width / 2:
                    high_mask[i] = 0.0
                else:
                    normalized = (f - (self.low_freq - self.rolloff_width / 2)) / self.rolloff_width
                    high_mask[i] = 0.5 * (1 - np.cos(np.pi * normalized))

            # 低通部分（通过高频以下的信号）
            if self.rolloff_width is None:
                low_mask[i] = 1.0 if f <= self.high_freq else 0.0
            else:
                if f <= self.high_freq - self.rolloff_width / 2:
                    low_mask[i] = 1.0
                elif f >= self.high_freq + self.rolloff_width / 2:
                    low_mask[i] = 0.0
                else:
                    normalized = (f - (self.high_freq - self.rolloff_width / 2)) / self.rolloff_width
                    low_mask[i] = 0.5 * (1 + np.cos(np.pi * normalized))

        return low_mask * high_mask


class NotchFilter(Filter):
    """陷波滤波器（带阻滤波器）

    衰减特定频率，允许其他频率通过。

    应用场景:
    - 去除工频干扰（50Hz/60Hz）
    - 去除特定频率的噪声
    """

    def __init__(self, center_freq: float, bandwidth: float = 10.0,
                 sample_rate: int = 44100):
        """初始化陷波滤波器

        Args:
            center_freq: 中心频率（Hz）
            bandwidth: 带宽（Hz）
            sample_rate: 采样率
        """
        super().__init__(sample_rate)
        self.center_freq = center_freq
        self.bandwidth = bandwidth

    def _create_filter_mask(self, n_samples: int) -> np.ndarray:
        """创建陷波滤波器掩码"""
        freqs = np.fft.fftfreq(n_samples, 1.0 / self.sample_rate)
        freqs_abs = np.abs(freqs)

        # 陷波：在中心频率附近衰减
        mask = np.ones(n_samples)
        for i in range(n_samples):
            f = freqs_abs[i]
            if abs(f - self.center_freq) <= self.bandwidth / 2:
                # 使用余弦衰减
                normalized = abs(f - self.center_freq) / (self.bandwidth / 2)
                mask[i] = 0.5 * (1 + np.cos(np.pi * normalized))

        return mask
