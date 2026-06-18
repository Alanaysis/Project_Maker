"""
量化算子模块

提供基本的量化和反量化操作：
- 对称量化
- 非对称量化
- 逐通道量化
"""

import numpy as np
from typing import Tuple, Optional, Union
from dataclasses import dataclass


@dataclass
class QuantParams:
    """
    量化参数

    Attributes:
        scale: 缩放因子
        zero_point: 零点
        num_bits: 量化位数
        symmetric: 是否对称量化
        per_channel: 是否逐通道量化
        channel_axis: 通道轴
    """
    scale: Union[float, np.ndarray]
    zero_point: Union[int, np.ndarray]
    num_bits: int = 8
    symmetric: bool = True
    per_channel: bool = False
    channel_axis: int = 0

    @property
    def dtype(self) -> np.dtype:
        """获取量化数据类型"""
        if self.num_bits == 8:
            return np.int8 if self.symmetric else np.uint8
        elif self.num_bits == 4:
            return np.int8  # INT4 使用 INT8 存储
        else:
            raise ValueError(f"不支持的量化位数: {self.num_bits}")

    @property
    def quant_range(self) -> Tuple[int, int]:
        """获取量化范围"""
        if self.symmetric:
            return (-(2 ** (self.num_bits - 1)), 2 ** (self.num_bits - 1) - 1)
        else:
            return (0, 2**self.num_bits - 1)


def symmetric_quantize(
    tensor: np.ndarray,
    num_bits: int = 8,
    per_channel: bool = False,
    channel_axis: int = 0,
) -> Tuple[np.ndarray, QuantParams]:
    """
    对称量化

    量化公式: q = round(x / scale)
    反量化公式: x ≈ q * scale
    缩放因子: scale = max(|x|) / (2^(bits-1) - 1)

    Args:
        tensor: 输入张量
        num_bits: 量化位数
        per_channel: 是否逐通道量化
        channel_axis: 通道轴

    Returns:
        (quantized_tensor, quant_params)
    """
    if per_channel:
        return _symmetric_quantize_per_channel(tensor, num_bits, channel_axis)
    else:
        return _symmetric_quantize_per_layer(tensor, num_bits)


def _symmetric_quantize_per_layer(
    tensor: np.ndarray, num_bits: int
) -> Tuple[np.ndarray, QuantParams]:
    """逐层对称量化"""
    # 计算缩放因子
    abs_max = np.max(np.abs(tensor))
    qmin, qmax = -(2 ** (num_bits - 1)), 2 ** (num_bits - 1) - 1
    scale = abs_max / qmax if abs_max > 0 else 1.0

    # 量化
    quantized = np.clip(np.round(tensor / scale), qmin, qmax).astype(np.int8)

    # 量化参数
    params = QuantParams(
        scale=scale,
        zero_point=0,
        num_bits=num_bits,
        symmetric=True,
        per_channel=False,
    )

    return quantized, params


def _symmetric_quantize_per_channel(
    tensor: np.ndarray, num_bits: int, channel_axis: int
) -> Tuple[np.ndarray, QuantParams]:
    """逐通道对称量化"""
    # 获取通道数
    num_channels = tensor.shape[channel_axis]
    qmin, qmax = -(2 ** (num_bits - 1)), 2 ** (num_bits - 1) - 1

    # 计算每个通道的缩放因子
    scales = np.zeros(num_channels)
    for i in range(num_channels):
        # 获取当前通道的数据
        channel_data = np.take(tensor, i, axis=channel_axis)
        abs_max = np.max(np.abs(channel_data))
        scales[i] = abs_max / qmax if abs_max > 0 else 1.0

    # 量化
    quantized = np.zeros_like(tensor, dtype=np.int8)
    for i in range(num_channels):
        channel_data = np.take(tensor, i, axis=channel_axis)
        quantized_channel = np.clip(
            np.round(channel_data / scales[i]), qmin, qmax
        ).astype(np.int8)
        # 将量化后的通道放回
        quantized = np.moveaxis(quantized, channel_axis, 0)
        quantized[i] = quantized_channel
        quantized = np.moveaxis(quantized, 0, channel_axis)

    # 量化参数
    params = QuantParams(
        scale=scales,
        zero_point=0,
        num_bits=num_bits,
        symmetric=True,
        per_channel=True,
        channel_axis=channel_axis,
    )

    return quantized, params


def asymmetric_quantize(
    tensor: np.ndarray,
    num_bits: int = 8,
    per_channel: bool = False,
    channel_axis: int = 0,
) -> Tuple[np.ndarray, QuantParams]:
    """
    非对称量化

    量化公式: q = round(x / scale) + zero_point
    反量化公式: x ≈ (q - zero_point) * scale
    缩放因子: scale = (max(x) - min(x)) / (2^bits - 1)
    零点: zero_point = round(-min(x) / scale)

    Args:
        tensor: 输入张量
        num_bits: 量化位数
        per_channel: 是否逐通道量化
        channel_axis: 通道轴

    Returns:
        (quantized_tensor, quant_params)
    """
    if per_channel:
        return _asymmetric_quantize_per_channel(tensor, num_bits, channel_axis)
    else:
        return _asymmetric_quantize_per_layer(tensor, num_bits)


