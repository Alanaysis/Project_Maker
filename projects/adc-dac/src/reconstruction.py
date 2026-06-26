"""
重建滤波器模块 (Reconstruction Filter)
=======================================

重建滤波器用于将离散时间信号恢复为连续时间信号。

关键概念:
- 零阶保持 (Zero-Order Hold, ZOH): 保持每个采样值不变
- 理想重建: 使用 sinc 函数插值
- 抗镜像滤波器 (Anti-imaging Filter): 低通滤波器，去除高频镜像

数学基础:
- 理想重建滤波器: H(f) = T_s * rect(f * T_s)
- sinc 插值: x(t) = sum(x[n] * sinc((t - n*T_s)/T_s))
- ZOH 频率响应: H_ZOH(f) = T_s * sinc(f*T_s) * exp(-j*pi*f*T_s)
"""

import numpy as np


def zero_order_hold(samples: np.ndarray, sample_times: np.ndarray,
                    t_start: float, t_end: float, fs_output: float) -> dict:
    """
    零阶保持 (ZOH)

    每个采样值在下一个采样到来之前保持不变。
    这是 DAC 中最常用的保持方式。

    参数:
        samples: 采样值数组
        sample_times: 采样时刻数组
        t_start: 输出信号起始时间
        t_end: 输出信号结束时间
        fs_output: 输出信号采样频率 (Hz)

    返回:
        dict 包含:
            - signal: 重建的信号
            - times: 重建信号的时间点
    """
    output_times = np.arange(t_start, t_end, 1.0 / fs_output)
    output_signal = np.zeros_like(output_times)

    for i in range(len(sample_times) - 1):
        # 找到该采样值有效的区间
        mask = (output_times >= sample_times[i]) & (output_times < sample_times[i + 1])
        output_signal[mask] = samples[i]

    # 处理最后一个采样点
    if len(sample_times) > 0:
        mask = (output_times >= sample_times[-1]) & (output_times <= t_end)
        output_signal[mask] = samples[-1]

    return {
        "signal": output_signal,
        "times": output_times,
    }


def ideal_reconstruction(samples: np.ndarray, sample_times: np.ndarray,
                         t_start: float, t_end: float, fs_output: float,
                         bandwidth: float = None) -> dict:
    """
    理想重建 (sinc 插值)

    使用 sinc 函数进行理想插值，理论上可以完全恢复原始信号
    (前提是满足奈奎斯特采样定理)。

    x(t) = sum(x[n] * sinc((t - n*T_s) / T_s))

    参数:
        samples: 采样值数组
        sample_times: 采样时刻数组
        t_start: 输出信号起始时间
        t_end: 输出信号结束时间
        fs_output: 输出信号采样频率 (Hz)
        bandwidth: 截止频率 (Hz)，默认为奈奎斯特频率

    返回:
        dict 包含重建信号
    """
    output_times = np.arange(t_start, t_end, 1.0 / fs_output)

    if bandwidth is None:
        bandwidth = 1.0 / (2.0 * (sample_times[1] - sample_times[0])) if len(sample_times) > 1 else 500.0

    output_signal = np.zeros_like(output_times)

    for i, t in enumerate(output_times):
        for j, t_n in enumerate(sample_times):
            ts = sample_times[1] - sample_times[0] if len(sample_times) > 1 else 0.001
            if ts == 0:
                continue
            arg = np.pi * (t - t_n) / ts
            if abs(arg) < 1e-10:
                sinc_val = 1.0
            else:
                sinc_val = np.sin(arg) / arg
            output_signal[i] += samples[j] * sinc_val

    return {
        "signal": output_signal,
        "times": output_times,
    }


def reconstruct_with_filter(samples: np.ndarray, sample_times: np.ndarray,
                            t_start: float, t_end: float, fs_output: float,
                            cutoff_freq: float, filter_order: int = 4) -> dict:
    """
    使用低通滤波器进行重建

    在理想重建的基础上加入抗镜像滤波器，去除高频分量。

    参数:
        samples: 采样值数组
        sample_times: 采样时刻数组
        t_start: 起始时间
        t_end: 结束时间
        fs_output: 输出采样频率
        cutoff_freq: 滤波器截止频率 (Hz)
        filter_order: 滤波器阶数

    返回:
        dict 包含滤波后的重建信号
    """
    # 先进行 ZOH 重建
    zoh_result = zero_order_hold(samples, sample_times, t_start, t_end, fs_output)
    reconstructed = zoh_result["signal"]
    times = zoh_result["times"]

    # 使用简单的一阶 IIR 低通滤波器模拟
    # 这是 scipy.signal 的简化实现
    alpha = cutoff_freq / (cutoff_freq + fs_output / (2 * np.pi))
    filtered = np.zeros_like(reconstructed)
    filtered[0] = reconstructed[0]

    for i in range(1, len(reconstructed)):
        filtered[i] = alpha * reconstructed[i] + (1 - alpha) * filtered[i - 1]

    return {
        "signal": filtered,
        "times": times,
        "cutoff_freq": cutoff_freq,
        "filter_order": filter_order,
    }


def compute_zoh_frequency_response(fs: float, num_points: int = 1024) -> dict:
    """
    计算 ZOH 的频率响应

    ZOH 的频率响应函数:
    H(f) = T_s * sinc(f*T_s) * exp(-j*pi*f*T_s)

    参数:
        fs: 采样频率
        num_points: 频率响应点数

    返回:
        dict 包含频率响应数据
    """
    ts = 1.0 / fs
    freqs = np.linspace(0, fs, num_points)
    omega = 2 * np.pi * freqs

    # ZOH 频率响应
    # np.sinc(x) = sin(pi*x)/(pi*x), so np.sinc(freqs * ts) = sin(pi*freqs*ts)/(pi*freqs*ts)
    # We need sinc(f*Ts) = sin(pi*f*Ts)/(pi*f*Ts) which is exactly np.sinc(freqs * ts)
    h = ts * np.sinc(freqs * ts) * np.exp(-1j * np.pi * freqs * ts)

    # 幅度响应 (dB)
    magnitude_db = 20 * np.log10(np.abs(h) + 1e-12)
    # 相位响应 (度)
    phase_deg = np.angle(h) * 180 / np.pi

    return {
        "frequencies": freqs,
        "magnitude_db": magnitude_db,
        "phase_deg": phase_deg,
        "ts": ts,
    }
