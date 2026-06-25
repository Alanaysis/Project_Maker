"""FIR Filter implementation using window method and frequency sampling method."""

import numpy as np
from scipy import signal


class FIRFilter:
    """FIR (Finite Impulse Response) filter with multiple design methods.

    Supports:
    - Window method (Hamming, Hanning, Blackman, Kaiser, etc.)
    - Frequency sampling method
    """

    def __init__(self, coefficients: np.ndarray, fs: float = 1.0):
        """Initialize FIR filter.

        Args:
            coefficients: Filter coefficients (impulse response).
            fs: Sampling frequency in Hz.
        """
        self.coefficients = np.asarray(coefficients, dtype=float)
        self.fs = fs
        self.order = len(coefficients) - 1

    def apply(self, x: np.ndarray) -> np.ndarray:
        """Apply FIR filter to signal.

        Args:
            x: Input signal.

        Returns:
            Filtered signal.
        """
        return signal.lfilter(self.coefficients, 1.0, x)

    def apply_filtfilt(self, x: np.ndarray) -> np.ndarray:
        """Apply zero-phase FIR filter (forward-backward filtering).

        Args:
            x: Input signal.

        Returns:
            Zero-phase filtered signal.
        """
        return signal.filtfilt(self.coefficients, 1.0, x)


def fir_lowpass(
    cutoff: float,
    num_taps: int = 101,
    fs: float = 1.0,
    window: str = "hamming",
) -> FIRFilter:
    """Design a low-pass FIR filter using the window method.

    Args:
        cutoff: Cutoff frequency in Hz.
        num_taps: Number of filter taps (must be odd).
        fs: Sampling frequency in Hz.
        window: Window function name.

    Returns:
        FIRFilter instance.
    """
    if num_taps % 2 == 0:
        num_taps += 1
    normalized_cutoff = cutoff / (fs / 2)
    coefficients = signal.firwin(num_taps, normalized_cutoff, window=window)
    return FIRFilter(coefficients, fs)


def fir_highpass(
    cutoff: float,
    num_taps: int = 101,
    fs: float = 1.0,
    window: str = "hamming",
) -> FIRFilter:
    """Design a high-pass FIR filter using the window method.

    Args:
        cutoff: Cutoff frequency in Hz.
        num_taps: Number of filter taps (must be odd).
        fs: Sampling frequency in Hz.
        window: Window function name.

    Returns:
        FIRFilter instance.
    """
    if num_taps % 2 == 0:
        num_taps += 1
    normalized_cutoff = cutoff / (fs / 2)
    coefficients = signal.firwin(num_taps, normalized_cutoff, pass_zero=False, window=window)
    return FIRFilter(coefficients, fs)


def fir_bandpass(
    low_cutoff: float,
    high_cutoff: float,
    num_taps: int = 101,
    fs: float = 1.0,
    window: str = "hamming",
) -> FIRFilter:
    """Design a band-pass FIR filter using the window method.

    Args:
        low_cutoff: Low cutoff frequency in Hz.
        high_cutoff: High cutoff frequency in Hz.
        num_taps: Number of filter taps (must be odd).
        fs: Sampling frequency in Hz.
        window: Window function name.

    Returns:
        FIRFilter instance.
    """
    if num_taps % 2 == 0:
        num_taps += 1
    normalized = [low_cutoff / (fs / 2), high_cutoff / (fs / 2)]
    coefficients = signal.firwin(num_taps, normalized, pass_zero=False, window=window)
    return FIRFilter(coefficients, fs)


def fir_bandstop(
    low_cutoff: float,
    high_cutoff: float,
    num_taps: int = 101,
    fs: float = 1.0,
    window: str = "hamming",
) -> FIRFilter:
    """Design a band-stop (notch) FIR filter using the window method.

    Args:
        low_cutoff: Low cutoff frequency in Hz.
        high_cutoff: High cutoff frequency in Hz.
        num_taps: Number of filter taps (must be odd).
        fs: Sampling frequency in Hz.
        window: Window function name.

    Returns:
        FIRFilter instance.
    """
    if num_taps % 2 == 0:
        num_taps += 1
    normalized = [low_cutoff / (fs / 2), high_cutoff / (fs / 2)]
    coefficients = signal.firwin(num_taps, normalized, pass_zero=True, window=window)
    return FIRFilter(coefficients, fs)


def fir_frequency_sampling(
    desired_response: np.ndarray,
    fs: float = 1.0,
    window: str = "hamming",
) -> FIRFilter:
    """Design FIR filter using the frequency sampling method.

    Args:
        desired_response: Desired frequency response at uniformly spaced
            frequency samples (real-valued, length N).
        fs: Sampling frequency in Hz.
        window: Window to apply to the resulting impulse response.

    Returns:
        FIRFilter instance.
    """
    desired = np.asarray(desired_response, dtype=float)
    N = len(desired)
    # IFFT to get impulse response
    h = np.fft.ifft(desired).real
    # Circular shift to make causal
    h = np.roll(h, N // 2)
    # Apply window
    win = signal.get_window(window, N)
    h = h * win
    return FIRFilter(h, fs)


def design_fir_lowpass_freq_sampling(
    cutoff: float,
    num_taps: int = 64,
    fs: float = 1.0,
    transition_width: float = None,
) -> FIRFilter:
    """Design low-pass FIR filter using frequency sampling method.

    Args:
        cutoff: Cutoff frequency in Hz.
        num_taps: Number of filter taps.
        fs: Sampling frequency in Hz.
        transition_width: Width of transition band in Hz (optional smoothing).

    Returns:
        FIRFilter instance.
    """
    N = num_taps
    freqs = np.arange(N) / N  # Normalized frequency [0, 1)
    cutoff_norm = cutoff / fs

    # Ideal low-pass response
    desired = np.zeros(N)
    for i in range(N):
        f = freqs[i] if freqs[i] <= 0.5 else freqs[i] - 1.0
        if abs(f) <= cutoff_norm:
            desired[i] = 1.0

    return fir_frequency_sampling(desired, fs=fs)
