"""Frequency response analysis and visualization."""

import numpy as np
from scipy import signal
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def frequency_response(
    b: np.ndarray,
    a: np.ndarray,
    fs: float = 1.0,
    worN: int = 8192,
) -> tuple:
    """Compute frequency response of a digital filter.

    Args:
        b: Numerator coefficients.
        a: Denominator coefficients.
        fs: Sampling frequency in Hz.
        worN: Number of frequency points.

    Returns:
        (freqs_hz, magnitude_db, phase_deg) tuple.
    """
    w, h = signal.freqz(b, a, worN=worN, fs=fs)
    magnitude_db = 20 * np.log10(np.abs(h) + 1e-12)
    phase_deg = np.degrees(np.unwrap(np.angle(h)))
    return w, magnitude_db, phase_deg


def plot_response(
    b: np.ndarray,
    a: np.ndarray,
    fs: float = 1.0,
    title: str = "Frequency Response",
    save_path: str = None,
) -> None:
    """Plot magnitude and phase response of a filter.

    Args:
        b: Numerator coefficients.
        a: Denominator coefficients.
        fs: Sampling frequency in Hz.
        title: Plot title.
        save_path: Path to save figure (optional).
    """
    freqs, mag_db, phase_deg = frequency_response(b, a, fs)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6))
    fig.suptitle(title, fontsize=14)

    ax1.plot(freqs, mag_db, "b-", linewidth=1.5)
    ax1.set_ylabel("Magnitude (dB)")
    ax1.set_xlabel("Frequency (Hz)")
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim([0, fs / 2])

    ax2.plot(freqs, phase_deg, "r-", linewidth=1.5)
    ax2.set_ylabel("Phase (degrees)")
    ax2.set_xlabel("Frequency (Hz)")
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim([0, fs / 2])

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()


def plot_filter_comparison(
    filters: list,
    labels: list,
    fs: float = 1.0,
    title: str = "Filter Comparison",
    save_path: str = None,
) -> None:
    """Compare magnitude responses of multiple filters.

    Args:
        filters: List of (b, a) coefficient tuples.
        labels: List of labels for each filter.
        fs: Sampling frequency in Hz.
        title: Plot title.
        save_path: Path to save figure (optional).
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    fig.suptitle(title, fontsize=14)

    for (b, a), label in zip(filters, labels):
        freqs, mag_db, phase_deg = frequency_response(b, a, fs)
        ax1.plot(freqs, mag_db, linewidth=1.5, label=label)
        ax2.plot(freqs, phase_deg, linewidth=1.5, label=label)

    ax1.set_ylabel("Magnitude (dB)")
    ax1.set_xlabel("Frequency (Hz)")
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    ax1.set_xlim([0, fs / 2])

    ax2.set_ylabel("Phase (degrees)")
    ax2.set_xlabel("Frequency (Hz)")
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    ax2.set_xlim([0, fs / 2])

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()


def group_delay(b: np.ndarray, a: np.ndarray, fs: float = 1.0, worN: int = 8192) -> tuple:
    """Compute group delay of a digital filter.

    Args:
        b: Numerator coefficients.
        a: Denominator coefficients.
        fs: Sampling frequency in Hz.
        worN: Number of frequency points.

    Returns:
        (freqs_hz, delay_samples) tuple.
    """
    w, gd = signal.group_delay((b, a), worN=worN, fs=fs)
    return w, gd
