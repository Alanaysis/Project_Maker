"""
02 - DFT vs FFT Comparison Demo
DFT vs FFT 对比示例

This example compares the direct DFT computation with the FFT algorithm,
demonstrating:
    - Numerical equivalence
    - Performance difference
    - Complexity scaling
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.dft import dft, magnitude_spectrum, frequency_axis_positive
from src.fft import fft, fft_iterative, fft_complexity_analysis
from src.spectrum import apply_window


def compare_dft_fft():
    """Compare DFT and FFT results for a small signal."""
    sample_rate = 1000
    duration = 0.5
    N = int(sample_rate * duration)

    # Generate test signal
    t = np.arange(N) / sample_rate
    signal = np.sin(2 * np.pi * 50 * t) + 0.5 * np.sin(2 * np.pi * 120 * t)

    # Compute DFT and FFT
    X_dft = dft(signal)
    X_fft = fft(signal)

    # Check numerical equivalence
    diff = np.max(np.abs(X_dft - X_fft))
    print(f'Max difference between DFT and FFT: {diff:.2e}')
    print(f'Results match: {diff < 1e-10}')
    print()


def benchmark_dft_fft():
    """Benchmark DFT vs FFT for various signal lengths."""
    print('Benchmarking DFT vs FFT:')
    print('-' * 60)
    print(f'{"N":>8s} | {"DFT (ms)":>10s} | {"FFT (ms)":>10s} | {"Speedup":>10s}')
    print('-' * 60)

    sizes = [32, 64, 128, 256, 512, 1024]

    for N in sizes:
        t = np.arange(N) / 1000
        signal = np.sin(2 * np.pi * 50 * t)

        # Benchmark DFT
        start = time.perf_counter()
        for _ in range(3):
            X_dft = dft(signal)
        dft_time = (time.perf_counter() - start) / 3 * 1000

        # Benchmark FFT
        start = time.perf_counter()
        for _ in range(3):
            X_fft = fft(signal)
        fft_time = (time.perf_counter() - start) / 3 * 1000

        speedup = dft_time / fft_time if fft_time > 0 else float('inf')
        print(f'{N:>8d} | {dft_time:>10.3f} | {fft_time:>10.3f} | {speedup:>10.1f}x')

    print('-' * 60)
    print()


def plot_complexity_scaling():
    """Plot the theoretical complexity scaling of DFT vs FFT."""
    N_values = [2**i for i in range(2, 16)]
    dft_ops = [N * N for N in N_values]
    fft_ops = [N * int(np.log2(N)) for N in N_values]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Linear scale
    ax1.plot(N_values, dft_ops, 'o-', label='DFT: O(N²)', linewidth=2)
    ax1.plot(N_values, fft_ops, 's-', label='FFT: O(N log N)', linewidth=2)
    ax1.set_xlabel('Number of samples (N)', fontsize=11)
    ax1.set_ylabel('Operations', fontsize=11)
    ax1.set_title('Complexity Comparison (Linear Scale)', fontsize=12)
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Log-log scale
    ax2.loglog(N_values, dft_ops, 'o-', label='DFT: O(N²)', linewidth=2)
    ax2.loglog(N_values, fft_ops, 's-', label='FFT: O(N log N)', linewidth=2)
    ax2.set_xlabel('Number of samples (N)', fontsize=11)
    ax2.set_ylabel('Operations', fontsize=11)
    ax2.set_title('Complexity Comparison (Log-Log Scale)', fontsize=12)
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '02_complexity_comparison.png')
    plt.savefig(out_path, dpi=100, bbox_inches='tight')
    print(f'Saved complexity plot: {out_path}')
    plt.close()


def plot_fft_vs_dft_results():
    """Plot side-by-side DFT and FFT magnitude spectra."""
    sample_rate = 1000
    duration = 1.0
    N = int(sample_rate * duration)

    t = np.arange(N) / sample_rate
    signal = np.sin(2 * np.pi * 50 * t) + 0.5 * np.sin(2 * np.pi * 120 * t)

    X_dft = dft(signal)
    X_fft = fft(signal)
    mag_dft = magnitude_spectrum(X_dft)
    mag_fft = magnitude_spectrum(X_fft)
    freqs, n_pos = frequency_axis_positive(N, sample_rate)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    ax1.plot(freqs[:n_pos], mag_dft[:n_pos], linewidth=0.8, color='blue')
    ax1.set_title('DFT Magnitude Spectrum', fontsize=12)
    ax1.set_xlabel('Frequency (Hz)')
    ax1.set_ylabel('|X(f)|')
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, 300)

    ax2.plot(freqs[:n_pos], mag_fft[:n_pos], linewidth=0.8, color='red')
    ax2.set_title('FFT Magnitude Spectrum', fontsize=12)
    ax2.set_xlabel('Frequency (Hz)')
    ax2.set_ylabel('|X(f)|')
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(0, 300)

    # Mark peaks
    for ax in [ax1, ax2]:
        ax.axvline(x=50, color='green', linestyle='--', alpha=0.5)
        ax.axvline(x=120, color='orange', linestyle='--', alpha=0.5)

    plt.tight_layout()
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '02_dft_fft_results.png')
    plt.savefig(out_path, dpi=100, bbox_inches='tight')
    print(f'Saved DFT vs FFT plot: {out_path}')
    plt.close()


if __name__ == '__main__':
    print('=== DFT vs FFT Comparison / DFT与FFT对比 ===')
    print()

    print('1. Numerical Equivalence Test')
    print('-' * 40)
    compare_dft_fft()

    print('2. Performance Benchmark')
    print('-' * 40)
    benchmark_dft_fft()

    print('3. Complexity Analysis')
    print('-' * 40)
    for N in [64, 256, 1024, 4096]:
        analysis = fft_complexity_analysis(N)
        print(f'  N={analysis["N"]:>6d}: DFT={analysis["DFT_operations"]:>10d} ops, '
              f'FFT={analysis["FFT_operations"]:>10d} ops, '
              f'Speedup={analysis["Speedup_factor"]}')
    print()

    plot_complexity_scaling()
    plot_fft_vs_dft_results()

    print('Done!')
