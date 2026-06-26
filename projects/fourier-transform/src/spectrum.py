"""
Spectrum Analysis Utilities
频谱分析工具

This module provides utilities for analyzing frequency spectra,
including:
    - Power spectral density estimation
    - Peak detection in frequency domain
    - Frequency resolution and windowing
    - Spectral leakage analysis
"""

import numpy as np
from .dft import magnitude_spectrum, phase_spectrum, frequency_axis, frequency_axis_positive
from .fft import fft
from typing import Tuple, List, Optional


def power_spectral_density(X: np.ndarray, sample_rate: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute the Power Spectral Density (PSD) from DFT/FFT output.

    PSD shows how the power of a signal is distributed across frequency.
    For DFT output X[k]:
        PSD[k] = (1/N) * |X[k]|^2

    Args:
        X: DFT/FFT output (complex array)
        sample_rate: Sampling rate in Hz

    Returns:
        Tuple of (frequencies, power values)
    """
    N = len(X)
    freqs, n_pos = frequency_axis_positive(N, sample_rate)
    power = np.zeros(n_pos)

    for k in range(n_pos):
        power[k] = (np.abs(X[k]) ** 2) / N

    return freqs, power


def magnitude_to_db(magnitude: np.ndarray, ref: float = 1.0, eps: float = 1e-12) -> np.ndarray:
    """
    Convert magnitude to decibels (dB).

    dB = 20 * log10(magnitude / ref)

    Args:
        magnitude: Magnitude values
        ref: Reference value
        eps: Small value to avoid log(0)

    Returns:
        Magnitude in dB
    """
    return 20.0 * np.log10(np.maximum(magnitude, eps) / ref)


def detect_peaks(
    freqs: np.ndarray,
    magnitudes: np.ndarray,
    threshold_ratio: float = 0.1,
    min_distance: int = 1
) -> List[Tuple[float, float]]:
    """
    Detect prominent peaks in the magnitude spectrum.

    A peak is defined as a point that is:
        1. Greater than threshold_ratio * max(magnitudes)
        2. Greater than its neighbors within min_distance

    Args:
        freqs: Frequency array
        magnitudes: Magnitude array
        threshold_ratio: Minimum ratio to max magnitude to be considered a peak
        min_distance: Minimum number of points between peaks

    Returns:
        List of (frequency, magnitude) tuples for detected peaks
    """
    max_mag = np.max(magnitudes)
    threshold = threshold_ratio * max_mag

    peaks = []
    for i in range(1, len(magnitudes) - 1):
        if magnitudes[i] > threshold:
            # Check if it's a local maximum
            if (magnitudes[i] > magnitudes[i - 1] and
                    magnitudes[i] > magnitudes[i + 1]):
                # Check minimum distance from previous peak
                if not peaks or (freqs[i] - peaks[-1][0]) > min_distance:
                    peaks.append((freqs[i], magnitudes[i]))

    # Sort by magnitude (descending)
    peaks.sort(key=lambda p: p[1], reverse=True)
    return peaks


def apply_window(x: np.ndarray, window_type: str = 'hann') -> np.ndarray:
    """
    Apply a window function to reduce spectral leakage.

    Window functions taper the signal at the edges to reduce discontinuities
    that cause spectral leakage in the DFT.

    Available windows:
        - 'hann': Hann window (raised cosine)
        - 'hamming': Hamming window
        - 'blackman': Blackman window
        - 'rectangular': No windowing (rectangular window)
        - 'bartlett': Bartlett (triangular) window

    Args:
        x: Input signal
        window_type: Type of window to apply

    Returns:
        Windowed signal
    """
    N = len(x)

    if window_type == 'hann':
        # w[n] = 0.5 * (1 - cos(2*pi*n/(N-1)))
        w = 0.5 * (1 - np.cos(2 * np.pi * np.arange(N) / (N - 1)))
    elif window_type == 'hamming':
        # w[n] = 0.54 - 0.46 * cos(2*pi*n/(N-1))
        w = 0.54 - 0.46 * np.cos(2 * np.pi * np.arange(N) / (N - 1))
    elif window_type == 'blackman':
        # w[n] = 0.42 - 0.5 * cos(2*pi*n/(N-1)) + 0.08 * cos(4*pi*n/(N-1))
        w = (0.42 - 0.5 * np.cos(2 * np.pi * np.arange(N) / (N - 1)) +
             0.08 * np.cos(4 * np.pi * np.arange(N) / (N - 1)))
    elif window_type == 'rectangular':
        w = np.ones(N)
    elif window_type == 'bartlett':
        # w[n] = 2/(N-1) * ((N-1)/2 - |n - (N-1)/2|)
        w = 2.0 / (N - 1) * ((N - 1) / 2 - np.abs(np.arange(N) - (N - 1) / 2))
    else:
        raise ValueError(f"Unknown window type: {window_type}")

    return x * w


def spectral_leakage_example(sample_rate: float, signal_freq: float, N: int) -> dict:
    """
    Demonstrate spectral leakage phenomenon.

    Spectral leakage occurs when the signal frequency doesn't align with
    DFT bin frequencies, causing energy to "leak" into adjacent bins.

    Args:
        sample_rate: Sampling rate in Hz
        signal_freq: Frequency of the test signal in Hz
        N: Number of samples

    Returns:
        Dictionary with leakage analysis data
    """
    t = np.arange(N) / sample_rate
    signal = np.sin(2 * np.pi * signal_freq * t)

    # Without windowing (rectangular)
    fft_rect = fft(signal)
    mag_rect = magnitude_spectrum(fft_rect)

    # With Hann window
    signal_windowed = apply_window(signal, 'hann')
    fft_windowed = fft(signal_windowed)
    mag_windowed = magnitude_spectrum(fft_windowed)

    freqs, _ = frequency_axis_positive(N, sample_rate)

    return {
        'freqs': freqs,
        'mag_rect': mag_rect,
        'mag_windowed': mag_windowed,
        'signal_freq': signal_freq,
        'bin_freq': sample_rate / N * int(round(signal_freq * N / sample_rate)),
        'leakage': signal_freq % (sample_rate / N) > 0.001,
    }


def estimate_frequency(
    freqs: np.ndarray,
    magnitudes: np.ndarray,
    peak_idx: Optional[int] = None
) -> float:
    """
    Estimate the dominant frequency from the magnitude spectrum.

    Uses quadratic interpolation around the peak for sub-bin accuracy.

    Args:
        freqs: Frequency array
        magnitudes: Magnitude array
        peak_idx: Index of the peak (if known)

    Returns:
        Estimated dominant frequency in Hz
    """
    if peak_idx is None:
        peak_idx = np.argmax(magnitudes)

    N = len(magnitudes)

    # Quadratic interpolation for better frequency estimation
    if 0 < peak_idx < N - 1:
        p1 = magnitudes[peak_idx - 1]
        p2 = magnitudes[peak_idx]
        p3 = magnitudes[peak_idx + 1]

        # Parabolic interpolation
        denom = p1 - 2 * p2 + p3
        if abs(denom) > 1e-10:
            delta = 0.5 * (p1 - p3) / denom
            freq_est = freqs[peak_idx] + delta * (freqs[1] - freqs[0])
        else:
            freq_est = freqs[peak_idx]
    else:
        freq_est = freqs[peak_idx]

    return freq_est


def compute_frequency_resolution(sample_rate: float, N: int) -> float:
    """
    Compute the frequency resolution of a DFT.

    Frequency resolution = sample_rate / N

    This is the spacing between adjacent frequency bins.

    Args:
        sample_rate: Sampling rate in Hz
        N: Number of samples

    Returns:
        Frequency resolution in Hz
    """
    return sample_rate / N


def compute_dynamic_range(magnitude: np.ndarray, ref: float = 1.0) -> float:
    """
    Compute the dynamic range of a spectrum in dB.

    Args:
        magnitude: Magnitude spectrum
        ref: Reference magnitude

    Returns:
        Dynamic range in dB (max - min)
    """
    max_db = magnitude_to_db(magnitude, ref)
    min_db = magnitude_to_db(magnitude, ref)
    # Filter out near-zero values
    valid = magnitude > 1e-10
    if np.any(valid):
        return float(np.max(max_db[valid]) - np.min(max_db[valid]))
    return 0.0
