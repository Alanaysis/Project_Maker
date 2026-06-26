"""
采样模块 (Sampling Module)
==========================

采样是 ADC 的第一步，将连续时间信号转换为离散时间信号。

关键概念:
- 奈奎斯特采样定理: 采样频率必须大于信号最高频率的2倍
- 孔径误差 (Aperture Error): 采样时刻的不确定性导致的误差
- 混叠 (Aliasing): 采样频率不足时高频信号"折叠"到低频

数学基础:
- 理想采样: x_s(t) = x(t) * sum(delta(t - n*T_s))
- 采样间隔: T_s = 1/f_s
- 奈奎斯特频率: f_Nyquist = f_s / 2
"""

import numpy as np


def ideal_sampling(signal: np.ndarray, fs: float, t_start: float = 0.0, t_end: float = 1.0) -> dict:
    """
    理想采样过程

    将连续时间信号在均匀间隔处采样，得到离散时间信号。

    参数:
        signal: 连续时间信号的采样值 (numpy array)
        fs: 采样频率 (Hz)
        t_start: 起始时间 (秒)
        t_end: 结束时间 (秒)

    返回:
        dict 包含:
            - samples: 采样后的离散信号值
            - sample_times: 采样时刻数组
            - fs: 采样频率
            - ts: 采样间隔
            - num_samples: 采样点数
    """
    # 计算采样点数
    num_samples = int((t_end - t_start) * fs) + 1
    sample_times = np.linspace(t_start, t_end, num_samples)

    # 对连续信号进行插值并采样
    t_continuous = np.linspace(t_start, t_end, len(signal))
    # 使用插值获取连续信号在采样时刻的值
    samples = np.interp(sample_times, t_continuous, signal)

    return {
        "samples": samples,
        "sample_times": sample_times,
        "fs": fs,
        "ts": 1.0 / fs,
        "num_samples": num_samples,
    }


def calculate_nyquist(signal_freq: float) -> float:
    """
    计算奈奎斯特频率

    奈奎斯特频率是采样频率的一半。根据奈奎斯特采样定理，
    要无失真地重建信号，采样频率必须至少是信号最高频率的2倍。

    参数:
        signal_freq: 信号的最高频率成分 (Hz)

    返回:
        奈奎斯特频率 (Hz)
    """
    return signal_freq * 2.0


def check_aliasing(signal_freq: float, fs: float) -> dict:
    """
    检查是否会发生混叠

    参数:
        signal_freq: 信号的最高频率 (Hz)
        fs: 采样频率 (Hz)

    返回:
        dict 包含:
            - aliased: 是否会发生混叠 (bool)
            - nyquist_freq: 奈奎斯特频率 (Hz)
            - fs_ratio: 采样频率与信号频率的比值
            - recommendation: 建议的最小采样频率
    """
    nyquist_freq = calculate_nyquist(signal_freq)
    fs_ratio = fs / signal_freq if signal_freq > 0 else float("inf")

    return {
        "aliased": fs < nyquist_freq,
        "nyquist_freq": nyquist_freq,
        "fs_ratio": fs_ratio,
        "recommendation": nyquist_freq * 1.1,  # 建议10%的过采样
    }


def aperture_error(sigma: float, signal_freq: float, amplitude: float = 1.0) -> float:
    """
    计算孔径误差 (Aperture Error)

    孔径误差是由于采样保持电路中采样孔径时间不确定性
    导致的量化误差。孔径时间越短，误差越小。

    公式: V_error = 2*pi*f*A*sigma
    其中 f 是信号频率，A 是幅度，sigma 是孔径时间抖动

    参数:
        sigma: 孔径时间抖动 (秒)
        signal_freq: 信号频率 (Hz)
        amplitude: 信号幅度

    返回:
        孔径误差的峰值 (伏特)
    """
    return 2.0 * np.pi * signal_freq * amplitude * sigma


def aperture_error_rms(sigma: float, signal_freq: float, amplitude: float = 1.0) -> float:
    """
    计算孔径误差的 RMS 值

    参数:
        sigma: 孔径时间抖动 (秒)
        signal_freq: 信号频率 (Hz)
        amplitude: 信号幅度

    返回:
        孔径误差的 RMS 值 (伏特)
    """
    return aperture_error(sigma, signal_freq, amplitude) / np.sqrt(2.0)


def generate_sample_clock(fs: float, duration: float) -> dict:
    """
    生成采样时钟信号

    参数:
        fs: 采样频率 (Hz)
        duration: 持续时间 (秒)

    返回:
        dict 包含:
            - clock_times: 时钟脉冲时刻
            - clock_values: 时钟脉冲值 (0或1)
            - period: 时钟周期
    """
    period = 1.0 / fs
    num_pulses = int(duration / period)
    clock_times = np.array([n * period for n in range(num_pulses)])
    clock_values = np.ones(num_pulses)

    return {
        "clock_times": clock_times,
        "clock_values": clock_values,
        "period": period,
    }


def undersampling_demo(signal_freq: float, fs_values: list) -> dict:
    """
    欠采样演示：展示不同采样频率下的信号重建效果

    参数:
        signal_freq: 原始信号频率 (Hz)
        fs_values: 要测试的采样频率列表 (Hz)

    返回:
        dict 包含各采样频率的混叠检测结果
    """
    results = []
    for fs in fs_values:
        check = check_aliasing(signal_freq, fs)
        check["fs"] = fs
        results.append(check)

    return {"signal_freq": signal_freq, "results": results}
