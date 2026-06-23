#!/usr/bin/env python3
"""
混音和降噪示例

演示混音器和降噪器的使用。
"""

import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.audio_signal import AudioSignal
from src.mixer import Mixer
from src.denoiser import Denoiser
from src.equalizer import Equalizer, GraphicEqualizer


def mixing_example():
    """混音示例"""
    print("=" * 60)
    print("混音示例")
    print("=" * 60)

    sample_rate = 44100
    duration = 1.0

    # 创建多个音轨
    # 鼓（低频脉冲）
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    kick = np.zeros_like(t)
    for i in range(0, len(t), sample_rate // 2):  # 每 0.5 秒一个鼓点
        if i < len(kick):
            kick[i:i + 100] = np.sin(2 * np.pi * 60 * t[:100]) * np.exp(-t[:100] * 20)
    drum_signal = AudioSignal(kick, sample_rate)

    # 贝斯（低音旋律）
    bass = 0.5 * np.sin(2 * np.pi * 110 * t)  # A2
    bass_signal = AudioSignal(bass, sample_rate)

    # 主旋律（中音）
    melody = 0.3 * np.sin(2 * np.pi * 440 * t)  # A4
    melody_signal = AudioSignal(melody, sample_rate)

    # 和声（高音）
    harmony = 0.2 * np.sin(2 * np.pi * 880 * t)  # A5
    harmony_signal = AudioSignal(harmony, sample_rate)

    print("音轨:")
    print("  1. 鼓 (60 Hz 脉冲)")
    print("  2. 贝斯 (110 Hz)")
    print("  3. 主旋律 (440 Hz)")
    print("  4. 和声 (880 Hz)")

    # 创建混音器
    mixer = Mixer(sample_rate=sample_rate)

    # 添加音轨
    mixer.add_track(drum_signal, name="Drums", volume=0.8, pan=0.0)
    mixer.add_track(bass_signal, name="Bass", volume=0.7, pan=-0.2)
    mixer.add_track(melody_signal, name="Melody", volume=0.6, pan=0.3)
    mixer.add_track(harmony_signal, name="Harmony", volume=0.4, pan=-0.3)

    print("\n混音设置:")
    for i, name in enumerate(mixer.get_track_names()):
        track = mixer.get_track(i)
        print(f"  {name}: 音量={track.volume:.1f}, 声像={track.pan:.1f}")

    # 渲染混音
    left, right = mixer.render()
    mono = mixer.render_to_mono()

    print(f"\n混音结果:")
    print(f"  左声道: {left}")
    print(f"  右声道: {right}")
    print(f"  单声道: {mono}")

    # 频谱分析
    freqs, mag = mono.get_spectrum()
    peaks = np.argsort(mag)[-4:][::-1]
    print(f"\n混音后的主要频率:")
    for idx in peaks:
        print(f"  {freqs[idx]:.1f} Hz: {mag[idx]:.4f}")


def denoising_example():
    """降噪示例"""
    print("\n" + "=" * 60)
    print("降噪示例")
    print("=" * 60)

    sample_rate = 44100
    duration = 1.0

    # 创建纯净信号
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    clean = np.sin(2 * np.pi * 440 * t)

    # 添加噪声
    noise_level = 0.3
    noise = np.random.randn(len(t)) * noise_level
    noisy = clean + noise

    signal = AudioSignal(noisy, sample_rate)

    print("信号:")
    print(f"  纯净信号: 440 Hz 正弦波")
    print(f"  噪声水平: {noise_level}")
    print(f"  信噪比: {20 * np.log10(1.0 / noise_level):.1f} dB")

    # 创建降噪器
    denoiser = Denoiser(
        noise_factor=2.0,
        spectral_floor=0.1,
        sample_rate=sample_rate
    )

    # 估计噪声（使用信号开头的噪声段）
    denoiser.estimate_noise(signal, noise_duration=0.1)
    print(f"\n噪声估计: 使用前 0.1 秒的信号")

    # 应用降噪
    denoised = denoiser.apply(signal)

    # 评估降噪效果
    # 计算残余噪声
    residual_noise = denoised.data[:1000] - clean[:1000]
    residual_level = np.sqrt(np.mean(residual_noise ** 2))

    print(f"\n降噪结果:")
    print(f"  残余噪声水平: {residual_level:.4f}")
    print(f"  噪声降低: {(1 - residual_level / noise_level) * 100:.1f}%")

    # 频谱对比
    freqs_noisy, mag_noisy = signal.get_spectrum()
    freqs_clean, mag_clean = AudioSignal(clean, sample_rate).get_spectrum()
    freqs_denoised, mag_denoised = denoised.get_spectrum()

    idx_440 = np.argmin(np.abs(freqs_noisy - 440))
    print(f"\n440 Hz 幅度对比:")
    print(f"  含噪信号: {mag_noisy[idx_440]:.4f}")
    print(f"  降噪后: {mag_denoised[idx_440]:.4f}")
    print(f"  纯净信号: {mag_clean[idx_440]:.4f}")


def equalizer_example():
    """均衡器示例"""
    print("\n" + "=" * 60)
    print("均衡器示例")
    print("=" * 60)

    sample_rate = 44100
    duration = 0.5

    # 创建包含多个频率的信号
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    signal_data = (np.sin(2 * np.pi * 100 * t) +   # 低音
                   np.sin(2 * np.pi * 1000 * t) +   # 中音
                   np.sin(2 * np.pi * 5000 * t))    # 高音
    signal = AudioSignal(signal_data, sample_rate)

    print("原始信号: 100 Hz + 1000 Hz + 5000 Hz")

    # 参数均衡器
    eq = Equalizer(sample_rate=sample_rate)
    eq.add_band(100, gain_db=6.0, q_factor=1.0)    # 提升低音
    eq.add_band(1000, gain_db=-3.0, q_factor=2.0)   # 衰减中音
    eq.add_band(5000, gain_db=4.0, q_factor=1.5)    # 提升高音

    print("\n均衡设置:")
    for band in eq.bands:
        print(f"  {band.frequency} Hz: {band.gain_db:+.1f} dB (Q={band.q_factor})")

    equalized = eq.apply(signal)

    # 频谱对比
    freqs_orig, mag_orig = signal.get_spectrum()
    freqs_eq, mag_eq = equalized.get_spectrum()

    print("\n频谱变化:")
    for freq in [100, 1000, 5000]:
        idx_orig = np.argmin(np.abs(freqs_orig - freq))
        idx_eq = np.argmin(np.abs(freqs_eq - freq))
        gain = mag_eq[idx_eq] / mag_orig[idx_orig] if mag_orig[idx_orig] > 0 else 0
        gain_db = 20 * np.log10(gain) if gain > 0 else -100
        print(f"  {freq} Hz: {gain_db:+.1f} dB")


def graphic_equalizer_example():
    """图示均衡器示例"""
    print("\n" + "=" * 60)
    print("图示均衡器示例")
    print("=" * 60)

    sample_rate = 44100
    duration = 0.5

    # 创建白噪声
    signal = AudioSignal.from_noise(duration=duration, sample_rate=sample_rate, amplitude=0.5)
    print("输入信号: 白噪声")

    # 创建图示均衡器
    geq = GraphicEqualizer(sample_rate=sample_rate)

    # 设置 "微笑曲线"（提升低音和高音）
    gains = [4, 3, 1, 0, -1, -1, 0, 1, 3, 4]
    geq.set_gains(gains)

    print("\n均衡曲线（微笑曲线）:")
    for freq, gain in zip(geq.frequencies, geq.gains):
        bar = "+" * int(abs(gain)) if gain > 0 else "-" * int(abs(gain))
        print(f"  {freq:>6.0f} Hz: {gain:+.1f} dB {bar}")

    # 应用均衡
    equalized = geq.apply(signal)

    # 频谱对比
    freqs_orig, mag_orig = signal.get_spectrum()
    freqs_eq, mag_eq = equalized.get_spectrum()

    print("\n各频段变化:")
    for freq in geq.frequencies:
        idx_orig = np.argmin(np.abs(freqs_orig - freq))
        idx_eq = np.argmin(np.abs(freqs_eq - freq))
        if mag_orig[idx_orig] > 0:
            gain = mag_eq[idx_eq] / mag_orig[idx_orig]
            gain_db = 20 * np.log10(gain)
            print(f"  {freq:>6.0f} Hz: {gain_db:+.1f} dB")


def complete_processing_pipeline():
    """完整处理流水线示例"""
    print("\n" + "=" * 60)
    print("完整音频处理流水线")
    print("=" * 60)

    sample_rate = 44100
    duration = 2.0

    # 创建 "录音" 信号（语音 + 噪声）
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)

    # 语音-like 信号（多个谐波）
    speech = (0.5 * np.sin(2 * np.pi * 200 * t) +
              0.3 * np.sin(2 * np.pi * 400 * t) +
              0.2 * np.sin(2 * np.pi * 600 * t))

    # 背景噪声
    noise = np.random.randn(len(t)) * 0.1

    # 50Hz 工频干扰
    hum = 0.05 * np.sin(2 * np.pi * 50 * t)

    # 混合
    recording = speech + noise + hum
    signal = AudioSignal(recording, sample_rate)

    print("原始录音:")
    print("  - 语音信号 (200, 400, 600 Hz)")
    print("  - 随机噪声")
    print("  - 50 Hz 工频干扰")

    # 处理流水线
    print("\n处理流水线:")

    # 1. 去除工频干扰
    from src.filters import NotchFilter
    notch = NotchFilter(center_freq=50, bandwidth=20, sample_rate=sample_rate)
    processed = notch.apply(signal)
    print("  1. 去除 50 Hz 工频干扰")

    # 2. 降噪
    denoiser = Denoiser(noise_factor=1.5, spectral_floor=0.2, sample_rate=sample_rate)
    denoiser.estimate_noise(processed, noise_duration=0.2)
    processed = denoiser.apply(processed)
    print("  2. 频谱减法降噪")

    # 3. 均衡（提升语音频段）
    eq = Equalizer(sample_rate=sample_rate)
    eq.add_band(200, gain_db=3.0, q_factor=1.0)   # 提升基频
    eq.add_band(400, gain_db=2.0, q_factor=1.5)   # 提升二次谐波
    eq.add_band(3000, gain_db=-2.0, q_factor=1.0)  # 衰减高频噪声
    processed = eq.apply(processed)
    print("  3. 均衡处理（提升语音频段）")

    # 4. 归一化
    processed = processed.normalize(target_level=0.8)
    print("  4. 归一化")

    print(f"\n处理结果: {processed}")

    # 对比
    print("\n处理前后对比:")
    print(f"  原始信号峰值: {np.max(np.abs(signal.data)):.4f}")
    print(f"  处理后峰值: {np.max(np.abs(processed.data)):.4f}")


if __name__ == "__main__":
    mixing_example()
    denoising_example()
    equalizer_example()
    graphic_equalizer_example()
    complete_processing_pipeline()
