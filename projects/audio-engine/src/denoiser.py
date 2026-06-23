"""
降噪模块 - 音频降噪处理

实现基于频谱减法的音频降噪算法。
"""

import numpy as np
from typing import Optional
from .fft import FFT, IFFT
from .audio_signal import AudioSignal


class Denoiser:
    """音频降噪器

    使用频谱减法（Spectral Subtraction）算法进行降噪。

    算法原理:
    1. 对含噪信号进行 FFT 变换
    2. 估计噪声频谱（从信号的静音段或使用最小统计量）
    3. 从含噪信号频谱中减去噪声频谱
    4. 使用 IFFT 变换回时域

    频谱减法公式:
        |S(f)|^2 = |X(f)|^2 - α|N(f)|^2
        |S(f)| = max(|S(f)|^2, β|X(f)|^2)

    其中:
    - X(f): 含噪信号频谱
    - N(f): 噪声频谱
    - α: 过减因子（over-subtraction factor）
    - β: 谱下限因子（spectral floor）

    参数:
    - noise_factor: 噪声估计因子（α）
    - spectral_floor: 谱下限（β），防止过度衰减
    - noise_frames: 用于估计噪声的帧数
    """

    def __init__(self, noise_factor: float = 2.0, spectral_floor: float = 0.1,
                 frame_size: int = 2048, hop_size: int = 512,
                 sample_rate: int = 44100):
        """初始化降噪器

        Args:
            noise_factor: 噪声过减因子（1-3）
            spectral_floor: 谱下限（0-0.5）
            frame_size: FFT 帧大小
            hop_size: 帧移
            sample_rate: 采样率
        """
        self.noise_factor = noise_factor
        self.spectral_floor = spectral_floor
        self.frame_size = frame_size
        self.hop_size = hop_size
        self.sample_rate = sample_rate

        # 噪声频谱估计
        self.noise_spectrum: Optional[np.ndarray] = None

    def estimate_noise(self, signal: AudioSignal,
                       noise_duration: float = 0.5) -> None:
        """从信号的开头估计噪声频谱

        假设信号开头是纯噪声（静音段）。

        Args:
            signal: 含噪音频信号
            noise_duration: 用于估计噪声的时长（秒）
        """
        noise_samples = int(noise_duration * self.sample_rate)
        noise_segment = signal.data[:noise_samples]

        # 计算噪声的平均功率谱
        noise_spectrum = np.zeros(self.frame_size // 2 + 1)
        num_frames = 0

        for start in range(0, len(noise_segment) - self.frame_size, self.hop_size):
            frame = noise_segment[start:start + self.frame_size]

            # 加窗
            windowed = frame * np.hanning(self.frame_size)
            spectrum = FFT.transform(windowed)

            # 累加功率谱
            noise_spectrum += np.abs(spectrum[:self.frame_size // 2 + 1]) ** 2
            num_frames += 1

        if num_frames > 0:
            noise_spectrum /= num_frames

        self.noise_spectrum = noise_spectrum

    def estimate_noise_from_segment(self, noise_segment: np.ndarray) -> None:
        """从给定的噪声片段估计噪声频谱

        Args:
            noise_segment: 纯噪声信号
        """
        noise_spectrum = np.zeros(self.frame_size // 2 + 1)
        num_frames = 0

        for start in range(0, len(noise_segment) - self.frame_size, self.hop_size):
            frame = noise_segment[start:start + self.frame_size]
            windowed = frame * np.hanning(self.frame_size)
            spectrum = FFT.transform(windowed)
            noise_spectrum += np.abs(spectrum[:self.frame_size // 2 + 1]) ** 2
            num_frames += 1

        if num_frames > 0:
            noise_spectrum /= num_frames

        self.noise_spectrum = noise_spectrum

    def apply(self, signal: AudioSignal) -> AudioSignal:
        """应用降噪

        Args:
            signal: 含噪音频信号

        Returns:
            降噪后的音频信号

        Raises:
            ValueError: 未估计噪声频谱
        """
        if self.noise_spectrum is None:
            # 如果未估计噪声，使用信号开头自动估计
            self.estimate_noise(signal)

        data = signal.data.copy()
        output = np.zeros_like(data)
        window = np.hanning(self.frame_size)

        # 重叠相加法（Overlap-Add）
        for start in range(0, len(data) - self.frame_size, self.hop_size):
            # 提取帧并加窗
            frame = data[start:start + self.frame_size]
            windowed = frame * window

            # FFT
            spectrum = FFT.transform(windowed)
            magnitude = np.abs(spectrum[:self.frame_size // 2 + 1])
            phase = np.angle(spectrum[:self.frame_size // 2 + 1])

            # 频谱减法
            magnitude_sq = magnitude ** 2
            noise_sq = self.noise_spectrum[:self.frame_size // 2 + 1]

            # 减去噪声频谱
            clean_sq = magnitude_sq - self.noise_factor * noise_sq

            # 应用谱下限（防止过度衰减）
            clean_sq = np.maximum(clean_sq, self.spectral_floor * magnitude_sq)

            # 恢复幅度
            clean_magnitude = np.sqrt(clean_sq)

            # 重建频谱（使用原始相位）
            clean_spectrum = np.zeros(self.frame_size, dtype=complex)
            clean_spectrum[:self.frame_size // 2 + 1] = clean_magnitude * np.exp(1j * phase)
            # 共轭对称
            clean_spectrum[self.frame_size // 2 + 1:] = np.conj(
                clean_spectrum[self.frame_size // 2 - 1:0:-1]
            )

            # IFFT
            clean_frame = IFFT.transform_real(clean_spectrum)

            # 重叠相加
            output[start:start + self.frame_size] += clean_frame * window

        # 归一化（补偿窗函数重叠）
        window_sum = np.zeros(len(data))
        for start in range(0, len(data) - self.frame_size, self.hop_size):
            window_sum[start:start + self.frame_size] += window ** 2

        # 避免除零
        window_sum = np.maximum(window_sum, 1e-10)
        output /= window_sum

        return AudioSignal(output, signal.sample_rate, signal.channels)

    def apply_simple(self, signal: AudioSignal) -> AudioSignal:
        """简单降噪（不使用重叠相加）

        适用于快速处理，质量略低但速度更快。

        Args:
            signal: 含噪音频信号

        Returns:
            降噪后的音频信号
        """
        if self.noise_spectrum is None:
            self.estimate_noise(signal)

        # FFT
        spectrum = FFT.transform(signal.data)
        N = len(spectrum)

        # 计算幅度和相位
        magnitude = np.abs(spectrum)
        phase = np.angle(spectrum)

        # 频谱减法
        magnitude_sq = magnitude ** 2

        # 扩展噪声频谱到完整长度
        noise_full = np.zeros(N)
        noise_len = len(self.noise_spectrum)
        # 填充前半部分（正频率）
        copy_len = min(noise_len, N // 2 + 1)
        noise_full[:copy_len] = self.noise_spectrum[:copy_len]
        # 对称填充后半部分（负频率）
        if copy_len > 1 and N > copy_len:
            # 跳过 DC 分量，对称复制
            for i in range(1, copy_len):
                if copy_len + i - 1 < N:
                    noise_full[copy_len + i - 1] = self.noise_spectrum[copy_len - i]

        clean_sq = magnitude_sq - self.noise_factor * noise_full
        clean_sq = np.maximum(clean_sq, self.spectral_floor * magnitude_sq)
        clean_magnitude = np.sqrt(clean_sq)

        # 重建
        clean_spectrum = clean_magnitude * np.exp(1j * phase)

        # IFFT
        clean_data = IFFT.transform_real(clean_spectrum)

        return AudioSignal(clean_data[:len(signal.data)], signal.sample_rate, signal.channels)
