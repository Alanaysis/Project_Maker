#!/usr/bin/env python3
"""
音频处理应用演示
================

演示模拟滤波器在音频处理中的应用:
1. 音频分频器 (低音/高音分离)
2. 均衡器 (多频段调节)
3. 噪声消除 (陷波滤波)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
from src.lowpass import RCLowPass
from src.highpass import RCHighPass
from src.bandpass import RLCBandPass
from src.bandstop import RLCBandStop
from src.applications import AudioCrossover, NotchFilter, SignalConditioner
from src.frequency_response import generate_log_freq


def demo_audio_crossover():
    """演示音频分频器"""
    print("=" * 60)
    print("音频分频器演示")
    print("=" * 60)

    # 分频频率 1kHz
    crossover_freq = 1000
    crossover = AudioCrossover(crossover_freq)

    print(f"\n分频频率: {crossover_freq} Hz")
    print(f"低通截止: {crossover.lowpass.fc:.2f} Hz")
    print(f"高通截止: {crossover.highpass.fc:.2f} Hz")

    # 生成测试信号
    fs = 44100
    duration = 0.01
    t = np.arange(0, duration, 1.0 / fs)

    # 复合信号: 200Hz + 2000Hz
    signal = np.sin(2 * np.pi * 200 * t) + 0.5 * np.sin(2 * np.pi * 2000 * t)

    # 分频处理
    low_out = crossover.process(signal, t, 'low')
    high_out = crossover.process(signal, t, 'high')

    print(f"\n输入信号 RMS: {np.sqrt(np.mean(signal**2)):.4f}")
    print(f"低频通道 RMS: {np.sqrt(np.mean(low_out**2)):.4f}")
    print(f"高频通道 RMS: {np.sqrt(np.mean(high_out**2)):.4f}")

    # 验证分频效果
    print(f"\n频率响应验证 (100Hz vs 10kHz):")
    f_test = np.array([100, 10000])
    mag_lp = crossover.lowpass.magnitude(f_test)
    mag_hp = crossover.highpass.magnitude(f_test)
    print(f"  低通 @ 100Hz:  {mag_lp[0]:.3f} ({20*np.log10(mag_lp[0]):.1f} dB)")
    print(f"  低通 @ 10kHz:  {mag_lp[1]:.3f} ({20*np.log10(mag_lp[1]+1e-10):.1f} dB)")
    print(f"  高通 @ 100Hz:  {mag_hp[0]:.3f} ({20*np.log10(mag_hp[0]+1e-10):.1f} dB)")
    print(f"  高通 @ 10kHz:  {mag_hp[1]:.3f} ({20*np.log10(mag_hp[1]):.1f} dB)")


def demo_equalizer():
    """演示简易均衡器"""
    print("\n" + "=" * 60)
    print("简易均衡器演示")
    print("=" * 60)

    # 三个频段的带通滤波器
    # 低频: 100Hz, 中频: 1kHz, 高频: 10kHz
    bands = [
        ("低频 (100Hz)", RLCBandPass(R=100, L=0.1, C=2.53e-6)),
        ("中频 (1kHz)",  RLCBandPass(R=100, L=0.01, C=2.53e-6)),
        ("高频 (10kHz)", RLCBandPass(R=100, L=0.001, C=2.53e-6)),
    ]

    print("\n频段配置:")
    for name, filt in bands:
        print(f"  {name}: f0={filt.f0:.0f}Hz, BW={filt.bw:.0f}Hz, Q={filt.Q:.1f}")

    # 测试信号
    f_test = np.array([100, 1000, 10000])
    print("\n各频段在不同频率的增益:")
    print(f"  {'频率':>10s}  {'低频段':>10s}  {'中频段':>10s}  {'高频段':>10s}")
    for freq in f_test:
        gains = [filt.magnitude(np.array([freq]))[0] for _, filt in bands]
        print(f"  {freq:>10.0f}  {gains[0]:>10.3f}  {gains[1]:>10.3f}  {gains[2]:>10.3f}")


def demo_noise_removal():
    """演示噪声消除"""
    print("\n" + "=" * 60)
    print("噪声消除演示 (50Hz 工频干扰)")
    print("=" * 60)

    # 创建 50Hz 陷波滤波器
    notch = NotchFilter(notch_freq=50.0, Q=30)
    print(f"\n陷波滤波器: f0={notch.bandstop.f0:.1f}Hz, Q={notch.Q}")
    print(f"  带宽: {notch.bandstop.bw:.2f} Hz")

    # 生成测试信号
    fs = 1000
    duration = 0.2
    t = np.arange(0, duration, 1.0 / fs)

    # 有用信号 (10Hz 正弦波)
    useful = np.sin(2 * np.pi * 10 * t)

    # 工频干扰 (50Hz)
    interference = 0.3 * np.sin(2 * np.pi * 50 * t)

    # 合成含噪声信号
    noisy = useful + interference

    # 滤波处理
    cleaned = notch.process(noisy, t)

    # 计算信噪比改善
    noise_before = noisy - useful
    noise_after = cleaned - useful

    snr_before = 10 * np.log10(np.mean(useful**2) / np.mean(noise_before**2))
    snr_after = 10 * np.log10(np.mean(useful**2) / np.mean(noise_after**2 + 1e-30))

    print(f"\n信号处理结果:")
    print(f"  输入信噪比: {snr_before:.1f} dB")
    print(f"  输出信噪比: {snr_after:.1f} dB")
    print(f"  信噪比改善: {snr_after - snr_before:.1f} dB")

    # 验证 50Hz 处的衰减
    f_test = np.array([10, 50, 100])
    mag = notch.bandstop.magnitude(f_test)
    print(f"\n频率响应:")
    print(f"  10Hz:  {mag[0]:.4f} ({20*np.log10(mag[0]+1e-10):.1f} dB)")
    print(f"  50Hz:  {mag[1]:.6f} ({20*np.log10(mag[1]+1e-10):.1f} dB)")
    print(f"  100Hz: {mag[2]:.4f} ({20*np.log10(mag[2]+1e-10):.1f} dB)")


def demo_signal_conditioning():
    """演示信号调理"""
    print("\n" + "=" * 60)
    print("信号调理演示")
    print("=" * 60)

    fs = 1000
    conditioner = SignalConditioner(fs)

    # 生成测试信号
    duration = 1.0
    t = np.arange(0, duration, 1.0 / fs)

    # 有用信号 + 直流偏移 + 工频干扰
    useful = np.sin(2 * np.pi * 20 * t)
    dc_offset = 2.0
    powerline = 0.5 * np.sin(2 * np.pi * 50 * t)
    signal = useful + dc_offset + powerline

    print(f"\n原始信号:")
    print(f"  直流分量: {np.mean(signal):.2f}")
    print(f"  有效值: {np.sqrt(np.mean(signal**2)):.2f}")

    # 去除直流偏移
    signal_no_dc = conditioner.remove_dc_offset(signal, t, cutoff=5.0)
    print(f"\n去除直流后:")
    print(f"  直流分量: {np.mean(signal_no_dc):.4f}")

    # 去除工频干扰
    signal_clean = conditioner.remove_powerline_hum(signal_no_dc, t, freq=50.0)
    print(f"\n去除工频干扰后:")
    print(f"  有效值: {np.sqrt(np.mean(signal_clean**2)):.2f}")

    # 带宽限制
    signal_limited = conditioner.band_limit(signal_clean, t, f_low=10, f_high=100)
    print(f"\n带宽限制后 (10-100Hz):")
    print(f"  有效值: {np.sqrt(np.mean(signal_limited**2)):.2f}")


def main():
    """主函数"""
    print("音频处理应用演示")
    print("模拟滤波器在实际音频处理中的应用\n")

    demo_audio_crossover()
    demo_equalizer()
    demo_noise_removal()
    demo_signal_conditioning()

    print("\n" + "=" * 60)
    print("演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
