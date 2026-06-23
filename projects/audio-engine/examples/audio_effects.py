#!/usr/bin/env python3
"""
音频特效示例

演示各种音频效果器的使用。
"""

import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.audio_signal import AudioSignal
from src.effects import Delay, Reverb, Chorus, Distortion


def delay_effect_example():
    """延迟效果示例"""
    print("=" * 60)
    print("延迟效果示例")
    print("=" * 60)

    sample_rate = 44100

    # 创建短脉冲信号
    signal_data = np.zeros(sample_rate)
    signal_data[0] = 1.0  # 脉冲
    signal = AudioSignal(signal_data, sample_rate)

    print("原始信号: 单个脉冲")

    # 延迟效果
    delay = Delay(
        delay_time=0.1,    # 100ms 延迟
        feedback=0.6,      # 60% 反馈
        mix=0.5,           # 50% 混合
        sample_rate=sample_rate
    )
    delayed = delay.apply(signal)

    print(f"\n延迟参数:")
    print(f"  延迟时间: {delay.delay_time * 1000:.0f} ms")
    print(f"  反馈量: {delay.feedback * 100:.0f}%")
    print(f"  混合比例: {delay.mix * 100:.0f}%")

    # 检测回声
    delay_samples = int(0.1 * sample_rate)
    echoes = []
    for i in range(1, 6):
        pos = i * delay_samples
        if pos < len(delayed.data):
            echoes.append(delayed.data[pos])

    print(f"\n检测到的回声幅度:")
    for i, amp in enumerate(echoes):
        print(f"  回声 {i + 1}: {amp:.4f}")


def reverb_effect_example():
    """混响效果示例"""
    print("\n" + "=" * 60)
    print("混响效果示例")
    print("=" * 60)

    sample_rate = 44100

    # 创建脉冲信号
    signal_data = np.zeros(sample_rate)
    signal_data[0] = 1.0
    signal = AudioSignal(signal_data, sample_rate)

    # 不同房间大小的混响
    room_sizes = [0.2, 0.5, 0.8]
    damping = 0.5

    print("混响参数:")
    print(f"  阻尼: {damping}")

    for size in room_sizes:
        reverb = Reverb(
            room_size=size,
            damping=damping,
            mix=0.5,
            sample_rate=sample_rate
        )
        reverbed = reverb.apply(signal)

        # 计算混响尾能量
        mid = len(signal) // 2
        tail_energy = np.sum(reverbed.data[mid:] ** 2)

        print(f"\n  房间大小 {size:.1f}:")
        print(f"    混响尾能量: {tail_energy:.6f}")

        # 估计 RT60（混响时间）
        # 简单估计：能量衰减到初始的百万分之一
        initial_energy = np.sum(reverbed.data[:1000] ** 2)
        if initial_energy > 0:
            decay_ratio = tail_energy / initial_energy
            print(f"    衰减比: {decay_ratio:.6f}")


def chorus_effect_example():
    """合唱效果示例"""
    print("\n" + "=" * 60)
    print("合唱效果示例")
    print("=" * 60)

    sample_rate = 44100
    duration = 1.0

    # 创建正弦信号
    signal = AudioSignal.from_tone(440, duration=duration, sample_rate=sample_rate)

    print("原始信号: 440 Hz 正弦波")

    # 合唱效果
    chorus = Chorus(
        rate=2.0,       # LFO 频率 2 Hz
        depth=0.003,    # 调制深度 3ms
        mix=0.5,
        sample_rate=sample_rate
    )
    chorused = chorus.apply(signal)

    print(f"\n合唱参数:")
    print(f"  LFO 频率: {chorus.rate} Hz")
    print(f"  调制深度: {chorus.depth * 1000:.1f} ms")
    print(f"  混合比例: {chorus.mix * 100:.0f}%")

    # 分析频谱变化
    spectrum_orig = np.abs(np.fft.fft(signal.data))
    spectrum_chorus = np.abs(np.fft.fft(chorused.data))

    # 合唱应该产生边带
    freqs = np.fft.fftfreq(len(signal.data), 1.0 / sample_rate)
    idx_440 = np.argmin(np.abs(freqs - 440))

    # 检查主频率附近的频谱宽度
    threshold = spectrum_orig[idx_440] * 0.1
    width_orig = np.sum(spectrum_orig[idx_440 - 50:idx_440 + 50] > threshold)
    width_chorus = np.sum(spectrum_chorus[idx_440 - 50:idx_440 + 50] > threshold)

    print(f"\n频谱分析:")
    print(f"  原始信号频谱宽度: {width_orig} 个频率点")
    print(f"  合唱后频谱宽度: {width_chorus} 个频率点")


