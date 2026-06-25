"""
音频采样演示
=============

演示音频信号的采样和量化。
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.audio_sampling import (
    AudioSampler,
    resample_audio,
    demonstrate_audio_quantization,
    generate_test_tone,
)


def demo_audio_presets():
    """音频预设演示"""
    print("=" * 60)
    print("音频采样预设演示")
    print("=" * 60)

    presets = ['telephone', 'radio', 'cd', 'dvd', 'studio']

    print("预设      | 采样率    | 量化位数 | 声道 | 比特率")
    print("-" * 55)

    for preset in presets:
        sampler = AudioSampler.from_preset(preset)
        info = sampler.info
        print(f"{preset:9s} | {info['采样频率']:9s} | {info['量化位数']:8d} | {info['声道数']:4d} | {info['比特率']}")


def demo_audio_quantization():
    """音频量化演示"""
    print("\n" + "=" * 60)
    print("音频量化演示")
    print("=" * 60)

    # 生成测试音调
    freq = 440  # A4 音符
    duration = 0.1
    fs = 44100

    t, signal = generate_test_tone(freq, duration, fs)

    print(f"测试音调: {freq} Hz (A4)")
    print(f"采样频率: {fs} Hz")
    print(f"持续时间: {duration} s")
    print(f"采样点数: {len(signal)}")
    print()

    # 不同量化位数
    bits_list = [4, 8, 12, 16, 24]

    print("量化位数 | SQNR (dB) | 理论 SQNR | 量化电平数")
    print("-" * 50)

    for bits in bits_list:
        sampler = AudioSampler(fs=fs, bits=bits)
        quantized, indices = sampler.quantize(signal)
        sqnr = sampler.quantizer.sqnr(signal)

        print(f"  {bits:2d} bit | {sqnr:9.2f} | {sampler.quantizer.theoretical_sqnr:9.2f} | {2**bits:10d}")


def demo_resampling():
    """音频重采样演示"""
    print("\n" + "=" * 60)
    print("音频重采样演示")
    print("=" * 60)

    # 原始信号
    fs_original = 44100
    freq = 1000
    duration = 0.01

    t, signal = generate_test_tone(freq, duration, fs_original)

    print(f"原始采样率: {fs_original} Hz")
    print(f"信号频率: {freq} Hz")
    print(f"原始采样点数: {len(signal)}")
    print()

    # 重采样到不同采样率
    target_rates = [8000, 22050, 48000, 96000]

    print("目标采样率 | 重采样点数 | 点数比")
    print("-" * 40)

    for fs_target in target_rates:
        resampled, fs = resample_audio(signal, fs_original, fs_target)
        ratio = len(resampled) / len(signal)
        print(f"  {fs_target:6d} Hz | {len(resampled):10d} | {ratio:.2f}")


def demo_nyquist_in_audio():
    """奈奎斯特定理在音频中的应用"""
    print("\n" + "=" * 60)
    print("奈奎斯特定理在音频中的应用")
    print("=" * 60)

    print("人耳听觉范围: 20 Hz ~ 20 kHz")
    print("奈奎斯特率: 2 * 20 kHz = 40 kHz")
    print()
    print("常用音频采样率:")
    print("  - 8 kHz:  电话音质 (最高 4 kHz)")
    print("  - 22 kHz: AM 广播音质 (最高 11 kHz)")
    print("  - 44.1 kHz: CD 音质 (最高 22.05 kHz)")
    print("  - 48 kHz: DVD 音质 (最高 24 kHz)")
    print("  - 96 kHz: 高保真 (最高 48 kHz)")
    print()
    print("为什么 CD 采样率是 44.1 kHz?")
    print("  - 人耳最高听觉: 20 kHz")
    print("  - 奈奎斯特率: 40 kHz")
    print("  - 需要过渡带: ~4 kHz")
    print("  - 总计: 44 kHz")
    print("  - 44.1 kHz 来自早期数字音频标准")


def demo_pcm_encoding():
    """PCM 编码演示"""
    print("\n" + "=" * 60)
    print("PCM 编码演示")
    print("=" * 60)

    # 生成简单信号
    t, signal = generate_test_tone(440, 0.001, 8000)

    sampler = AudioSampler(fs=8000, bits=8)

    # 编码
    pcm = sampler.encode(signal)

    # 解码
    decoded = sampler.decode(pcm)

    print(f"采样频率: {sampler.fs} Hz")
    print(f"量化位数: {sampler.bits}")
    print(f"采样点数: {len(signal)}")
    print()
    print("PCM 编码示例 (前 10 个样本):")
    print("  原始值    | PCM 编码 | 解码值")
    print("  " + "-" * 35)

    for i in range(min(10, len(signal))):
        print(f"  {signal[i]:8.4f} | {pcm[i]:8d} | {decoded[i]:8.4f}")


if __name__ == "__main__":
    demo_audio_presets()
    demo_audio_quantization()
    demo_resampling()
    demo_nyquist_in_audio()
    demo_pcm_encoding()
