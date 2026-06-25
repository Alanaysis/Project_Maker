"""
音频采样实现
=============

实现音频信号的采样、量化和重建。

核心概念:
- CD 音质: 44100 Hz, 16 bit
- 电话音质: 8000 Hz, 8 bit (mu律)
- 高保真: 96000 Hz, 24 bit

采样定理在音频中的应用:
- 人耳听觉范围: 20 Hz ~ 20 kHz
- 奈奎斯特率: 40 kHz
- CD 采样率: 44.1 kHz (留有余量)
"""

import numpy as np
from typing import Tuple, Optional, Dict
from .sampling import sample_signal
from .quantization import UniformQuantizer, NonUniformQuantizer


class AudioSampler:
    """音频采样器

    模拟音频信号的采样过程。

    Parameters
    ----------
    fs : float
        采样频率 (Hz)
    bits : int
        量化位数
    channels : int
        声道数
    """

    # 常用音频采样率
    SAMPLE_RATES = {
        "telephone": 8000,
        "radio": 22050,
        "cd": 44100,
        "dvd": 48000,
        "studio": 96000,
    }

    def __init__(
        self,
        fs: float = 44100,
        bits: int = 16,
        channels: int = 1,
    ):
        if fs <= 0:
            raise ValueError("采样频率必须为正数")
        if bits <= 0:
            raise ValueError("量化位数必须为正整数")
        if channels not in (1, 2):
            raise ValueError("声道数必须为 1 或 2")

        self.fs = fs
        self.bits = bits
        self.channels = channels
        self.quantizer = UniformQuantizer(bits, vmin=-1.0, vmax=1.0)

    @classmethod
    def from_preset(cls, preset: str, bits: int = 16) -> 'AudioSampler':
        """从预设创建采样器

        Parameters
        ----------
        preset : str
            预设名称: 'telephone', 'radio', 'cd', 'dvd', 'studio'
        bits : int
            量化位数

        Returns
        -------
        AudioSampler
            音频采样器实例
        """
        if preset not in cls.SAMPLE_RATES:
            raise ValueError(f"未知预设: {preset}，可选: {list(cls.SAMPLE_RATES.keys())}")

        fs = cls.SAMPLE_RATES[preset]
        channels = 1 if preset == "telephone" else 2
        return cls(fs=fs, bits=bits, channels=channels)

    def sample(
        self,
        signal: np.ndarray,
        t: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """采样音频信号

        Parameters
        ----------
        signal : np.ndarray
            连续音频信号
        t : np.ndarray
            时间轴

        Returns
        -------
        Tuple[np.ndarray, np.ndarray]
            (采样时间点, 采样值)
        """
        return sample_signal(t, signal, self.fs)

    def quantize(self, samples: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """量化采样值

        Parameters
        ----------
        samples : np.ndarray
            采样值

        Returns
        -------
        Tuple[np.ndarray, np.ndarray]
            (量化值, 量化索引)
        """
        # 归一化到 [-1, 1]
        max_val = np.max(np.abs(samples))
        if max_val > 0:
            normalized = samples / max_val
        else:
            normalized = samples

        quantized, indices = self.quantizer.quantize(normalized)

        # 还原
        if max_val > 0:
            quantized = quantized * max_val

        return quantized, indices

    def encode(self, samples: np.ndarray) -> np.ndarray:
        """编码为 PCM 数据

        Parameters
        ----------
        samples : np.ndarray
            采样值 (归一化)

        Returns
        -------
        np.ndarray
            PCM 编码数据
        """
        max_val = np.max(np.abs(samples))
        if max_val > 0:
            normalized = samples / max_val
        else:
            normalized = samples

        # 量化
        _, indices = self.quantizer.quantize(normalized)

        # 转换为整数
        max_int = 2 ** (self.bits - 1) - 1
        pcm = (indices - 2 ** (self.bits - 1)).astype(np.int32)

        return pcm

    def decode(self, pcm: np.ndarray) -> np.ndarray:
        """解码 PCM 数据

        Parameters
        ----------
        pcm : np.ndarray
            PCM 编码数据

        Returns
        -------
        np.ndarray
            解码后的采样值
        """
        indices = (pcm + 2 ** (self.bits - 1)).astype(int)
        return self.quantizer.dequantize(indices)

    @property
    def nyquist_frequency(self) -> float:
        """奈奎斯特频率"""
        return self.fs / 2

    @property
    def bit_rate(self) -> float:
        """比特率 (bps)"""
        return self.fs * self.bits * self.channels

    @property
    def info(self) -> Dict:
        """采样器信息"""
        return {
            "采样频率": f"{self.fs} Hz",
            "量化位数": self.bits,
            "声道数": self.channels,
            "比特率": f"{self.bit_rate / 1000:.1f} kbps",
            "奈奎斯特频率": f"{self.nyquist_frequency} Hz",
        }


def resample_audio(
    samples: np.ndarray,
    fs_original: float,
    fs_target: float,
) -> Tuple[np.ndarray, float]:
    """重采样音频

    使用 sinc 插值进行重采样。

    Parameters
    ----------
    samples : np.ndarray
        原始采样值
    fs_original : float
        原始采样频率
    fs_target : float
        目标采样频率

    Returns
    -------
    Tuple[np.ndarray, float]
        (重采样后的值, 目标采样频率)
    """
    if fs_original <= 0 or fs_target <= 0:
        raise ValueError("采样频率必须为正数")

    n_original = len(samples)
    duration = n_original / fs_original

    # 目标采样点数
    n_target = int(duration * fs_target)

    # 原始时间轴
    t_original = np.arange(n_original) / fs_original

    # 目标时间轴
    t_target = np.arange(n_target) / fs_target

    # sinc 插值重采样
    resampled = np.zeros(n_target)
    Ts_original = 1.0 / fs_original

    for i, t in enumerate(t_target):
        sinc_vals = np.sinc((t - t_original) / Ts_original)
        resampled[i] = np.sum(samples * sinc_vals)

    return resampled, fs_target


def demonstrate_audio_quantization(
    duration: float = 1.0,
    fs: float = 44100,
    freq: float = 440.0,
) -> dict:
    """演示音频量化效果

    Parameters
    ----------
    duration : float
        持续时间 (秒)
    fs : float
        采样频率 (Hz)
    freq : float
        信号频率 (Hz)

    Returns
    -------
    dict
        不同量化位数的量化结果
    """
    t = np.linspace(0, duration, int(fs * duration), endpoint=False)
    signal = np.sin(2 * np.pi * freq * t)

    results = {}
    bits_list = [4, 8, 12, 16, 24]

    for bits in bits_list:
        quantizer = UniformQuantizer(bits, vmin=-1.0, vmax=1.0)
        quantized, indices = quantizer.quantize(signal)
        sqnr = quantizer.sqnr(signal)

        results[f"{bits}bit"] = {
            "quantized": quantized,
            "indices": indices,
            "sqnr": sqnr,
            "theoretical_sqnr": quantizer.theoretical_sqnr,
            "bits": bits,
        }

    return {
        "t": t,
        "signal": signal,
        "quantization_results": results,
    }


def generate_test_tone(
    freq: float,
    duration: float,
    fs: float,
    amplitude: float = 1.0,
) -> Tuple[np.ndarray, np.ndarray]:
    """生成测试音调

    Parameters
    ----------
    freq : float
        频率 (Hz)
    duration : float
        持续时间 (秒)
    fs : float
        采样频率 (Hz)
    amplitude : float
        幅度

    Returns
    -------
    Tuple[np.ndarray, np.ndarray]
        (时间轴, 信号)
    """
    n_samples = int(fs * duration)
    t = np.arange(n_samples) / fs
    signal = amplitude * np.sin(2 * np.pi * freq * t)
    return t, signal
