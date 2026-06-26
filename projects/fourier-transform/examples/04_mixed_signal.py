"""
04 - Mixed Signal Decomposition Demo
混合信号分解示例

Demonstrates decomposing a complex mixed signal into its frequency components:
    - Generate a signal with known frequency components
    - Apply FFT to find the components
    - Reconstruct the signal from identified peaks
    - Compare original and reconstructed signals
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
from src.spectrum import (
    detect_peaks,
    apply_window,
    magnitude_to_db,
)
from src.inverse import inverse_fft


def generate_mixed_signal(sample_rate: float, duration: float) -> np.ndarray:
    """Generate a complex mixed signal."""
    t = np.arange(int(sample_rate * duration)) / sample_rate
    # Multiple frequency components with noise
    signal = (
        1.0 * np.sin(2 * np.pi * 25 * t) +      # 25 Hz, amplitude 1.0
        0.6 * np.sin(2 * np.pi * 60 * t) +      # 60 Hz, amplitude 0.6
        0.3 * np.sin(2 * np.pi * 100 * t) +     # 100 Hz, amplitude 0.3
        0.15 * np.sin(2 * np.pi * 180 * t) +    # 180 Hz, amplitude 0.15
        0.05 * np.random.randn(len(t))           # Noise
    )
    return signal, t


def decompose_signal(signal: np.ndarray, sample_rate: float, n_peaks: int = 5) -> dict:
    """Decompose a signal into its dominant frequency components."""
    N = len(signal)

    # Apply Hann window to reduce leakage
    windowed = apply_window(signal, 'hann')

    # Compute FFT
    X = fft(windowed)
    mag = magnitude_spectrum(X)
    freqs, n_pos = frequency_axis_positive(N, sample_rate)

    # Detect peaks
    peaks = detect_peaks(freqs, mag, threshold_ratio=0.05)

    # Get top N peaks
    top_peaks = peaks[:n_peaks]

    # Estimate frequencies with sub-bin accuracy
    estimated_components = []
    for freq, mag_val in top_peaks:
        # Find closest bin
        bin_idx = int(round(freq * N / sample_rate))
        bin_idx = min(bin_idx, n_pos - 1)

        # Quadratic interpolation for amplitude
        if 0 < bin_idx < n_pos - 1:
            p1 = mag[bin_idx - 1]
            p2 = mag[bin_idx]
            p3 = mag[bin_idx + 1]
            denom = p1 - 2 * p2 + p3
            if abs(denom) > 1e-10:
                delta = 0.5 * (p1 - p3) / denom
                corrected_mag = p2 - (p1 - p3) ** 2 / (8 * denom)
            else:
                corrected_mag = p2
                delta = 0
        else:
            corrected_mag = mag[bin_idx]
            delta = 0

        estimated_components.append({
            'frequency': freq,
            'magnitude': corrected_mag,
            'bin_idx': bin_idx,
            'delta': delta,
        })

    return {
        'freqs': freqs,
        'magnitude': mag,
        'peaks': top_peaks,
        'components': estimated_components,
    }


def reconstruct_from_peaks(signal: np.ndarray, components: list, sample_rate: float) -> np.ndarray:
    """Reconstruct a signal from identified frequency components."""
    N = len(signal)
    t = np.arange(N) / sample_rate
    reconstructed = np.zeros(N)

    for comp in components:
        freq = comp['frequency']
        amplitude = comp['magnitude'] / (N / 2)  # Scale back from FFT magnitude
        reconstructed += amplitude * np.sin(2 * np.pi * freq * t)

    return reconstructed


def plot_decomposition():
    """Create visualization of the signal decomposition."""
    sample_rate = 1000
    duration = 2.0

    signal, t = generate_mixed_signal(sample_rate, duration)
    result = decompose_signal(signal, sample_rate, n_peaks=5)
    reconstructed = reconstruct_from_peaks(signal, result['components'], sample_rate)

    fig, axes = plt.subplots(4, 1, figsize=(14, 12))

    # Original signal (first 500 samples)
    plot_len = min(500, len(signal))
    axes[0].plot(t[:plot_len], signal[:plot_len], linewidth=0.5)
    axes[0].set_title('Original Mixed Signal (First 500 samples)', fontsize=12)
    axes[0].set_xlabel('Time (s)')
    axes[0].set_ylabel('Amplitude')
    axes[0].grid(True, alpha=0.3)

    # Magnitude spectrum
    axes[1].plot(result['freqs'], result['magnitude'], linewidth=0.8)
    for comp in result['components']:
        axes[1].axvline(x=comp['frequency'], color='red', linestyle='--', alpha=0.5)
    axes[1].set_title('Frequency Spectrum (Detected Peaks)', fontsize=12)
    axes[1].set_xlabel('Frequency (Hz)')
    axes[1].set_ylabel('|X(f)|')
    axes[1].grid(True, alpha=0.3)
    axes[1].set_xlim(0, 300)

    # Bar chart of detected peaks
    peak_freqs = [c['frequency'] for c in result['components']]
    peak_mags = [c['magnitude'] for c in result['components']]
    bar_colors = ['red', 'orange', 'green', 'blue', 'purple']
    axes[2].bar(peak_freqs, peak_mags, color=bar_colors[:len(peak_freqs)], alpha=0.7)
    axes[2].set_title('Detected Frequency Components', fontsize=12)
    axes[2].set_xlabel('Frequency (Hz)')
    axes[2].set_ylabel('Magnitude')
    axes[2].grid(True, alpha=0.3, axis='y')
    for i, comp in enumerate(result['components']):
        axes[2].text(comp['frequency'], comp['magnitude'] + 5,
                     f'{comp["frequency"]:.1f} Hz', ha='center', fontsize=8)

    # Comparison: original vs reconstructed
    axes[3].plot(t[:plot_len], signal[:plot_len], linewidth=0.5, label='Original', alpha=0.7)
    axes[3].plot(t[:plot_len], reconstructed[:plot_len], linewidth=1.0,
                 label='Reconstructed', color='red')
    axes[3].set_title('Original vs Reconstructed Signal', fontsize=12)
    axes[3].set_xlabel('Time (s)')
    axes[3].set_ylabel('Amplitude')
    axes[3].legend()
    axes[3].grid(True, alpha=0.3)

    plt.tight_layout()
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '04_decomposition.png')
    plt.savefig(out_path, dpi=100, bbox_inches='tight')
    print(f'Saved decomposition plot: {out_path}')
    plt.close()


def print_decomposition_report(result: dict):
    """Print a report of the decomposition results."""
    print('Signal Decomposition Report:')
    print('=' * 50)
    print(f'  {"Component":>10s} | {"Frequency":>10s} | {"Magnitude":>10s}')
    print(f'  {"-"*10}s | {"-"*10}s | {"-"*10}s')
    for i, comp in enumerate(result['components']):
        print(f'  {i+1:>10d} | {comp["frequency"]:>10.1f} | {comp["magnitude"]:>10.1f}')
    print('=' * 50)
    print()


if __name__ == '__main__':
    print('=== Mixed Signal Decomposition / 混合信号分解 ===')
    print()

    sample_rate = 1000
    duration = 2.0

    print('1. Generating mixed signal...')
    signal, t = generate_mixed_signal(sample_rate, duration)
    print(f'   Signal length: {len(signal)} samples')
    print(f'   Duration: {duration} seconds')
    print(f'   Amplitude range: [{signal.min():.3f}, {signal.max():.3f}]')
    print()

    print('2. Decomposing signal...')
    result = decompose_signal(signal, sample_rate, n_peaks=5)
    print_decomposition_report(result)

    print('3. Reconstructing signal...')
    reconstructed = reconstruct_from_peaks(signal, result['components'], sample_rate)
    error = np.max(np.abs(signal - reconstructed))
    snr = 10 * np.log10(np.mean(signal**2) / np.mean((signal - reconstructed)**2))
    print(f'   Max reconstruction error: {error:.6f}')
    print(f'   SNR: {snr:.2f} dB')
    print()

    plot_decomposition()

    print('Done!')
