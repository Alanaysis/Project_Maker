"""
基准测试脚本

运行各种量化和推理的基准测试
"""

import numpy as np
import sys
import os
import time

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.quantization import (
    symmetric_quantize,
    asymmetric_quantize,
    dequantize_tensor,
    compute_quantization_error,
)


def benchmark_quantization():
    """量化性能基准测试"""
    print("=" * 60)
    print("量化性能基准测试")
    print("=" * 60)

    # 测试不同大小的张量
    sizes = [
        (100, 100),
        (1000, 1000),
        (100, 100, 3, 3),  # 卷积权重
        (1000, 1000),
    ]

    for size in sizes:
        tensor = np.random.randn(*size).astype(np.float32)
        print(f"\n测试大小: {size}")

        # INT8 对称量化
        times = []
        for _ in range(100):
            start = time.time()
            symmetric_quantize(tensor, num_bits=8)
            times.append(time.time() - start)
        print(f"  INT8 对称量化: {np.mean(times)*1000:.2f} ms")

        # INT8 非对称量化
        times = []
        for _ in range(100):
            start = time.time()
            asymmetric_quantize(tensor, num_bits=8)
            times.append(time.time() - start)
        print(f"  INT8 非对称量化: {np.mean(times)*1000:.2f} ms")

        # INT4 对称量化
        times = []
        for _ in range(100):
            start = time.time()
            symmetric_quantize(tensor, num_bits=4)
            times.append(time.time() - start)
        print(f"  INT4 对称量化: {np.mean(times)*1000:.2f} ms")


def benchmark_quantization_error():
    """量化误差基准测试"""
    print("\n" + "=" * 60)
    print("量化误差基准测试")
    print("=" * 60)

    # 测试不同分布的数据
    distributions = [
        ("正态分布", np.random.randn(1000, 1000).astype(np.float32)),
        ("均匀分布", np.random.uniform(-1, 1, (1000, 1000)).astype(np.float32)),
        ("稀疏数据", np.random.choice([0, 1], size=(1000, 1000), p=[0.9, 0.1]).astype(np.float32)),
    ]

    for name, tensor in distributions:
        print(f"\n{name}:")

        # INT8 对称量化
        quantized, params = symmetric_quantize(tensor, num_bits=8)
        errors = compute_quantization_error(tensor, quantized, params)
        print(f"  INT8 对称: MSE={errors['mse']:.6f}, SNR={errors['snr']:.2f} dB")

        # INT8 非对称量化
        quantized, params = asymmetric_quantize(tensor, num_bits=8)
        errors = compute_quantization_error(tensor, quantized, params)
        print(f"  INT8 非对称: MSE={errors['mse']:.6f}, SNR={errors['snr']:.2f} dB")

        # INT4 对称量化
        quantized, params = symmetric_quantize(tensor, num_bits=4)
        errors = compute_quantization_error(tensor, quantized, params)
        print(f"  INT4 对称: MSE={errors['mse']:.6f}, SNR={errors['snr']:.2f} dB")


def benchmark_dequantization():
    """反量化性能基准测试"""
    print("\n" + "=" * 60)
    print("反量化性能基准测试")
    print("=" * 60)

    sizes = [
        (100, 100),
        (1000, 1000),
        (100, 100, 3, 3),
    ]

    for size in sizes:
        tensor = np.random.randn(*size).astype(np.float32)
        quantized, params = symmetric_quantize(tensor, num_bits=8)

        print(f"\n测试大小: {size}")

        times = []
        for _ in range(100):
            start = time.time()
            dequantize_tensor(quantized, params)
            times.append(time.time() - start)
        print(f"  反量化: {np.mean(times)*1000:.2f} ms")


def run_all_benchmarks():
    """运行所有基准测试"""
    print("开始基准测试...")
    print("=" * 60)

    benchmark_quantization()
    benchmark_quantization_error()
    benchmark_dequantization()

    print("\n" + "=" * 60)
    print("基准测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_benchmarks()