def distortion_effect_example():
    """失真效果示例"""
    print("\n" + "=" * 60)
    print("失真效果示例")
    print("=" * 60)

    sample_rate = 44100
    duration = 0.1

    # 创建正弦信号
    signal = AudioSignal.from_tone(440, duration=duration, sample_rate=sample_rate)

    print("原始信号: 440 Hz 正弦波")

    # 软失真
    soft_dist = Distortion(drive=0.3, mix=1.0, clip_type='soft')
    soft_result = soft_dist.apply(signal)

    # 硬失真
    hard_dist = Distortion(drive=0.3, mix=1.0, clip_type='hard')
    hard_result = hard_dist.apply(signal)

    # 分析谐波
    def count_harmonics(data, threshold=0.1):
        spectrum = np.abs(np.fft.fft(data))
        freqs = np.fft.fftfreq(len(data), 1.0 / sample_rate)
        idx_440 = np.argmin(np.abs(freqs - 440))
        max_amp = spectrum[idx_440]
        peaks = np.sum(spectrum[:len(data) // 2] > max_amp * threshold)
        return peaks

    orig_harmonics = count_harmonics(signal.data)
    soft_harmonics = count_harmonics(soft_result.data)
    hard_harmonics = count_harmonics(hard_result.data)

    print(f"\n谐波分析 (>10% 主频率幅度):")
    print(f"  原始信号: {orig_harmonics} 个峰")
    print(f"  软失真: {soft_harmonics} 个峰")
    print(f"  硬失真: {hard_harmonics} 个峰")

    print(f"\n失真产生谐波，使音色更丰富")


def combined_effects_example():
    """组合效果示例"""
    print("\n" + "=" * 60)
    print("组合效果示例（吉他效果链）")
    print("=" * 60)

    sample_rate = 44100
    duration = 0.5

    # 创建吉他-like 信号（多个谐波）
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    signal_data = (np.sin(2 * np.pi * 330 * t) +        # E4
                   0.5 * np.sin(2 * np.pi * 660 * t) +  # E5
                   0.3 * np.sin(2 * np.pi * 990 * t))   # E6
    signal = AudioSignal(signal_data, sample_rate)

    print("原始信号: E4 和声 (330, 660, 990 Hz)")

    # 效果链：失真 -> 延迟 -> 混响
    print("\n效果链: 失真 -> 延迟 -> 混响")

    # 1. 失真
    distortion = Distortion(drive=0.4, mix=0.7)
    processed = distortion.apply(signal)
    print("  1. 失真 (drive=0.4, mix=70%)")

    # 2. 延迟
    delay = Delay(delay_time=0.15, feedback=0.3, mix=0.3, sample_rate=sample_rate)
    processed = delay.apply(processed)
    print("  2. 延迟 (150ms, feedback=30%, mix=30%)")

    # 3. 混响
    reverb = Reverb(room_size=0.4, damping=0.6, mix=0.2, sample_rate=sample_rate)
    processed = reverb.apply(processed)
    print("  3. 混响 (room=0.4, damping=0.6, mix=20%)")

    print(f"\n处理后信号: {processed}")


if __name__ == "__main__":
    delay_effect_example()
    reverb_effect_example()
    chorus_effect_example()
    distortion_effect_example()
    combined_effects_example()
