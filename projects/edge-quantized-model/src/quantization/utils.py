"""
量化工具函数

提供量化相关的辅助功能
"""

import numpy as np
from typing import Tuple, List, Optional


def calculate_quantization_params(
    min_val: float,
    max_val: float,
    num_bits: int = 8,
    symmetric: bool = True,
) -> Tuple[float, int]:
    """
    计算量化参数

    Args:
        min_val: 最小值
        max_val: 最大值
        num_bits: 量化位数
        symmetric: 是否对称量化

    Returns:
        (scale, zero_point)
    """
    if symmetric:
        abs_max = max(abs(min_val), abs(max_val))
        qmin, qmax = -(2 ** (num_bits - 1)), 2 ** (num_bits - 1) - 1
        scale = abs_max / qmax if abs_max > 0 else 1.0
        zero_point = 0
    else:
        qmin, qmax = 0, 2**num_bits - 1
        scale = (max_val - min_val) / (qmax - qmin) if max_val != min_val else 1.0
        zero_point = int(np.clip(np.round(-min_val / scale), qmin, qmax))

    return scale, zero_point


def quantize_with_params(
    tensor: np.ndarray,
    scale: float,
    zero_point: int,
    num_bits: int = 8,
    symmetric: bool = True,
) -> np.ndarray:
    """
    使用指定参数量化张量

    Args:
        tensor: 输入张量
        scale: 缩放因子
        zero_point: 零点
        num_bits: 量化位数
        symmetric: 是否对称量化

    Returns:
        量化后的张量
    """
    if symmetric:
        qmin, qmax = -(2 ** (num_bits - 1)), 2 ** (num_bits - 1) - 1
        quantized = np.clip(np.round(tensor / scale), qmin, qmax)
    else:
        qmin, qmax = 0, 2**num_bits - 1
        quantized = np.clip(np.round(tensor / scale) + zero_point, qmin, qmax)

    if num_bits == 8:
        return quantized.astype(np.int8 if symmetric else np.uint8)
    elif num_bits == 4:
        return quantized.astype(np.int8)
    else:
        return quantized.astype(np.int32)


def dequantize_with_params(
    quantized: np.ndarray,
    scale: float,
    zero_point: int,
    symmetric: bool = True,
) -> np.ndarray:
    """
    使用指定参数反量化张量

    Args:
        quantized: 量化后的张量
        scale: 缩放因子
        zero_point: 零点
        symmetric: 是否对称量化

    Returns:
        反量化后的张量
    """
    if symmetric:
        return quantized.astype(np.float32) * scale
    else:
        return (quantized.astype(np.float32) - zero_point) * scale


def find_optimal_threshold(
    activations: np.ndarray,
    num_bits: int = 8,
    num_bins: int = 2048,
) -> float:
    """
    寻找最优量化阈值

    使用 KL 散度最小化寻找最优阈值

    Args:
        activations: 激活值
        num_bits: 量化位数
        num_bins: 直方图 bin 数量

    Returns:
        最优阈值
    """
    # 计算直方图
    min_val = activations.min()
    max_val = activations.max()

    # 只考虑正值
    if min_val < 0:
        abs_max = max(abs(min_val), abs(max_val))
        min_val = -abs_max
        max_val = abs_max

    hist, bin_edges = np.histogram(activations, bins=num_bins, range=(min_val, max_val))
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

    # 寻找最优阈值
    best_threshold = max_val
    best_kl_div = float('inf')

    num_quant_bins = 2 ** (num_bits - 1)  # 对称量化

    for threshold_idx in range(num_bins // 2, num_bins):
        threshold = bin_centers[threshold_idx]

        # 截断分布
        clipped_hist = hist.copy()
        clipped_hist[threshold_idx:] = 0

        if clipped_hist.sum() == 0:
            continue

        # 重新归一化
        p = clipped_hist / clipped_hist.sum()

        # 量化分布
        quant_hist = np.zeros(num_quant_bins)
        bin_size = threshold / num_quant_bins
        for i, count in enumerate(hist):
            if bin_centers[i] < threshold:
                bin_idx = min(int(bin_centers[i] / bin_size), num_quant_bins - 1)
                quant_hist[bin_idx] += count

        if quant_hist.sum() > 0:
            quant_hist = quant_hist / quant_hist.sum()

        # 计算 KL 散度
        epsilon = 1e-10
        p_safe = p + epsilon
        q_safe = quant_hist + epsilon
        kl_div = np.sum(p_safe * np.log(p_safe / q_safe))

        if kl_div < best_kl_div:
            best_kl_div = kl_div
            best_threshold = threshold

    return float(best_threshold)


def analyze_weight_distribution(weight: np.ndarray) -> dict:
    """
    分析权重分布

    Args:
        weight: 权重张量

    Returns:
        分布统计信息
    """
    return {
        "min": float(weight.min()),
        "max": float(weight.max()),
        "mean": float(weight.mean()),
        "std": float(weight.std()),
        "median": float(np.median(weight)),
        "shape": weight.shape,
        "size": weight.size,
        "sparsity": float(np.mean(weight == 0)),
    }


def estimate_quantization_impact(
    weight: np.ndarray,
    num_bits: int = 8,
    symmetric: bool = True,
) -> dict:
    """
    估算量化影响

    Args:
        weight: 权重张量
        num_bits: 量化位数
        symmetric: 是否对称量化

    Returns:
        量化影响评估
    """
    # 计算量化参数
    min_val, max_val = float(weight.min()), float(weight.max())
    scale, zero_point = calculate_quantization_params(min_val, max_val, num_bits, symmetric)

    # 量化
    quantized = quantize_with_params(weight, scale, zero_point, num_bits, symmetric)

    # 反量化
    dequantized = dequantize_with_params(quantized, scale, zero_point, symmetric)

    # 计算误差
    error = weight - dequantized
    mse = np.mean(error ** 2)
    mae = np.mean(np.abs(error))
    max_error = np.max(np.abs(error))

    # 计算 SNR
    signal_power = np.mean(weight ** 2)
    noise_power = mse
    snr = 10 * np.log10(signal_power / noise_power) if noise_power > 0 else float('inf')

    # 模型大小估算
    original_size = weight.nbytes
    quantized_size = weight.size * (num_bits / 8)
    compression_ratio = original_size / quantized_size

    return {
        "mse": float(mse),
        "mae": float(mae),
        "max_error": float(max_error),
        "snr": float(snr),
        "original_size_mb": original_size / (1024 * 1024),
        "quantized_size_mb": quantized_size / (1024 * 1024),
        "compression_ratio": float(compression_ratio),
        "scale": scale,
        "zero_point": zero_point,
    }