def _asymmetric_quantize_per_layer(
    tensor: np.ndarray, num_bits: int
) -> Tuple[np.ndarray, QuantParams]:
    """逐层非对称量化"""
    qmin, qmax = 0, 2**num_bits - 1

    # 计算缩放因子和零点
    min_val = np.min(tensor)
    max_val = np.max(tensor)
    scale = (max_val - min_val) / (qmax - qmin) if max_val != min_val else 1.0
    zero_point = np.clip(np.round(-min_val / scale), qmin, qmax).astype(int)

    # 量化
    quantized = np.clip(np.round(tensor / scale) + zero_point, qmin, qmax).astype(np.uint8)

    # 量化参数
    params = QuantParams(
        scale=scale,
        zero_point=zero_point,
        num_bits=num_bits,
        symmetric=False,
        per_channel=False,
    )

    return quantized, params


def _asymmetric_quantize_per_channel(
    tensor: np.ndarray, num_bits: int, channel_axis: int
) -> Tuple[np.ndarray, QuantParams]:
    """逐通道非对称量化"""
    num_channels = tensor.shape[channel_axis]
    qmin, qmax = 0, 2**num_bits - 1

    scales = np.zeros(num_channels)
    zero_points = np.zeros(num_channels, dtype=int)

    for i in range(num_channels):
        channel_data = np.take(tensor, i, axis=channel_axis)
        min_val = channel_data.min()
        max_val = channel_data.max()
        scales[i] = (max_val - min_val) / (qmax - qmin) if max_val != min_val else 1.0
        zero_points[i] = np.clip(np.round(-min_val / scales[i]), qmin, qmax).astype(int)

    # 量化
    quantized = np.zeros_like(tensor, dtype=np.uint8)
    for i in range(num_channels):
        channel_data = np.take(tensor, i, axis=channel_axis)
        quantized_channel = np.clip(
            np.round(channel_data / scales[i]) + zero_points[i], qmin, qmax
        ).astype(np.uint8)
        quantized = np.moveaxis(quantized, channel_axis, 0)
        quantized[i] = quantized_channel
        quantized = np.moveaxis(quantized, 0, channel_axis)

    # 量化参数
    params = QuantParams(
        scale=scales,
        zero_point=zero_points,
        num_bits=num_bits,
        symmetric=False,
        per_channel=True,
        channel_axis=channel_axis,
    )

    return quantized, params


def quantize_tensor(
    tensor: np.ndarray,
    num_bits: int = 8,
    symmetric: bool = True,
    per_channel: bool = False,
    channel_axis: int = 0,
) -> Tuple[np.ndarray, QuantParams]:
    """
    量化张量

    Args:
        tensor: 输入张量
        num_bits: 量化位数
        symmetric: 是否对称量化
        per_channel: 是否逐通道量化
        channel_axis: 通道轴

    Returns:
        (quantized_tensor, quant_params)
    """
    if symmetric:
        return symmetric_quantize(tensor, num_bits, per_channel, channel_axis)
    else:
        return asymmetric_quantize(tensor, num_bits, per_channel, channel_axis)


def dequantize_tensor(
    quantized: np.ndarray, params: QuantParams
) -> np.ndarray:
    """
    反量化张量

    Args:
        quantized: 量化后的张量
        params: 量化参数

    Returns:
        反量化后的张量
    """
    if params.symmetric:
        # 对称量化: x ≈ q * scale
        if params.per_channel:
            return _dequantize_per_channel(quantized, params)
        else:
            return quantized.astype(np.float32) * params.scale
    else:
        # 非对称量化: x ≈ (q - zero_point) * scale
        if params.per_channel:
            return _dequantize_per_channel(quantized, params)
        else:
            return (quantized.astype(np.float32) - params.zero_point) * params.scale


def _dequantize_per_channel(
    quantized: np.ndarray, params: QuantParams
) -> np.ndarray:
    """逐通道反量化"""
    result = np.zeros_like(quantized, dtype=np.float32)
    num_channels = quantized.shape[params.channel_axis]

    for i in range(num_channels):
        channel_data = np.take(quantized, i, axis=params.channel_axis)
        if params.symmetric:
            dequant_channel = channel_data.astype(np.float32) * params.scale[i]
        else:
            dequant_channel = (
                channel_data.astype(np.float32) - params.zero_point[i]
            ) * params.scale[i]

        result = np.moveaxis(result, params.channel_axis, 0)
        result[i] = dequant_channel
        result = np.moveaxis(result, 0, params.channel_axis)

    return result


def compute_quantization_error(
    original: np.ndarray, quantized: np.ndarray, params: QuantParams
) -> dict:
    """
    计算量化误差

    Args:
        original: 原始张量
        quantized: 量化后的张量
        params: 量化参数

    Returns:
        误差统计字典
    """
    # 反量化
    dequantized = dequantize_tensor(quantized, params)

    # 计算误差
    error = original - dequantized
    abs_error = np.abs(error)

    return {
        "mse": float(np.mean(error ** 2)),
        "mae": float(np.mean(abs_error)),
        "max_error": float(np.max(abs_error)),
        "mean_error": float(np.mean(error)),
        "std_error": float(np.std(error)),
        "snr": float(
            10 * np.log10(np.mean(original ** 2) / np.mean(error ** 2))
            if np.mean(error ** 2) > 0
            else float("inf")
        ),
    }
