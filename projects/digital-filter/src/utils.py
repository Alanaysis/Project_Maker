"""Utility functions for signal generation and visualization."""

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def generate_signal(
    duration: float = 1.0,
    fs: float = 1000.0,
    components: list = None,
) -> tuple:
    """Generate a test signal with multiple sinusoidal components.

    Args:
        duration: Signal duration in seconds.
        fs: Sampling frequency in Hz.
        components: List of (frequency_hz, amplitude) tuples.
            Defaults to 50Hz + 200Hz components.

    Returns:
        (time_array, signal_array) tuple.
    """
    if components is None:
        components = [(50, 1.0), (200, 0.5)]

    t = np.arange(0, duration, 1.0 / fs)
    x = np.zeros_like(t)
    for freq, amp in components:
        x += amp * np.sin(2 * np.pi * freq * t)
    return t, x


def add_noise(x: np.ndarray, snr_db: float = 20.0) -> np.ndarray:
    """Add white Gaussian noise to a signal.

    Args:
        x: Input signal.
        snr_db: Desired signal-to-noise ratio in dB.

    Returns:
        Noisy signal.
    """
    signal_power = np.mean(x ** 2)
    noise_power = signal_power / (10 ** (snr_db / 10))
    noise = np.random.normal(0, np.sqrt(noise_power), len(x))
    return x + noise


def snr(clean: np.ndarray, noisy: np.ndarray) -> float:
    """Calculate signal-to-noise ratio in dB.

    Args:
        clean: Clean signal.
        noisy: Noisy (or filtered) signal.

    Returns:
        SNR in dB.
    """
    noise = clean - noisy
    signal_power = np.mean(clean ** 2)
    noise_power = np.mean(noise ** 2)
    if noise_power == 0:
        return float("inf")
    return 10 * np.log10(signal_power / noise_power)


def plot_comparison(
    t: np.ndarray,
    signals: list,
    labels: list,
    title: str = "Signal Comparison",
    save_path: str = None,
) -> None:
    """Plot multiple signals for comparison.

    Args:
        t: Time array.
        signals: List of signal arrays.
        labels: List of labels.
        title: Plot title.
        save_path: Path to save figure (optional).
    """
    n = len(signals)
    fig, axes = plt.subplots(n, 1, figsize=(12, 3 * n), sharex=True)
    if n == 1:
        axes = [axes]
    fig.suptitle(title, fontsize=14)

    for ax, sig, label in zip(axes, signals, labels):
        ax.plot(t, sig, linewidth=0.8)
        ax.set_ylabel(label)
        ax.grid(True, alpha=0.3)

    axes[-1].set_xlabel("Time (s)")
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()


def plot_spectrum(
    x: np.ndarray,
    fs: float = 1000.0,
    title: str = "Spectrum",
    save_path: str = None,
) -> None:
    """Plot the magnitude spectrum of a signal.

    Args:
        x: Input signal.
        fs: Sampling frequency in Hz.
        title: Plot title.
        save_path: Path to save figure (optional).
    """
    N = len(x)
    freqs = np.fft.rfftfreq(N, 1.0 / fs)
    spectrum = np.abs(np.fft.rfft(x)) / N

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(freqs, 20 * np.log10(spectrum + 1e-12), "b-", linewidth=1)
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Magnitude (dB)")
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
