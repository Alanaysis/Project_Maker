"""
重建演示
=========

演示零阶保持、一阶保持和 sinc 插值重建。
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.reconstruction import (
    zero_order_hold,
    first_order_hold,
    sinc_interpolation,
    reconstruct_signal,
    compare_reconstruction,
)


def demo_zoh():
    """零阶保持演示"""
    print("=" * 60)
    print("零阶保持 (ZOH) 重建演示")
    print("=" * 60)

    # 采样参数
    fs = 50
    f_signal = 5
    duration = 0.5

    # 采样
    t_sampled = np.arange(int(fs * duration)) / fs
    samples = np.sin(2 * np.pi * f_signal * t_sampled)

    # 重建
    t_continuous = np.linspace(0, duration, 500)
    reconstructed = zero_order_hold(t_sampled, samples, t_continuous)

    print(f"信号频率: {f_signal} Hz")
    print(f"采样频率: {fs} Hz")
    print(f"采样点数: {len(t_sampled)}")
    print(f"重建点数: {len(t_continuous)}")
    print()
    print("特点:")
    print("  - 每个采样值保持到下一个采样点")
    print("  - 产生阶梯状波形")
    print("  - 实现简单，硬件友好")
    print("  - 高频分量较多")


def demo_foh():
    """一阶保持演示"""
    print("\n" + "=" * 60)
    print("一阶保持 (FOH) 重建演示")
    print("=" * 60)

    # 采样参数
    fs = 50
    f_signal = 5
    duration = 0.5

    # 采样
    t_sampled = np.arange(int(fs * duration)) / fs
    samples = np.sin(2 * np.pi * f_signal * t_sampled)

    # 重建
    t_continuous = np.linspace(0, duration, 500)
    reconstructed = first_order_hold(t_sampled, samples, t_continuous)

    print(f"信号频率: {f_signal} Hz")
    print(f"采样频率: {fs} Hz")
    print(f"采样点数: {len(t_sampled)}")
    print(f"重建点数: {len(t_continuous)}")
    print()
    print("特点:")
    print("  - 采样点之间线性插值")
    print("  - 产生折线波形")
    print("  - 比 ZOH 更平滑")
    print("  - 计算量适中")


def demo_sinc():
    """sinc 插值演示"""
    print("\n" + "=" * 60)
    print("sinc 插值 (理想重建) 演示")
    print("=" * 60)

    # 采样参数
    fs = 50
    f_signal = 5
    duration = 0.5

    # 采样
    t_sampled = np.arange(int(fs * duration)) / fs
    samples = np.sin(2 * np.pi * f_signal * t_sampled)

    # 重建
    t_continuous = np.linspace(0.1, duration - 0.1, 300)  # 避免边界
    reconstructed = sinc_interpolation(t_sampled, samples, t_continuous, fs)
    original = np.sin(2 * np.pi * f_signal * t_continuous)

    # 计算误差
    mse = np.mean((original - reconstructed) ** 2)

    print(f"信号频率: {f_signal} Hz")
    print(f"采样频率: {fs} Hz")
    print(f"采样点数: {len(t_sampled)}")
    print(f"重建点数: {len(t_continuous)}")
    print(f"MSE: {mse:.8f}")
    print()
    print("特点:")
    print("  - 理论上完美重建带限信号")
    print("  - 使用 sinc 函数插值")
    print("  - 计算量较大")
    print("  - 需要知道采样频率")


def demo_comparison():
    """重建方法比较演示"""
    print("\n" + "=" * 60)
    print("重建方法比较")
    print("=" * 60)

    # 采样参数
    fs = 100
    f_signal = 10
    duration = 0.2

    # 采样
    t_sampled = np.arange(int(fs * duration)) / fs
    samples = np.sin(2 * np.pi * f_signal * t_sampled)

    # 重建
    t_continuous = np.linspace(0.05, duration - 0.05, 200)
    original = np.sin(2 * np.pi * f_signal * t_continuous)

    # 比较
    results = compare_reconstruction(t_sampled, samples, t_continuous, original, fs)

    print(f"信号频率: {f_signal} Hz")
    print(f"采样频率: {fs} Hz")
    print()
    print("方法      | MSE        | 最大误差   | SNR (dB)")
    print("-" * 55)

    for method, data in results.items():
        print(f"{method:9s} | {data['mse']:.8f} | {data['max_error']:.6f} | {data['snr_db']:.2f}")

    print()
    print("结论: sinc 插值对带限信号重建效果最好")


def demo_different_sampling_rates():
    """不同采样率下的重建效果"""
    print("\n" + "=" * 60)
    print("不同采样率下的重建效果")
    print("=" * 60)

    f_signal = 10
    duration = 0.2

    fs_list = [30, 50, 100, 200]

    print(f"信号频率: {f_signal} Hz")
    print()
    print("采样率 (Hz) | 过采样率 | sinc MSE")
    print("-" * 40)

    for fs in fs_list:
        t_sampled = np.arange(int(fs * duration)) / fs
        samples = np.sin(2 * np.pi * f_signal * t_sampled)

        t_continuous = np.linspace(0.05, duration - 0.05, 200)
        original = np.sin(2 * np.pi * f_signal * t_continuous)

        reconstructed = sinc_interpolation(t_sampled, samples, t_continuous, fs)
        mse = np.mean((original - reconstructed) ** 2)

        oversampling = fs / (2 * f_signal)
        print(f"  {fs:8d}  |   {oversampling:.1f}x   | {mse:.8f}")


if __name__ == "__main__":
    demo_zoh()
    demo_foh()
    demo_sinc()
    demo_comparison()
    demo_different_sampling_rates()
