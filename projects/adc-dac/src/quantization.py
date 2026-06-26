"""
量化模块 (Quantization Module)
==============================

量化是将连续幅度的信号映射到有限离散值的过程。

关键概念:
- 均匀量化 (Uniform Quantization): 量化间隔相等
- 非均匀量化 (Non-uniform Quantization): 量化间隔不等 (如 A-law, mu-law)
- 量化误差: 原始值与量化值之间的差
- 量化噪声: 量化误差的统计特性

数学基础:
- 量化级数: L = 2^B (B 为位数)
- 量化步长: delta = V_range / L
- 量化误差范围: [-delta/2, +delta/2]
- 量化噪声功率: delta^2 / 12
"""

import numpy as np


def uniform_quantize(signal: np.ndarray, num_bits: int, v_range: tuple = (-1.0, 1.0)) -> dict:
    """
    均匀量化

    将连续幅度的信号映射到 2^num_bits 个离散电平。

    参数:
        signal: 输入信号 (numpy array)
        num_bits: 量化位数 (1-32)
        v_range: 电压范围 (min, max)

    返回:
        dict 包含:
            - quantized: 量化后的信号
            - levels: 量化电平数组
            - num_levels: 量化级数
            - step_size: 量化步长
            - quantization_error: 量化误差
            - snr_theoretical: 理论 SNR (dB)
    """
    if not (1 <= num_bits <= 32):
        raise ValueError(f"位数必须在 1-32 之间，收到 {num_bits}")

    v_min, v_max = v_range
    v_range_val = v_max - v_min
    num_levels = 2 ** num_bits
    step_size = v_range_val / num_levels

    # 计算量化电平 (居中)
    levels = np.linspace(v_min + step_size / 2, v_max - step_size / 2, num_levels)

    # 对信号进行量化
    # 将信号映射到 [0, num_levels-1] 的索引
    indices = np.clip((signal - v_min) / step_size, 0, num_levels - 1).astype(int)
    quantized = levels[indices]

    # 计算量化误差
    quantization_error = signal - quantized

    # 理论 SNR (对于满量程正弦波)
    # SNR = 6.02*B + 1.76 dB
    snr_theoretical = 6.02 * num_bits + 1.76

    return {
        "quantized": quantized,
        "levels": levels,
        "num_levels": num_levels,
        "step_size": step_size,
        "quantization_error": quantization_error,
        "snr_theoretical": snr_theoretical,
    }


def non_uniform_quantize_a_law(signal: np.ndarray, num_bits: int = 8, v_max: float = 1.0) -> dict:
    """
    A-law 非均匀量化 (用于欧洲/中国电话系统)

    A-law 压缩特性:
    - |x| <= 1/A:  y = A*x / (1 + ln(A))
    - |x| > 1/A:  y = sign(x) * (1 + ln(A*|x|)) / (1 + ln(A))

    其中 A = 87.6 (欧洲标准)

    参数:
        signal: 输入信号 (numpy array, 归一化到 [-1, 1])
        num_bits: 量化位数
        v_max: 最大电压

    返回:
        dict 包含量化结果
    """
    A = 87.6  # A-law 标准参数
    num_levels = 2 ** num_bits
    denominator = 1.0 + np.log(A)

    # 压缩 (companding)
    compressed = np.zeros_like(signal)
    abs_signal = np.abs(signal)

    # 小信号区域 (线性)
    mask_small = abs_signal <= (1.0 / A)
    compressed[mask_small] = A * signal[mask_small] / denominator

    # 大信号区域 (对数)
    mask_large = ~mask_small
    if np.any(mask_large):
        compressed[mask_large] = (
            np.sign(signal[mask_large])
            * (1.0 + np.log(A * abs_signal[mask_large]))
            / denominator
        )

    # 对压缩后的信号进行均匀量化
    quantized_compressed = np.clip(compressed, -1.0, 1.0)
    indices = ((quantized_compressed + 1.0) / 2.0 * (num_levels - 1)).astype(int)
    quantized_compressed = (indices / (num_levels - 1)) * 2.0 - 1.0

    # 扩张 (expanding) - 恢复原始范围
    expanded = np.zeros_like(quantized_compressed)
    abs_compressed = np.abs(quantized_compressed)

    mask_small_q = abs_compressed <= (1.0 / A)
    expanded[mask_small_q] = quantized_compressed[mask_small_q] * denominator / A

    mask_large_q = ~mask_small_q
    if np.any(mask_large_q):
        expanded[mask_large_q] = (
            np.sign(quantized_compressed[mask_large_q])
            * (1.0 / A)
            * np.exp(abs_compressed[mask_large_q] * (1.0 + np.log(A)) - 1.0)
        )

    # 量化误差
    quantization_error = signal - expanded

    return {
        "quantized": expanded * v_max,
        "compressed": compressed,
        "quantization_error": quantization_error,
        "num_levels": num_levels,
        "law_type": "A-law",
        "A_parameter": A,
    }


