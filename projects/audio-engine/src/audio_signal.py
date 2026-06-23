"""
音频信号模块 - 音频信号的表示和操作

提供音频信号的基本数据结构和常用操作。
"""

import numpy as np
from typing import Optional, Tuple
from .fft import FFT, IFFT


class AudioSignal:
    """音频信号类

    表示一个音频信号，包含采样数据和元信息。

    Attributes:
        data: 音频采样数据（一维 numpy 数组）
        sample_rate: 采样率（Hz）
        channels: 通道数（1=单声道，2=立体声）
    """

    def __init__(self, data: np.ndarray, sample_rate: int = 44100, channels: int = 1):
        """初始化音频信号

        Args:
            data: 音频采样数据
            sample_rate: 采样率，默认 44100 Hz
            channels: 通道数，默认 1（单声道）

        Raises:
            ValueError: 参数无效
        """
        if not isinstance(data, np.ndarray):
            raise ValueError("data 必须是 numpy 数组")
        if sample_rate <= 0:
            raise ValueError("采样率必须为正数")
        if channels not in (1, 2):
            raise ValueError("通道数必须是 1 或 2")

        self.data = data.astype(np.float64)
        self.sample_rate = sample_rate
        self.channels = channels

    @property
    def duration(self) -> float:
        """信号时长（秒）"""
        if self.channels == 1:
            return len(self.data) / self.sample_rate
        return len(self.data) / (self.sample_rate * self.channels)

    @property
    def num_samples(self) -> int:
        """采样点数"""
        return len(self.data)

    @property
    def nyquist_freq(self) -> float:
        """奈奎斯特频率"""
        return self.sample_rate / 2.0

    @classmethod
    def from_tone(cls, frequency: float, duration: float,
                  sample_rate: int = 44100, amplitude: float = 1.0) -> 'AudioSignal':
        """生成正弦波音调

        Args:
            frequency: 频率（Hz）
            duration: 时长（秒）
            sample_rate: 采样率
            amplitude: 振幅（0-1）

        Returns:
            AudioSignal 对象
        """
        t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
        data = amplitude * np.sin(2 * np.pi * frequency * t)
        return cls(data, sample_rate)

    @classmethod
    def from_noise(cls, duration: float, sample_rate: int = 44100,
                   amplitude: float = 0.1) -> 'AudioSignal':
        """生成白噪声

        Args:
            duration: 时长（秒）
            sample_rate: 采样率
            amplitude: 振幅

        Returns:
            AudioSignal 对象
        """
        num_samples = int(sample_rate * duration)
        data = amplitude * np.random.randn(num_samples)
        return cls(data, sample_rate)

    @classmethod
    def from_wav(cls, filepath: str) -> 'AudioSignal':
        """从 WAV 文件加载音频

        Args:
            filepath: WAV 文件路径

        Returns:
            AudioSignal 对象

        Raises:
            ValueError: 文件格式不支持
        """
        try:
            import wave
            with wave.open(filepath, 'rb') as wav:
                sample_rate = wav.getframerate()
                n_channels = wav.getnchannels()
                n_frames = wav.getnframes()
                sample_width = wav.getsampwidth()

                raw_data = wav.readframes(n_frames)

                # 根据采样位宽转换
                if sample_width == 1:
                    data = np.frombuffer(raw_data, dtype=np.uint8).astype(np.float64) / 128.0 - 1.0
                elif sample_width == 2:
                    data = np.frombuffer(raw_data, dtype=np.int16).astype(np.float64) / 32768.0
                elif sample_width == 4:
                    data = np.frombuffer(raw_data, dtype=np.int32).astype(np.float64) / 2147483648.0
                else:
                    raise ValueError(f"不支持的采样位宽: {sample_width}")

                # 如果是多声道，取第一个声道
                if n_channels > 1:
                    data = data[::n_channels]

                return cls(data, sample_rate, 1)
        except ImportError:
            raise ValueError("需要 wave 模块支持 WAV 文件读取")

    def to_wav(self, filepath: str) -> None:
        """保存为 WAV 文件

        Args:
            filepath: 输出文件路径
        """
        import wave
        import struct

        # 归一化到 16-bit 整数范围
        data_int = np.clip(self.data, -1.0, 1.0)
        data_int = (data_int * 32767).astype(np.int16)

        with wave.open(filepath, 'wb') as wav:
            wav.setnchannels(self.channels)
            wav.setsampwidth(2)  # 16-bit
            wav.setframerate(self.sample_rate)
            wav.writeframes(data_int.tobytes())

    def get_spectrum(self) -> Tuple[np.ndarray, np.ndarray]:
        """获取频谱

        Returns:
            (频率数组, 幅度数组)
        """
        N = len(self.data)
        spectrum = FFT.transform(self.data)
        # FFT 可能填充到不同的长度
        actual_len = len(spectrum)
        freqs = np.fft.fftfreq(actual_len, 1.0 / self.sample_rate)
        magnitude = np.abs(spectrum) * 2.0 / actual_len

        # 只返回正频率部分
        positive_mask = freqs >= 0
        return freqs[positive_mask], magnitude[positive_mask]

    def normalize(self, target_level: float = 0.9) -> 'AudioSignal':
        """归一化音频

        Args:
            target_level: 目标电平（0-1）

        Returns:
            归一化后的 AudioSignal
        """
        max_val = np.max(np.abs(self.data))
        if max_val > 0:
            normalized = self.data * (target_level / max_val)
        else:
            normalized = self.data.copy()
        return AudioSignal(normalized, self.sample_rate, self.channels)

    def mix(self, other: 'AudioSignal', ratio: float = 0.5) -> 'AudioSignal':
        """混合两个音频信号

        Args:
            other: 另一个音频信号
            ratio: 混合比例（0-1，0=全部self，1=全部other）

        Returns:
            混合后的 AudioSignal
        """
        if self.sample_rate != other.sample_rate:
            raise ValueError("采样率不匹配")

        # 确保长度相同
        min_len = min(len(self.data), len(other.data))
        mixed = (1 - ratio) * self.data[:min_len] + ratio * other.data[:min_len]
        return AudioSignal(mixed, self.sample_rate, self.channels)

    def apply_gain(self, gain_db: float) -> 'AudioSignal':
        """应用增益

        Args:
            gain_db: 增益（分贝）

        Returns:
            应用增益后的 AudioSignal
        """
        gain_linear = 10 ** (gain_db / 20.0)
        return AudioSignal(self.data * gain_linear, self.sample_rate, self.channels)

    def trim(self, start: float = 0.0, end: Optional[float] = None) -> 'AudioSignal':
        """裁剪音频

        Args:
            start: 开始时间（秒）
            end: 结束时间（秒），None 表示到末尾

        Returns:
            裁剪后的 AudioSignal
        """
        start_sample = int(start * self.sample_rate)
        end_sample = int(end * self.sample_rate) if end is not None else len(self.data)

        start_sample = max(0, start_sample)
        end_sample = min(len(self.data), end_sample)

        return AudioSignal(self.data[start_sample:end_sample], self.sample_rate, self.channels)

    def __len__(self) -> int:
        return len(self.data)

    def __add__(self, other: 'AudioSignal') -> 'AudioSignal':
        return self.mix(other, ratio=0.5)

    def __repr__(self) -> str:
        return (f"AudioSignal(duration={self.duration:.2f}s, "
                f"sample_rate={self.sample_rate}Hz, "
                f"samples={self.num_samples})")
