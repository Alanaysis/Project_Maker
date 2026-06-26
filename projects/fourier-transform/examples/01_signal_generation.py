"""
01 - Signal Generation Demo
信号生成示例

Demonstrates generating common signal types:
    - Sine wave
    - Square wave
    - Sawtooth wave
    - Triangular wave
    - Composite signal
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
from src.dft import magnitude_spectrum, frequency_axis_positive


def generate_sine_wave(sample_rate: float, frequency: float, duration: float) -> np.ndarray:
    """Generate a sine wave signal."""
    t = np.arange(int(sample_rate * duration)) / sample_rate
    return np.sin(2 * np.pi * frequency * t)


def generate_square_wave(sample_rate: float, frequency: float, duration: float) -> np.ndarray:
    """Generate a square wave signal."""
    t = np.arange(int(sample_rate * duration)) / sample_rate
    return np.sign(np.sin(2 * np.pi * frequency * t))


def generate_sawtooth_wave(sample_rate: float, frequency: float, duration: float) -> np.ndarray:
    """Generate a sawtooth wave signal."""
    t = np.arange(int(sample_rate * duration)) / sample_rate
    period = 1.0 / frequency
    return 2 * ((t / period) - np.floor((t / period) + 0.5))


def generate_triangle_wave(sample_rate: float, frequency: float, duration: float) -> np.ndarray:
    """Generate a triangle wave signal."""
    t = np.arange(int(sample_rate * duration)) / sample_rate
    period = 1.0 / frequency
    # Use arcsin of sine to create triangle wave
    return (2 / np.pi) * np.arcsin(np.sin(2 * np.pi * frequency * t))


def generate_composite_signal(sample_rate: float, duration: float) -> np.ndarray:
    """Generate a composite signal with multiple frequencies."""
    t = np.arange(int(sample_rate * duration)) / sample_rate
    # 50 Hz + 120 Hz + 200 Hz
    signal = (np.sin(2 * np.pi * 50 * t) +
              0.5 * np.sin(2 * np.pi * 120 * t) +
              0.3 * np.sin(2 * np.pi * 200 * t))
    return signal


def plot_signal_comparison():
    """Plot time-domain and frequency-domain of different signal types."""
    sample_rate = 1000  # Hz
    duration = 1.0  # seconds
    frequencies = [50, 120]  # Hz

    # Generate signals
    signals = {
        'Sine (正弦波)': generate_sine_wave(sample_rate, 50, duration),
        'Square (方波)': generate_square_wave(sample_rate, 50, duration),
        'Sawtooth (锯齿波)': generate_sawtooth_wave(sample_rate, 50, duration),
        'Triangle (三角波)': generate_triangle_wave(sample_rate, 50, duration),
    }

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.ravel()

    for idx, (name, signal) in enumerate(signals.items()):
        # Time domain
        t = np.arange(len(signal)) / sample_rate
        axes[idx].plot(t[:200], signal[:200], linewidth=0.8)
        axes[idx].set_title(f'{name} - Time Domain (First 200 samples)', fontsize=10)
        axes[idx].set_xlabel('Time (s)')
        axes[idx].set_ylabel('Amplitude')
        axes[idx].grid(True, alpha=0.3)

        # Frequency domain
        X = fft(signal)
        mag = magnitude_spectrum(X)
        freqs, n_pos = frequency_axis_positive(len(signal), sample_rate)

        axes[idx + 4].plot(freqs[:n_pos], mag[:n_pos], linewidth=0.8, color='blue')
        axes[idx + 4].set_title(f'{name} - Magnitude Spectrum', fontsize=10)
        axes[idx + 4].set_xlabel('Frequency (Hz)')
        axes[idx + 4].set_ylabel('|X(f)|')
        axes[idx + 4].grid(True, alpha=0.3)
        axes[idx + 4].set_xlim(0, 300)

    plt.tight_layout()
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '01_signal_comparison.png')
    plt.savefig(out_path, dpi=100, bbox_inches='tight')
    print(f'Saved: {out_path}')
    plt.close()


def plot_composite_signal():
    """Plot the composite signal and its spectrum."""
    sample_rate = 1000
    duration = 1.0

    signal = generate_composite_signal(sample_rate, duration)
    t = np.arange(len(signal)) / sample_rate

    X = fft(signal)
    mag = magnitude_spectrum(X)
    freqs, n_pos = frequency_axis_positive(len(signal), sample_rate)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

    # Time domain
    ax1.plot(t, signal, linewidth=0.5)
    ax1.set_title('Composite Signal: 50Hz + 120Hz + 200Hz', fontsize=12)
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Amplitude')
    ax1.grid(True, alpha=0.3)

    # Frequency domain
    ax2.plot(freqs[:n_pos], mag[:n_pos], linewidth=0.8, color='red')
    ax2.set_title('Frequency Spectrum (FFT)', fontsize=12)
    ax2.set_xlabel('Frequency (Hz)')
    ax2.set_ylabel('|X(f)|')
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(0, 400)

    # Mark the known frequencies
    for f in [50, 120, 200]:
        ax2.axvline(x=f, color='green', linestyle='--', alpha=0.5, label=f'{f} Hz')
    ax2.legend()

    plt.tight_layout()
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '01_composite_signal.png')
    plt.savefig(out_path, dpi=100, bbox_inches='tight')
    print(f'Saved: {out_path}')
    plt.close()


if __name__ == '__main__':
    print('=== Signal Generation Demo / 信号生成示例 ===')
    print()

    sample_rate = 1000
    duration = 1.0

    print('Generating signals...')
    sine = generate_sine_wave(sample_rate, 50, duration)
    square = generate_square_wave(sample_rate, 50, duration)
    sawtooth = generate_sawtooth_wave(sample_rate, 50, duration)
    triangle = generate_triangle_wave(sample_rate, 50, duration)
    composite = generate_composite_signal(sample_rate, duration)

    print(f'  Sine wave:      {len(sine)} samples, amplitude range [{sine.min():.3f}, {sine.max():.3f}]')
    print(f'  Square wave:    {len(square)} samples, amplitude range [{square.min():.3f}, {square.max():.3f}]')
    print(f'  Sawtooth wave:  {len(sawtooth)} samples, amplitude range [{sawtooth.min():.3f}, {sawtooth.max():.3f}]')
    print(f'  Triangle wave:  {len(triangle)} samples, amplitude range [{triangle.min():.3f}, {triangle.max():.3f}]')
    print(f'  Composite:      {len(composite)} samples, amplitude range [{composite.min():.3f}, {composite.max():.3f}]')
    print()

    # Analyze each signal
    print('FFT Analysis:')
    for name, sig in [('Sine', sine), ('Square', square), ('Sawtooth', sawtooth), ('Triangle', triangle)]:
        X = fft(sig)
        mag = magnitude_spectrum(X)
        freqs, n_pos = frequency_axis_positive(len(sig), sample_rate)
        peak_idx = np.argmax(mag[:n_pos])
        print(f'  {name:10s}: Peak at {freqs[peak_idx]:.1f} Hz, magnitude = {mag[peak_idx]:.1f}')
    print()

    plot_signal_comparison()
    plot_composite_signal()

    print('Done! Check the generated PNG files.')
