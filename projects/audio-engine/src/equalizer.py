"""
均衡器模块 - 频率均衡处理

实现参数均衡器和图示均衡器。
"""

import numpy as np
from typing import List, Tuple, Optional
from .fft import FFT, IFFT
from .audio_signal import AudioSignal
from .filters import LowPassFilter, HighPassFilter, BandPassFilter


class EQBand:
    """均衡器频段

    表示均衡器的一个频段，包含中心频率、增益和Q值。
    """

    def __init__(self, frequency: float, gain_db: float = 0.0,
                 q_factor: float = 1.0):
        """初始化频段

        Args:
            frequency: 中心频率（Hz）
            gain_db: 增益（dB），正值提升，负值衰减
            q_factor: 品质因子（控制带宽）
        """
        self.frequency = frequency
        self.gain_db = gain_db
        self.q_factor = q_factor

    @property
    def bandwidth(self) -> float:
        """带宽（Hz）"""
        return self.frequency / self.q_factor

    @property
    def gain_linear(self) -> float:
        """线性增益"""
        return 10 ** (self.gain_db / 20.0)


class Equalizer:
    """参数均衡器

    使用频域处理实现多频段均衡。

    原理:
    1. 对信号进行 FFT 变换
    2. 根据各频段参数计算频率响应
    3. 将频率响应应用到信号频谱
    4. 使用 IFFT 变换回时域

    参数均衡器允许精确控制:
    - 中心频率
    - 增益（提升/衰减）
    - Q 值（带宽）

    用法:
    ```python
    eq = Equalizer(sample_rate=44100)

    # 添加频段
    eq.add_band(60, gain_db=3.0, q_factor=1.0)     # 低音增强
    eq.add_band(1000, gain_db=-2.0, q_factor=2.0)   # 中音衰减
    eq.add_band(8000, gain_db=4.0, q_factor=1.5)    # 高音增强

    # 应用均衡
    output = eq.apply(input_signal)
    ```
    """

    def __init__(self, sample_rate: int = 44100):
        """初始化均衡器

        Args:
            sample_rate: 采样率
        """
        self.sample_rate = sample_rate
        self.bands: List[EQBand] = []

    def add_band(self, frequency: float, gain_db: float = 0.0,
                 q_factor: float = 1.0) -> int:
        """添加均衡频段

        Args:
            frequency: 中心频率（Hz）
            gain_db: 增益（dB）
            q_factor: 品质因子

        Returns:
            频段索引
        """
        band = EQBand(frequency, gain_db, q_factor)
        self.bands.append(band)
        return len(self.bands) - 1

    def remove_band(self, index: int) -> None:
        """移除频段

        Args:
            index: 频段索引
        """
        if 0 <= index < len(self.bands):
            self.bands.pop(index)

    def set_band_gain(self, index: int, gain_db: float) -> None:
        """设置频段增益

        Args:
            index: 频段索引
            gain_db: 增益（dB）
        """
        if 0 <= index < len(self.bands):
            self.bands[index].gain_db = gain_db

    def set_band_frequency(self, index: int, frequency: float) -> None:
        """设置频段频率

        Args:
            index: 频段索引
            frequency: 中心频率（Hz）
        """
        if 0 <= index < len(self.bands):
            self.bands[index].frequency = frequency

    def set_band_q(self, index: int, q_factor: float) -> None:
        """设置频段 Q 值

        Args:
            index: 频段索引
            q_factor: 品质因子
        """
        if 0 <= index < len(self.bands):
            self.bands[index].q_factor = q_factor

    def _calculate_band_response(self, freqs: np.ndarray,
                                  band: EQBand) -> np.ndarray:
        """计算单个频段的频率响应

        使用参数均衡器的标准公式:
        H(f) = 1 + gain * bell(f, fc, Q)

        其中 bell 是钟形函数。

        Args:
            freqs: 频率数组
            band: 频段参数

        Returns:
            频率响应
        """
        fc = band.frequency
        gain = band.gain_linear
        Q = band.q_factor

        # 钟形函数（Bell/Peaking EQ）
        # H(f) = 1 + (gain - 1) * bell(f)
        # bell(f) = 1 / (1 + ((f^2 - fc^2) / (f * fc / Q))^2)
        response = np.ones(len(freqs))

        for i, f in enumerate(freqs):
            if f > 0:
                # 标准化频率差
                normalized = (f ** 2 - fc ** 2) / (f * fc / Q)
                bell = 1.0 / (1.0 + normalized ** 2)
                response[i] = 1.0 + (gain - 1.0) * bell

        return response

    def get_frequency_response(self, n_points: int = 1024) -> Tuple[np.ndarray, np.ndarray]:
        """获取均衡器的总频率响应

        Args:
            n_points: 频率点数

        Returns:
            (频率数组, 响应幅度数组)
        """
        freqs = np.fft.fftfreq(n_points, 1.0 / self.sample_rate)

        # 只计算正频率
        positive_mask = freqs >= 0
        positive_freqs = freqs[positive_mask]

        # 计算总响应（所有频段相乘）
        total_response = np.ones(len(positive_freqs))
        for band in self.bands:
            band_response = self._calculate_band_response(positive_freqs, band)
            total_response *= band_response

        return positive_freqs, total_response

    def apply(self, signal: AudioSignal) -> AudioSignal:
        """应用均衡处理

        Args:
            signal: 输入音频信号

        Returns:
            均衡处理后的音频信号
        """
        if not self.bands:
            return AudioSignal(signal.data.copy(), signal.sample_rate, signal.channels)

        # FFT 变换
        spectrum = FFT.transform(signal.data)
        N = len(spectrum)

        # 计算频率轴
        freqs = np.fft.fftfreq(N, 1.0 / self.sample_rate)

        # 计算总频率响应
        total_response = np.ones(N)
        for band in self.bands:
            band_response = self._calculate_band_response(np.abs(freqs), band)
            total_response *= band_response

        # 应用均衡
        equalized_spectrum = spectrum * total_response

        # IFFT 变换
        equalized_data = IFFT.transform_real(equalized_spectrum)

        # 确保长度一致
        equalized_data = equalized_data[:len(signal.data)]

        return AudioSignal(equalized_data, signal.sample_rate, signal.channels)


