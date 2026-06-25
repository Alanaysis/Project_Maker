#!/usr/bin/env python3
"""
基本滤波器演示
==============

演示各种模拟滤波器的基本用法和频率响应特性。
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
from src.lowpass import RCLowPass, RLLowPass
from src.highpass import RCHighPass, RLHighPass
from src.bandpass import RLCBandPass
from src.bandstop import RLCBandStop
from src.frequency_response import generate_log_freq, analyze_filter


def demo_lowpass():
    """演示低通滤波器"""
    print("=" * 60)
    print("低通滤波器演示")
    print("=" * 60)

    # RC 低通: R=1kΩ, C=1μF → fc ≈ 159Hz
    rc_lp = RCLowPass(R=1000, C=1e-6)
    print(f"\nRC 低通: {rc_lp}")
    print(f"  时间常数 τ = {rc_lp.tau*1000:.2f} ms")
    print(f"  截止频率 fc = {rc_lp.fc:.2f} Hz")

    # RL 低通: R=100Ω, L=0.1H → fc ≈ 159Hz
    rl_lp = RLLowPass(R=100, L=0.1)
    print(f"\nRL 低通: {rl_lp}")
    print(f"  时间常数 τ = {rl_lp.tau*1000:.2f} ms")
    print(f"  截止频率 fc = {rl_lp.fc:.2f} Hz")

    # 频率响应分析
    f = generate_log_freq(1, 1e5, 100)
    print(f"\n频率响应 (RC 低通):")
    print(f"  f=10Hz:   {rc_lp.magnitude_db(np.array([10]))[0]:.1f} dB")
    print(f"  f=fc:     {rc_lp.magnitude_db(np.array([rc_lp.fc]))[0]:.1f} dB")
    print(f"  f=1kHz:   {rc_lp.magnitude_db(np.array([1000]))[0]:.1f} dB")
    print(f"  f=10kHz:  {rc_lp.magnitude_db(np.array([10000]))[0]:.1f} dB")

    print(f"\n相位响应 (RC 低通):")
    print(f"  f=10Hz:   {rc_lp.phase(np.array([10]))[0]:.1f}°")
    print(f"  f=fc:     {rc_lp.phase(np.array([rc_lp.fc]))[0]:.1f}°")
    print(f"  f=1kHz:   {rc_lp.phase(np.array([1000]))[0]:.1f}°")


def demo_highpass():
    """演示高通滤波器"""
    print("\n" + "=" * 60)
    print("高通滤波器演示")
    print("=" * 60)

    # RC 高通: R=1kΩ, C=1μF → fc ≈ 159Hz
    rc_hp = RCHighPass(R=1000, C=1e-6)
    print(f"\nRC 高通: {rc_hp}")
    print(f"  截止频率 fc = {rc_hp.fc:.2f} Hz")

    # RL 高通: R=100Ω, L=0.1H → fc ≈ 159Hz
    rl_hp = RLHighPass(R=100, L=0.1)
    print(f"\nRL 高通: {rl_hp}")
    print(f"  截止频率 fc = {rl_hp.fc:.2f} Hz")

    print(f"\n频率响应 (RC 高通):")
    print(f"  f=10Hz:   {rc_hp.magnitude_db(np.array([10]))[0]:.1f} dB")
    print(f"  f=fc:     {rc_hp.magnitude_db(np.array([rc_hp.fc]))[0]:.1f} dB")
    print(f"  f=1kHz:   {rc_hp.magnitude_db(np.array([1000]))[0]:.1f} dB")
    print(f"  f=10kHz:  {rc_hp.magnitude_db(np.array([10000]))[0]:.1f} dB")


def demo_bandpass():
    """演示带通滤波器"""
    print("\n" + "=" * 60)
    print("带通滤波器演示")
    print("=" * 60)

    # RLC 带通: R=100Ω, L=10mH, C=1μF
    bp = RLCBandPass(R=100, L=0.01, C=1e-6)
    print(f"\nRLC 带通: {bp}")
    print(f"  中心频率 f0 = {bp.f0:.2f} Hz")
    print(f"  带宽 BW = {bp.bw:.2f} Hz")
    print(f"  品质因数 Q = {bp.Q:.2f}")
    print(f"  下截止频率 = {bp.lower_cutoff():.2f} Hz")
    print(f"  上截止频率 = {bp.upper_cutoff():.2f} Hz")

    print(f"\n频率响应:")
    test_freqs = [bp.f0/10, bp.f0/2, bp.f0, bp.f0*2, bp.f0*10]
    for freq in test_freqs:
        mag = bp.magnitude_db(np.array([freq]))[0]
        print(f"  f={freq:.0f}Hz: {mag:.1f} dB")


def demo_bandstop():
    """演示带阻滤波器"""
    print("\n" + "=" * 60)
    print("带阻滤波器演示")
    print("=" * 60)

    # RLC 带阻: R=100Ω, L=10mH, C=1μF
    bs = RLCBandStop(R=100, L=0.01, C=1e-6)
    print(f"\nRLC 带阻: {bs}")
    print(f"  中心频率 f0 = {bs.f0:.2f} Hz")
    print(f"  带宽 BW = {bs.bw:.2f} Hz")
    print(f"  品质因数 Q = {bs.Q:.2f}")

    print(f"\n频率响应:")
    test_freqs = [bs.f0/10, bs.f0/2, bs.f0, bs.f0*2, bs.f0*10]
    for freq in test_freqs:
        mag = bs.magnitude_db(np.array([freq]))[0]
        print(f"  f={freq:.0f}Hz: {mag:.1f} dB")


def demo_step_impulse():
    """演示时域响应"""
    print("\n" + "=" * 60)
    print("时域响应演示")
    print("=" * 60)

    filt = RCLowPass(R=1000, C=1e-6)
    tau = filt.tau

    t_values = [0, tau, 2*tau, 3*tau, 5*tau]
    print(f"\nRC 低通阶跃响应 (τ = {tau*1000:.2f} ms):")
    for t in t_values:
        if t == 0:
            print(f"  t=0:     0.000")
        else:
            val = filt.step_response(np.array([t]))[0]
            print(f"  t={t/tau:.0f}τ:    {val:.3f}")


def main():
    """主函数"""
    print("模拟滤波器基本演示")
    print("从零实现各种模拟滤波器\n")

    demo_lowpass()
    demo_highpass()
    demo_bandpass()
    demo_bandstop()
    demo_step_impulse()

    print("\n" + "=" * 60)
    print("演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