def non_uniform_quantize_mu_law(signal: np.ndarray, num_bits: int = 8, v_max: float = 1.0) -> dict:
    """
    mu-law 非均匀量化 (用于北美/日本电话系统)

    mu-law 压缩特性:
    y = sign(x) * ln(1 + mu*|x|) / ln(1 + mu)

    其中 mu = 255 (标准值)

    参数:
        signal: 输入信号 (numpy array, 归一化到 [-1, 1])
        num_bits: 量化位数
        v_max: 最大电压

    返回:
        dict 包含量化结果
    """
    mu = 255  # mu-law 标准参数
    num_levels = 2 ** num_bits
    denominator = np.log(1.0 + mu)

    # 压缩
    compressed = np.sign(signal) * np.log(1.0 + mu * np.abs(signal)) / denominator

    # 均匀量化压缩信号
    quantized_compressed = np.clip(compressed, -1.0, 1.0)
    indices = ((quantized_compressed + 1.0) / 2.0 * (num_levels - 1)).astype(int)
    quantized_compressed = (indices / (num_levels - 1)) * 2.0 - 1.0

    # 扩张
    expanded = np.sign(quantized_compressed) * (
        (1.0 + mu) ** np.abs(quantized_compressed) - 1.0
    ) / mu

    quantization_error = signal - expanded

    return {
        "quantized": expanded * v_max,
        "compressed": compressed,
        "quantization_error": quantization_error,
        "num_levels": num_levels,
        "law_type": "mu-law",
        "mu_parameter": mu,
    }


def quantization_noise_analysis(signal: np.ndarray, quantized: np.ndarray) -> dict:
    """
    量化噪声分析

    分析量化误差的统计特性。

    参数:
        signal: 原始信号
        quantized: 量化后信号

    返回:
        dict 包含噪声统计信息
    """
    error = signal - quantized

    return {
        "mean_error": np.mean(error),
        "rms_error": np.sqrt(np.mean(error ** 2)),
        "max_error": np.max(np.abs(error)),
        "min_error": np.min(error),
        "max_error_positive": np.max(error),
        "max_error_negative": np.min(error),
        "error_std": np.std(error),
        "error_hist": np.histogram(error, bins=50, density=True),
    }


def calculate_quantization_snr(signal: np.ndarray, quantized: np.ndarray) -> float:
    """
    计算量化信噪比 (SNR)

    SNR = 10 * log10(P_signal / P_noise)

    参数:
        signal: 原始信号
        quantized: 量化后信号

    返回:
        SNR (dB)
    """
    signal_power = np.mean(signal ** 2)
    noise_power = np.mean((signal - quantized) ** 2)

    if noise_power == 0:
        return float("inf")

    return 10.0 * np.log10(signal_power / noise_power)


def adaptive_quantization(signal: np.ndarray, num_bits: int, segments: int = 8) -> dict:
    """
    自适应量化

    根据信号幅度动态调整量化步长。
    小幅度信号使用小步长 (高精度)，大幅度信号使用大步长 (宽范围)。

    参数:
        signal: 输入信号
        num_bits: 量化位数
        segments: 自适应分段数

    返回:
        dict 包含量化结果
    """
    abs_max = np.max(np.abs(signal))
    if abs_max == 0:
        abs_max = 1e-10

    # 归一化
    normalized = signal / abs_max

    # 分段量化
    num_levels = 2 ** num_bits
    step_size = 2.0 / num_levels
    indices = ((normalized + 1.0) / step_size).astype(int)
    indices = np.clip(indices, 0, num_levels - 1)

    # 量化
    quantized_normalized = (indices + 0.5) * step_size - 1.0
    quantized = quantized_normalized * abs_max

    return {
        "quantized": quantized,
        "num_levels": num_levels,
        "segments": segments,
        "max_amplitude": abs_max,
    }