class GraphicEqualizer:
    """图示均衡器

    使用固定频段的均衡器，每个频段有独立的增益滑块。

    标准频段（ISO 标准）:
    31.5, 63, 125, 250, 500, 1000, 2000, 4000, 8000, 16000 Hz

    用法:
    ```python
    geq = GraphicEqualizer(sample_rate=44100)

    # 设置各频段增益（dB）
    geq.set_gains([3, 2, 0, -1, -2, 0, 1, 2, 3, 4])

    # 应用均衡
    output = geq.apply(input_signal)
    ```
    """

    # ISO 标准频率
    STANDARD_FREQUENCIES = [31.5, 63, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]

    def __init__(self, frequencies: Optional[List[float]] = None,
                 sample_rate: int = 44100):
        """初始化图示均衡器

        Args:
            frequencies: 频段列表，默认使用 ISO 标准
            sample_rate: 采样率
        """
        self.sample_rate = sample_rate
        self.frequencies = frequencies or self.STANDARD_FREQUENCIES
        self.gains = [0.0] * len(self.frequencies)

        # 创建内部参数均衡器
        self._eq = Equalizer(sample_rate)
        for freq in self.frequencies:
            self._eq.add_band(freq, gain_db=0.0, q_factor=1.0)

    def set_gain(self, band_index: int, gain_db: float) -> None:
        """设置单个频段增益

        Args:
            band_index: 频段索引
            gain_db: 增益（dB）
        """
        if 0 <= band_index < len(self.gains):
            self.gains[band_index] = gain_db
            self._eq.set_band_gain(band_index, gain_db)

    def set_gains(self, gains: List[float]) -> None:
        """设置所有频段增益

        Args:
            gains: 增益列表（dB）
        """
        if len(gains) != len(self.gains):
            raise ValueError(f"增益列表长度必须为 {len(self.gains)}")

        for i, gain in enumerate(gains):
            self.set_gain(i, gain)

    def get_gains(self) -> List[float]:
        """获取所有频段增益

        Returns:
            增益列表（dB）
        """
        return self.gains.copy()

    def get_frequency_response(self, n_points: int = 1024) -> Tuple[np.ndarray, np.ndarray]:
        """获取频率响应

        Args:
            n_points: 频率点数

        Returns:
            (频率数组, 响应幅度数组)
        """
        return self._eq.get_frequency_response(n_points)

    def apply(self, signal: AudioSignal) -> AudioSignal:
        """应用均衡

        Args:
            signal: 输入音频信号

        Returns:
            均衡后的音频信号
        """
        return self._eq.apply(signal)

    def reset(self) -> None:
        """重置所有频段增益为 0"""
        self.set_gains([0.0] * len(self.gains))
