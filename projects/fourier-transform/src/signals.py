"""
信号生成工具

提供常用测试信号的生成函数。
"""

import numpy as np


def sine_wave(
    frequency: float,
    sample_rate: float,
    duration: float,
    amplitude: float = 1.0,
    phase: float = 0.0,
) -> np.ndarray:
    """
    生成正弦波

    x(t) = A * sin(2*π*f*t + φ)

    参数:
        frequency: 频率 (Hz)
        sample_rate: 采样率 (Hz)
        duration: 持续时间 (秒)
        amplitude: 幅度
        phase: 初始相位 (弧度)

    返回:
        正弦波信号
    """
    t = np.arange(int(sample_rate * duration)) / sample_rate
    return amplitude * np.sin(2 * np.pi * frequency * t + phase)


def cosine_wave(
    frequency: float,
    sample_rate: float,
    duration: float,
    amplitude: float = 1.0,
    phase: float = 0.0,
) -> np.ndarray:
    """
    生成余弦波

    x(t) = A * cos(2*π*f*t + φ)
    """
    t = np.arange(int(sample_rate * duration)) / sample_rate
    return amplitude * np.cos(2 * np.pi * frequency * t + phase)


def composite_signal(
    frequencies: list,
    amplitudes: list,
    sample_rate: float,
    duration: float,
    phases: list = None,
) -> np.ndarray:
    """
    生成复合信号（多个正弦波叠加）

    x(t) = Σ A_i * sin(2*π*f_i*t + φ_i)

    参数:
        frequencies: 频率列表
        amplitudes: 幅度列表
        sample_rate: 采样率
        duration: 持续时间
        phases: 相位列表（默认全为 0）

    返回:
        复合信号
    """
    if phases is None:
        phases = [0.0] * len(frequencies)

    N = int(sample_rate * duration)
    t = np.arange(N) / sample_rate
    signal = np.zeros(N)

    for freq, amp, phase in zip(frequencies, amplitudes, phases):
        signal += amp * np.sin(2 * np.pi * freq * t + phase)

    return signal


def square_wave(
    frequency: float,
    sample_rate: float,
    duration: float,
    duty_cycle: float = 0.5,
) -> np.ndarray:
    """
    生成方波

    参数:
        frequency: 频率 (Hz)
        sample_rate: 采样率
        duration: 持续时间
        duty_cycle: 占空比 [0, 1]

    返回:
        方波信号 (±1)
    """
    t = np.arange(int(sample_rate * duration)) / sample_rate
    phase = (frequency * t) % 1.0
    return np.where(phase < duty_cycle, 1.0, -1.0)


def sawtooth_wave(
    frequency: float,
    sample_rate: float,
    duration: float,
) -> np.ndarray:
    """
    生成锯齿波

    参数:
        frequency: 频率
        sample_rate: 采样率
        duration: 持续时间

    返回:
        锯齿波信号 [-1, 1]
    """
    t = np.arange(int(sample_rate * duration)) / sample_rate
    return 2.0 * ((frequency * t) % 1.0) - 1.0


def triangle_wave(
    frequency: float,
    sample_rate: float,
    duration: float,
) -> np.ndarray:
    """
    生成三角波

    参数:
        frequency: 频率
        sample_rate: 采样率
        duration: 持续时间

    返回:
        三角波信号 [-1, 1]
    """
    t = np.arange(int(sample_rate * duration)) / sample_rate
    phase = (frequency * t) % 1.0
    return 2.0 * np.abs(2.0 * phase - 1.0) - 1.0


def white_noise(
    sample_rate: float,
    duration: float,
    amplitude: float = 1.0,
) -> np.ndarray:
    """
    生成白噪声

    参数:
        sample_rate: 采样率
        duration: 持续时间
        amplitude: 幅度

    返回:
        白噪声信号
    """
    N = int(sample_rate * duration)
    return amplitude * np.random.randn(N)


def chirp_signal(
    f_start: float,
    f_end: float,
    sample_rate: float,
    duration: float,
) -> np.ndarray:
    """
    生成线性调频信号 (Chirp)

    频率从 f_start 线性变化到 f_end。

    参数:
        f_start: 起始频率
        f_end: 结束频率
        sample_rate: 采样率
        duration: 持续时间

    返回:
        Chirp 信号
    """
    N = int(sample_rate * duration)
    t = np.arange(N) / sample_rate
    phase = 2 * np.pi * (f_start * t + (f_end - f_start) / (2 * duration) * t ** 2)
    return np.sin(phase)


def impulse_train(
    period: int,
    total_length: int,
    amplitude: float = 1.0,
) -> np.ndarray:
    """
    生成脉冲序列

    参数:
        period: 脉冲间隔（采样点数）
        total_length: 总长度
        amplitude: 幅度

    返回:
        脉冲序列
    """
    signal = np.zeros(total_length)
    signal[::period] = amplitude
    return signal


def gaussian_pulse(
    center: float,
    width: float,
    sample_rate: float,
    duration: float,
) -> np.ndarray:
    """
    生成高斯脉冲

    x(t) = exp(-(t - center)^2 / (2 * width^2))

    参数:
        center: 脉冲中心时间
        width: 脉冲宽度
        sample_rate: 采样率
        duration: 持续时间

    返回:
        高斯脉冲信号
    """
    t = np.arange(int(sample_rate * duration)) / sample_rate
    return np.exp(-((t - center) ** 2) / (2 * width ** 2))
