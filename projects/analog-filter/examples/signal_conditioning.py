#!/usr/bin/env python3
"""
信号调理应用演示
================

演示模拟滤波器在信号调理中的应用:
1. 抗混叠滤波
2. 直流偏移去除
3. 带宽限制
4. 工频干扰消除
5. 传感器信号调理
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
from src.lowpass import RCLowPass
from src.highpass import RCHighPass
from src.bandpass import RLCBandPass
from src.bandstop import RLCBandStop
from src.applications import SignalConditioner, NotchFilter
from src.frequency_response import generate_log_freq


def demo_anti_aliasing():
    """演示抗混叠滤波"""
    print("=" * 60)
    print("抗混叠滤波演示")
    print("=" * 60)

    # 模拟采样系统
    fs = 1000  # 采样率 1kHz
    Nyquist = fs / 2  # 奈奎斯特频率 500Hz

    print(f"\n采样率: {fs} Hz")
    print(f"奈奎斯特频率: {Nyquist} Hz")

    # 设计抗混叠滤波器 (截止频率 = 0.4 * fs)
    cutoff = 0.4 * fs
    R = 1000
    C = 1.0 / (2 * np.pi * R * cutoff)
    anti_alias = RCLowPass(R, C)

    print(f"抗混叠滤波器截止频率: {anti_alias.fc:.1f} Hz")

    # 验证在奈奎斯特频率处的衰减
    f_test = np.array([cutoff, Nyquist, fs])
    mag = anti_alias.magnitude_db(f_test)
    print(f"\n频率响应:")
    print(f"  截止频率 ({cutoff:.0f}Hz): {mag[0]:.1f} dB")
    print(f"  奈奎斯特频率 ({Nyquist:.0f}Hz): {mag[1]:.1f} dB")
    print(f"  采样频率 ({fs:.0f}Hz): {mag[2]:.1f} dB")


def demo_dc_removal():
    """演示直流偏移去除"""
    print("\n" + "=" * 60)
    print("直流偏移去除演示")
    print("=" * 60)

    # 模拟传感器信号 (带直流偏移)
    fs = 100
    duration = 5.0
    t = np.arange(0, duration, 1.0 / fs)

    # 有用信号 (0.5Hz 慢变化)
    useful = np.sin(2 * np.pi * 0.5 * t)

    # 直流偏移
    dc_offset = 3.3  # 模拟 3.3V 供电偏移

    # 含偏移信号
    signal = useful + dc_offset

    print(f"\n原始信号:")
    print(f"  直流分量: {np.mean(signal):.2f} V")
    print(f"  信号幅度: {np.max(np.abs(useful)):.2f} V")

    # 使用高通滤波器去除直流
    R = 10000
    C = 1.0 / (2 * np.pi * R * 0.1)  # 截止频率 0.1Hz
    hpf = RCHighPass(R, C)

    print(f"\n高通滤波器: fc = {hpf.fc:.3f} Hz")

    # 频域滤波
    dt = t[1] - t[0]
    n = len(signal)
    S = np.fft.rfft(signal)
    freqs = np.fft.rfftfreq(n, dt)
    H = hpf.transfer_function(freqs)
    S_filtered = S * H
    signal_filtered = np.fft.irfft(S_filtered, n=n)

    print(f"\n滤波后信号:")
    print(f"  直流分量: {np.mean(signal_filtered):.4f} V")
    print(f"  信号幅度: {np.max(np.abs(signal_filtered)):.2f} V")


def demo_sensor_conditioning():
    """演示传感器信号调理"""
    print("\n" + "=" * 60)
    print("传感器信号调理演示")
    print("=" * 60)

    # 模拟温度传感器信号
    fs = 100
    duration = 10.0
    t = np.arange(0, duration, 1.0 / fs)

    # 真实温度变化 (慢变化)
    temp_true = 25 + 5 * np.sin(2 * np.pi * 0.05 * t)  # 0.05Hz 温度变化

    # 传感器噪声
    noise_50hz = 0.1 * np.sin(2 * np.pi * 50 * t)  # 50Hz 工频
    noise_high = 0.05 * np.random.randn(len(t))      # 高频噪声
    dc_offset = 2.5                                    # 直流偏移

    # 含噪声信号
    signal_noisy = temp_true + noise_50hz + noise_high + dc_offset

    print(f"\n原始信号:")
    print(f"  真实温度范围: {np.min(temp_true):.1f} - {np.max(temp_true):.1f} °C")
    print(f"  信号均值: {np.mean(signal_noisy):.2f} V")
    print(f"  信号标准差: {np.std(signal_noisy):.4f} V")

    # 信号调理链
    conditioner = SignalConditioner(fs)

    # Step 1: 去除直流偏移
    signal_step1 = conditioner.remove_dc_offset(signal_noisy, t, cutoff=0.5)

    # Step 2: 去除 50Hz 工频干扰
    signal_step2 = conditioner.remove_powerline_hum(signal_step1, t, freq=50.0, Q=30)

    # Step 3: 低通滤波 (去除高频噪声)
    R = 10000
    C = 1.0 / (2 * np.pi * R * 1.0)  # 截止频率 1Hz
    lpf = RCLowPass(R, C)
    dt = t[1] - t[0]
    n = len(signal_step2)
    S = np.fft.rfft(signal_step2)
    freqs = np.fft.rfftfreq(n, dt)
    H = lpf.transfer_function(freqs)
    signal_clean = np.fft.irfft(S * H, n=n)

    # 恢复温度值 (假设线性映射)
    temp_recovered = signal_clean + np.mean(temp_true)

    print(f"\n调理后信号:")
    print(f"  信号均值: {np.mean(signal_clean):.4f} V")
    print(f"  信号标准差: {np.std(signal_clean):.6f} V")
    print(f"  恢复温度范围: {np.min(temp_recovered):.1f} - {np.max(temp_recovered):.1f} °C")

    # 计算误差
    error = np.std(temp_recovered - temp_true)
    print(f"\n温度恢复误差 (标准差): {error:.4f} °C")


def demo_bandwidth_limiting():
    """演示带宽限制"""
    print("\n" + "=" * 60)
    print("带宽限制演示")
    print("=" * 60)

    # 模拟通信信号
    fs = 10000
    duration = 0.1
    t = np.arange(0, duration, 1.0 / fs)

    # 多频信号
    f1, f2, f3 = 100, 1000, 5000
    signal = (np.sin(2 * np.pi * f1 * t) +
              0.5 * np.sin(2 * np.pi * f2 * t) +
              0.3 * np.sin(2 * np.pi * f3 * t))

    print(f"\n原始信号包含:")
    print(f"  {f1}Hz: 幅度 1.0")
    print(f"  {f2}Hz: 幅度 0.5")
    print(f"  {f3}Hz: 幅度 0.3")

    # 带通滤波 (只保留 500-2000Hz)
    bp = RLCBandPass(R=100, L=0.016, C=1.58e-6)
    print(f"\n带通滤波器: f0={bp.f0:.0f}Hz, BW={bp.bw:.0f}Hz")

    # 频域滤波
    dt = t[1] - t[0]
    n = len(signal)
    S = np.fft.rfft(signal)
    freqs = np.fft.rfftfreq(n, dt)
    H = bp.transfer_function(freqs)
    signal_filtered = np.fft.irfft(S * H, n=n)

    print(f"\n滤波后信号:")
    print(f"  有效值: {np.sqrt(np.mean(signal_filtered**2)):.4f}")

    # 验证各频率分量
    print(f"\n各频率增益:")
    for freq in [f1, f2, f3]:
        gain = bp.magnitude(np.array([freq]))[0]
        print(f"  {freq}Hz: {gain:.4f} ({20*np.log10(gain+1e-10):.1f} dB)")


def main():
    """主函数"""
    print("信号调理应用演示")
    print("模拟滤波器在信号调理中的应用\n")

    demo_anti_aliasing()
    demo_dc_removal()
    demo_sensor_conditioning()
    demo_bandwidth_limiting()

    print("\n" + "=" * 60)
    print("演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
