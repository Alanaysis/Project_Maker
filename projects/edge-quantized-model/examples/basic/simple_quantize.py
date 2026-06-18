"""
简单量化示例

演示基本的量化操作
"""

import numpy as np
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.quantization import (
    Quantizer,
    QuantConfig,
    symmetric_quantize,
    asymmetric_quantize,
    dequantize_tensor,
    compute_quantization_error,
)


def demo_symmetric_quantization():
    """演示对称量化"""
    print("=" * 60)
    print("对称量化演示")
    print("=" * 60)

    # 创建测试数据
    tensor = np.array([1.0, 2.0, 3.0, 4.0, 5.0, -1.0, -2.0, -3.0])
    print(f"\n原始数据: {tensor}")

    # 对称量化
    quantized, params = symmetric_quantize(tensor, num_bits=8)
    print(f"\n量化后数据: {quantized}")
    print(f"量化参数:")
    print(f"  scale: {params.scale:.6f}")
    print(f"  zero_point: {params.zero_point}")
    print(f"  num_bits: {params.num_bits}")

    # 反量化
    dequantized = dequantize_tensor(quantized, params)
    print(f"\n反量化数据: {dequantized}")

    # 计算误差
    error = np.abs(tensor - dequantized)
    print(f"\n量化误差: {error}")
    print(f"平均误差: {np.mean(error):.6f}")
    print(f"最大误差: {np.max(error):.6f}")


def demo_asymmetric_quantization():
    """演示非对称量化"""
    print("\n" + "=" * 60)
    print("非对称量化演示")
    print("=" * 60)

    # 创建测试数据
    tensor = np.array([1.0, 2.0, 3.0, 4.0, 5.0, -1.0, -2.0, -3.0])
    print(f"\n原始数据: {tensor}")

    # 非对称量化
    quantized, params = asymmetric_quantize(tensor, num_bits=8)
    print(f"\n量化后数据: {quantized}")
    print(f"量化参数:")
    print(f"  scale: {params.scale:.6f}")
    print(f"  zero_point: {params.zero_point}")
    print(f"  num_bits: {params.num_bits}")

    # 反量化
    dequantized = dequantize_tensor(quantized, params)
    print(f"\n反量化数据: {dequantized}")

    # 计算误差
    error = np.abs(tensor - dequantized)
    print(f"\n量化误差: {error}")
    print(f"平均误差: {np.mean(error):.6f}")
    print(f"最大误差: {np.max(error):.6f}")


def demo_int4_quantization():
    """演示 INT4 量化"""
    print("\n" + "=" * 60)
    print("INT4 量化演示")
    print("=" * 60)

    # 创建测试数据
    tensor = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0])
    print(f"\n原始数据: {tensor}")

    # INT4 量化
    quantized, params = symmetric_quantize(tensor, num_bits=4)
    print(f"\n量化后数据: {quantized}")
    print(f"量化参数:")
    print(f"  scale: {params.scale:.6f}")
    print(f"  zero_point: {params.zero_point}")
    print(f"  num_bits: {params.num_bits}")

    # 反量化
    dequantized = dequantize_tensor(quantized, params)
    print(f"\n反量化数据: {dequantized}")

    # 计算误差
    error = np.abs(tensor - dequantized)
    print(f"\n量化误差: {error}")
    print(f"平均误差: {np.mean(error):.6f}")
    print(f"最大误差: {np.max(error):.6f}")


def demo_per_channel_quantization():
    """演示逐通道量化"""
    print("\n" + "=" * 60)
    print("逐通道量化演示")
    print("=" * 60)

    # 模拟卷积权重 [out_channels, in_channels, kh, kw]
    weight = np.random.randn(3, 16, 3, 3).astype(np.float32)
    print(f"\n权重形状: {weight.shape}")

    # 逐通道量化
    quantized, params = symmetric_quantize(
        weight, num_bits=8, per_channel=True, channel_axis=0
    )

    print(f"\n量化参数:")
    print(f"  scale: {params.scale}")
    print(f"  zero_point: {params.zero_point}")
    print(f"  per_channel: {params.per_channel}")

    # 反量化
    dequantized = dequantize_tensor(quantized, params)

    # 计算误差
    error = np.abs(weight - dequantized)
    print(f"\n平均量化误差: {np.mean(error):.6f}")
    print(f"最大量化误差: {np.max(error):.6f}")


def demo_quantization_comparison():
    """演示不同量化方式的对比"""
    print("\n" + "=" * 60)
    print("量化方式对比")
    print("=" * 60)

    # 创建测试数据
    tensor = np.random.randn(100, 100).astype(np.float32)
    print(f"\n测试数据形状: {tensor.shape}")

    # INT8 对称量化
    quantized_8_sym, params_8_sym = symmetric_quantize(tensor, num_bits=8)
    errors_8_sym = compute_quantization_error(tensor, quantized_8_sym, params_8_sym)

    # INT8 非对称量化
    quantized_8_asym, params_8_asym = asymmetric_quantize(tensor, num_bits=8)
    errors_8_asym = compute_quantization_error(tensor, quantized_8_asym, params_8_asym)

    # INT4 对称量化
    quantized_4_sym, params_4_sym = symmetric_quantize(tensor, num_bits=4)
    errors_4_sym = compute_quantization_error(tensor, quantized_4_sym, params_4_sym)

    # 打印对比结果
    print(f"\n{'量化方式':<20} {'MSE':<15} {'MAE':<15} {'SNR (dB)':<15}")
    print("-" * 65)
    print(f"{'INT8 对称':<20} {errors_8_sym['mse']:<15.6f} {errors_8_sym['mae']:<15.6f} {errors_8_sym['snr']:<15.2f}")
    print(f"{'INT8 非对称':<20} {errors_8_asym['mse']:<15.6f} {errors_8_asym['mae']:<15.6f} {errors_8_asym['snr']:<15.2f}")
    print(f"{'INT4 对称':<20} {errors_4_sym['mse']:<15.6f} {errors_4_sym['mae']:<15.6f} {errors_4_sym['snr']:<15.2f}")


if __name__ == "__main__":
    demo_symmetric_quantization()
    demo_asymmetric_quantization()
    demo_int4_quantization()
    demo_per_channel_quantization()
    demo_quantization_comparison()

    print("\n" + "=" * 60)
    print("所有演示完成!")
    print("=" * 60)
