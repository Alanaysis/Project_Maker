"""
03 - Spectrum Analysis Demo
频谱分析示例

Demonstrates spectrum analysis techniques:
    - Power spectral density
    - Peak detection
    - Window functions and spectral leakage
    - Frequency resolution
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.fft import fft
from src.dft import magnitude_spectrum, phase_spectrum, frequency_axis_positive, fftshift
from src.spectrum import (
    power_spectral_density,
    magnitude_to_db,
    detect_peaks,
    apply_window,
    spectral_leakage_example,
    estimate_frequency,
    compute_frequency_resolution,
)


def analyze_spectrum_basic():
    """Basic spectrum analysis of a composite signal."""
    sample_rate = 1000
    duration = 2.0
    N = int(sample_rate * duration)

    t = np.arange(N) / sample_rate
    signal = (np.sin(2 * np.pi * 30 * t) +
              0.7 * np.sin(2 * np.pi * 80 * t) +
              0.3 * np.sin(2 * np.pi * 150 * t) +
              0.1 * np.random.randn(N))

    X = fft(signal)
    mag = magnitude_spectrum(X)
    phase = phase_spectrum(X)
    freqs, n_pos = frequency_axis_positive(N, sample_rate)

    # Find peaks
    peaks = detect_peaks(freqs, mag, threshold_ratio=0.05)

    print('Peak Detection Results:')
    print(f'  {"Frequency (Hz)":>15s} | {"Magnitude":>12s}')
    print(f'  {"-"*15}s | {"-"*12}s')
    for freq, mag_val in peaks[:5]:
        print(f'  {freq:>15.1f} | {mag_val:>12.1f}')
    print()

    return signal, X, mag, phase, freqs


def analyze_window_effects():
    """Demonstrate the effect of different window functions."""
    sample_rate = 1000
    duration = 1.0
    N = int(sample_rate * duration)

    # Signal with frequency that doesn't align with bins
    t = np.arange(N) / sample_rate
    signal = np.sin(2 * np.pi * 45.5 * t)  # 45.5 Hz (not on bin boundary)

    windows = {
        'Rectangular (矩形)': 'rectangular',
        'Hann (汉宁)': 'hann',
        'Hamming (汉明)': 'hamming',
        'Blackman (布莱克曼)': 'blackman',
        'Bartlett (巴特利特)': 'bartlett',
    }

    fig, axes = plt.subplots(3, 1, figsize=(12, 10))

    # Time domain
    axes[0].plot(t, signal, linewidth=0.5)
    axes[0].set_title(f'Test Signal: 45.5 Hz (Non-integer bin)', fontsize=12)
    axes[0].set_xlabel('Time (s)')
    axes[0].set_ylabel('Amplitude')
    axes[0].grid(True, alpha=0.3)

    freqs, n_pos = frequency_axis_positive(N, sample_rate)

    for idx, (name, wtype) in enumerate(windows.items()):
        windowed = apply_window(signal, wtype)
        X = fft(windowed)
        mag = magnitude_spectrum(X)
        mag_db = magnitude_to_db(mag)

        # Plot windowed spectra
        ax = axes[1] if idx < 2 else axes[2]
        row = idx // 2
        ax.plot(freqs[:n_pos], mag_db[:n_pos], linewidth=0.8, label=name)
        ax.set_xlim(0, 100)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)

    axes[1].set_ylabel('|X(f)| dB')
    axes[2].set_ylabel('|X(f)| dB')
    axes[2].set_xlabel('Frequency (Hz)')

    # Mark actual frequency
    for ax in [axes[1], axes[2]]:
        ax.axvline(x=45.5, color='red', linestyle='--', alpha=0.5, label='45.5 Hz')

    plt.tight_layout()
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '03_window_effects.png')
    plt.savefig(out_path, dpi=100, bbox_inches='tight')
    print(f'Saved window effects plot: {out_path}')
    plt.close()


def analyze_spectral_leakage():
    """Demonstrate spectral leakage."""
    sample_rate = 1000
    N = 256

    leakage_data = spectral_leakage_example(sample_rate, 37.5, N)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Without window
    ax1.plot(leakage_data['freqs'], leakage_data['mag_rect'], linewidth=0.8)
    ax1.set_title('Spectral Leakage (No Window)', fontsize=12)
    ax1.set_xlabel('Frequency (Hz)')
    ax1.set_ylabel('|X(f)|')
    ax1.grid(True, alpha=0.3)
    ax1.axvline(x=leakage_data['signal_freq'], color='red', linestyle='--', alpha=0.5)

    # With Hann window
    ax2.plot(leakage_data['freqs'], leakage_data['mag_windowed'], linewidth=0.8)
    ax2.set_title('Reduced Leakage (Hann Window)', fontsize=12)
    ax2.set_xlabel('Frequency (Hz)')
    ax2.set_ylabel('|X(f)|')
    ax2.grid(True, alpha=0.3)
    ax2.axvline(x=leakage_data['signal_freq'], color='red', linestyle='--', alpha=0.5)

    plt.tight_layout()
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '03_spectral_leakage.png')
    plt.savefig(out_path, dpi=100, bbox_inches='tight')
    print(f'Saved spectral leakage plot: {out_path}')
    plt.close()

    print(f'Spectral Leakage Analysis:')
    print(f'  Signal frequency: {leakage_data["signal_freq"]} Hz')
    print(f'  Nearest bin:      {leakage_data["bin_freq"]} Hz')
    print(f'  Leakage present:  {leakage_data["leakage"]}')
    print(f'  Frequency resolution: {compute_frequency_resolution(sample_rate, N):.2f} Hz')
    print()


def analyze_power_spectrum():
    """Analyze power spectral density."""
    sample_rate = 1000
    duration = 2.0
    N = int(sample_rate * duration)

    t = np.arange(N) / sample_rate
    signal = (np.sin(2 * np.pi * 60 * t) +
              0.5 * np.sin(2 * np.pi * 120 * t))

    X = fft(signal)
    freqs, power = power_spectral_density(X, sample_rate)
    freqs_pos, n_pos = frequency_axis_positive(N, sample_rate)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    ax1.plot(freqs_pos[:n_pos], power[:n_pos], linewidth=1, color='blue')
    ax1.set_title('Power Spectral Density', fontsize=12)
    ax1.set_xlabel('Frequency (Hz)')
    ax1.set_ylabel('Power')
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, 250)
    ax1.axvline(x=60, color='green', linestyle='--', alpha=0.5)
    ax1.axvline(x=120, color='orange', linestyle='--', alpha=0.5)

    # PSD in dB
    power_db = magnitude_to_db(power)
    ax2.plot(freqs_pos[:n_pos], power_db[:n_pos], linewidth=1, color='red')
    ax2.set_title('Power Spectral Density (dB)', fontsize=12)
    ax2.set_xlabel('Frequency (Hz)')
    ax2.set_ylabel('Power (dB)')
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(0, 250)

    plt.tight_layout()
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '03_power_spectrum.png')
    plt.savefig(out_path, dpi=100, bbox_inches='tight')
    print(f'Saved power spectrum plot: {out_path}')
    plt.close()


def frequency_estimation_demo():
    """Demonstrate frequency estimation with sub-bin accuracy."""
    sample_rate = 1000
    duration = 1.0
    N = int(sample_rate * duration)

    # True frequency: 47.3 Hz (not on bin boundary)
    true_freq = 47.3
    t = np.arange(N) / sample_rate
    signal = np.sin(2 * np.pi * true_freq * t)

    X = fft(signal)
    mag = magnitude_spectrum(X)
    freqs, n_pos = frequency_axis_positive(N, sample_rate)

    peak_idx = np.argmax(mag[:n_pos])
    estimated_freq = estimate_frequency(freqs, mag, peak_idx)
    freq_resolution = compute_frequency_resolution(sample_rate, N)

    print('Frequency Estimation Demo:')
    print(f'  True frequency:     {true_freq:.1f} Hz')
    print(f'  Frequency resolution: {freq_resolution:.2f} Hz')
    print(f'  Peak bin:           {peak_idx} ({freqs[peak_idx]:.1f} Hz)')
    print(f'  Estimated frequency:{estimated_freq:.3f} Hz')
    print(f'  Estimation error:   {abs(estimated_freq - true_freq):.3f} Hz')
    print()


if __name__ == '__main__':
    print('=== Spectrum Analysis Demo / 频谱分析示例 ===')
    print()

    print('1. Basic Spectrum Analysis')
    print('-' * 40)
    analyze_spectrum_basic()

    print('2. Window Function Effects')
    print('-' * 40)
    analyze_window_effects()

    print('3. Spectral Leakage')
    print('-' * 40)
    analyze_spectral_leakage()

    print('4. Power Spectrum')
    print('-' * 40)
    analyze_power_spectrum()

    print('5. Frequency Estimation')
    print('-' * 40)
    frequency_estimation_demo()

    print('Done!')
