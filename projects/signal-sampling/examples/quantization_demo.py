"""
量化演示
=========

演示均匀量化和非均匀量化。
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.quantization import (
    UniformQuantizer,
    NonUniformQuantizer,
    mu_law_quantizer,
    a_law_quantizer,
    snr_quantization,
)


def demo_uniform_quantization():
    """均匀量化演示"""
    print("=" * 60)
    print("均匀量化演示")
    print("=" * 60)

    # 生成测试信号
    t = np.linspace(0, 2 * np.pi, 1000)
    signal = np.sin(t)

    bits_list = [4, 8, 12, 16]

    print(f"测试信号: 正弦波, {len(signal)} 个采样点")
    print()

    for bits in bits_list:
        quantizer = UniformQuantizer(bits=bits, vmin=-1.0, vmax=1.0)
        quantized, indices = quantizer.quantize(signal)
        error = quantizer.quantization_error(signal)
        sqnr = quantizer.sqnr(signal)

        print(f"{bits} bit 量化:")
        print(f"  量化电平数: {quantizer.levels}")
        print(f"  量化步长: {quantizer.step:.6f}")
        print(f"  最大量化误差: {np.max(np.abs(error)):.6f}")
        print(f"  SQNR: {sqnr:.2f} dB")
        print(f"  理论 SQNR: {quantizer.theoretical_sqnr:.2f} dB")
        print()


def demo_nonuniform_quantization():
    """非均匀量化演示"""
    print("=" * 60)
    print("非均匀量化 (mu律) 演示")
    print("=" * 60)

    # 生成包含小信号的测试信号
    t = np.linspace(0, 2 * np.pi, 1000)
    signal = 0.8 * np.sin(t) + 0.1 * np.sin(5 * t) + 0.05 * np.sin(10 * t)

    bits = 8

    print(f"测试信号: 多频率混合信号, {len(signal)} 个采样点")
    print(f"量化位数: {bits}")
    print()

    # 均匀量化
    uniform = UniformQuantizer(bits=bits, vmin=signal.min(), vmax=signal.max())
    sqnr_uniform = uniform.sqnr(signal)

    # 非均匀量化
    non_uniform = NonUniformQuantizer(bits=bits, mu=255.0, vmin=signal.min(), vmax=signal.max())
    sqnr_non_uniform = non_uniform.sqnr(signal)

    print(f"均匀量化 SQNR: {sqnr_uniform:.2f} dB")
    print(f"非均匀量化 SQNR: {sqnr_non_uniform:.2f} dB")
    print(f"改善: {sqnr_non_uniform - sqnr_uniform:.2f} dB")


def demo_mu_law():
    """mu律量化演示"""
    print("\n" + "=" * 60)
    print("mu律量化演示")
    print("=" * 60)

    signal = np.sin(np.linspace(0, 2 * np.pi, 1000))

    print("不同 mu 值的量化效果:")
    print()

    for mu in [0, 50, 100, 255]:
        quantizer = NonUniformQuantizer(bits=8, mu=float(mu), vmin=-1.0, vmax=1.0)
        sqnr = quantizer.sqnr(signal)
        print(f"  mu={mu:3d}: SQNR = {sqnr:.2f} dB")


def demo_sqnr_analysis():
    """SQNR 分析演示"""
    print("\n" + "=" * 60)
    print("SQNR 与量化位数关系分析")
    print("=" * 60)

    signal = np.sin(np.linspace(0, 2 * np.pi, 1000))
    bits_range = range(2, 17)

    print("位数 | 均匀量化 SQNR | mu律量化 SQNR")
    print("-" * 45)

    for bits in bits_range:
        uniform = UniformQuantizer(bits=bits, vmin=-1.0, vmax=1.0)
        non_uniform = NonUniformQuantizer(bits=bits, mu=255.0, vmin=-1.0, vmax=1.0)

        sqnr_u = uniform.sqnr(signal)
        sqnr_nu = non_uniform.sqnr(signal)

        print(f"  {bits:2d}  |    {sqnr_u:8.2f}   |    {sqnr_nu:8.2f}")


if __name__ == "__main__":
    demo_uniform_quantization()
    demo_nonuniform_quantization()
    demo_mu_law()
    demo_sqnr_analysis()
