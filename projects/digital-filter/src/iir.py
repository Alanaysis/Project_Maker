"""IIR Filter implementation - Butterworth, Chebyshev, Elliptic."""

import numpy as np
from scipy import signal


class IIRFilter:
    """IIR (Infinite Impulse Response) filter wrapper.

    Wraps scipy.signal IIR filter design functions and provides
    a unified interface for filtering signals.
    """

    def __init__(self, b: np.ndarray, a: np.ndarray, fs: float = 1.0):
        """Initialize IIR filter with transfer function coefficients.

        Args:
            b: Numerator coefficients.
            a: Denominator coefficients.
            fs: Sampling frequency in Hz.
        """
        self.b = np.asarray(b, dtype=float)
        self.a = np.asarray(a, dtype=float)
        self.fs = fs

    @property
    def order(self) -> int:
        """Filter order."""
        return max(len(self.b), len(self.a)) - 1

    def apply(self, x: np.ndarray) -> np.ndarray:
        """Apply IIR filter to signal.

        Args:
            x: Input signal.

        Returns:
            Filtered signal.
        """
        return signal.lfilter(self.b, self.a, x)

    def apply_filtfilt(self, x: np.ndarray) -> np.ndarray:
        """Apply zero-phase IIR filter (forward-backward).

        Args:
            x: Input signal.

        Returns:
            Zero-phase filtered signal.
        """
        return signal.filtfilt(self.b, self.a, x)

    def sos(self) -> np.ndarray:
        """Return second-order sections representation."""
        return signal.tf2sos(self.b, self.a)

    def apply_sos(self, x: np.ndarray) -> np.ndarray:
        """Apply filter using SOS form (more numerically stable).

        Args:
            x: Input signal.

        Returns:
            Filtered signal.
        """
        sos = self.sos()
        return signal.sosfilt(sos, x)


# ---------------------------------------------------------------------------
# Butterworth filters
# ---------------------------------------------------------------------------

def butterworth_lowpass(
    cutoff: float,
    order: int = 4,
    fs: float = 1.0,
) -> IIRFilter:
    """Design a Butterworth low-pass filter.

    Args:
        cutoff: Cutoff frequency in Hz.
        order: Filter order.
        fs: Sampling frequency in Hz.

    Returns:
        IIRFilter instance.
    """
    nyq = fs / 2
    b, a = signal.butter(order, cutoff / nyq, btype="low")
    return IIRFilter(b, a, fs)


def butterworth_highpass(
    cutoff: float,
    order: int = 4,
    fs: float = 1.0,
) -> IIRFilter:
    """Design a Butterworth high-pass filter.

    Args:
        cutoff: Cutoff frequency in Hz.
        order: Filter order.
        fs: Sampling frequency in Hz.

    Returns:
        IIRFilter instance.
    """
    nyq = fs / 2
    b, a = signal.butter(order, cutoff / nyq, btype="high")
    return IIRFilter(b, a, fs)


def butterworth_bandpass(
    low_cutoff: float,
    high_cutoff: float,
    order: int = 4,
    fs: float = 1.0,
) -> IIRFilter:
    """Design a Butterworth band-pass filter.

    Args:
        low_cutoff: Low cutoff frequency in Hz.
        high_cutoff: High cutoff frequency in Hz.
        order: Filter order.
        fs: Sampling frequency in Hz.

    Returns:
        IIRFilter instance.
    """
    nyq = fs / 2
    b, a = signal.butter(order, [low_cutoff / nyq, high_cutoff / nyq], btype="band")
    return IIRFilter(b, a, fs)


def butterworth_bandstop(
    low_cutoff: float,
    high_cutoff: float,
    order: int = 4,
    fs: float = 1.0,
) -> IIRFilter:
    """Design a Butterworth band-stop filter.

    Args:
        low_cutoff: Low cutoff frequency in Hz.
        high_cutoff: High cutoff frequency in Hz.
        order: Filter order.
        fs: Sampling frequency in Hz.

    Returns:
        IIRFilter instance.
    """
    nyq = fs / 2
    b, a = signal.butter(order, [low_cutoff / nyq, high_cutoff / nyq], btype="bandstop")
    return IIRFilter(b, a, fs)


# ---------------------------------------------------------------------------
# Chebyshev Type I filters
# ---------------------------------------------------------------------------

def chebyshev1_lowpass(
    cutoff: float,
    order: int = 4,
    ripple: float = 1.0,
    fs: float = 1.0,
) -> IIRFilter:
    """Design a Chebyshev Type I low-pass filter.

    Args:
        cutoff: Cutoff frequency in Hz.
        order: Filter order.
        ripple: Maximum passband ripple in dB.
        fs: Sampling frequency in Hz.

    Returns:
        IIRFilter instance.
    """
    nyq = fs / 2
    b, a = signal.cheby1(order, ripple, cutoff / nyq, btype="low")
    return IIRFilter(b, a, fs)


def chebyshev1_highpass(
    cutoff: float,
    order: int = 4,
    ripple: float = 1.0,
    fs: float = 1.0,
) -> IIRFilter:
    """Design a Chebyshev Type I high-pass filter."""
    nyq = fs / 2
    b, a = signal.cheby1(order, ripple, cutoff / nyq, btype="high")
    return IIRFilter(b, a, fs)


def chebyshev1_bandpass(
    low_cutoff: float,
    high_cutoff: float,
    order: int = 4,
    ripple: float = 1.0,
    fs: float = 1.0,
) -> IIRFilter:
    """Design a Chebyshev Type I band-pass filter."""
    nyq = fs / 2
    b, a = signal.cheby1(order, ripple, [low_cutoff / nyq, high_cutoff / nyq], btype="band")
    return IIRFilter(b, a, fs)


# ---------------------------------------------------------------------------
# Chebyshev Type II filters
# ---------------------------------------------------------------------------

def chebyshev2_lowpass(
    cutoff: float,
    order: int = 4,
    attenuation: float = 40.0,
    fs: float = 1.0,
) -> IIRFilter:
    """Design a Chebyshev Type II low-pass filter.

    Args:
        cutoff: Cutoff frequency in Hz.
        order: Filter order.
        attenuation: Minimum stopband attenuation in dB.
        fs: Sampling frequency in Hz.

    Returns:
        IIRFilter instance.
    """
    nyq = fs / 2
    b, a = signal.cheby2(order, attenuation, cutoff / nyq, btype="low")
    return IIRFilter(b, a, fs)


def chebyshev2_highpass(
    cutoff: float,
    order: int = 4,
    attenuation: float = 40.0,
    fs: float = 1.0,
) -> IIRFilter:
    """Design a Chebyshev Type II high-pass filter."""
    nyq = fs / 2
    b, a = signal.cheby2(order, attenuation, cutoff / nyq, btype="high")
    return IIRFilter(b, a, fs)


# ---------------------------------------------------------------------------
# Elliptic filters
# ---------------------------------------------------------------------------

def elliptic_lowpass(
    cutoff: float,
    order: int = 4,
    ripple: float = 1.0,
    attenuation: float = 40.0,
    fs: float = 1.0,
) -> IIRFilter:
    """Design an elliptic (Cauer) low-pass filter.

    Args:
        cutoff: Cutoff frequency in Hz.
        order: Filter order.
        ripple: Maximum passband ripple in dB.
        attenuation: Minimum stopband attenuation in dB.
        fs: Sampling frequency in Hz.

    Returns:
        IIRFilter instance.
    """
    nyq = fs / 2
    b, a = signal.ellip(order, ripple, attenuation, cutoff / nyq, btype="low")
    return IIRFilter(b, a, fs)


def elliptic_highpass(
    cutoff: float,
    order: int = 4,
    ripple: float = 1.0,
    attenuation: float = 40.0,
    fs: float = 1.0,
) -> IIRFilter:
    """Design an elliptic high-pass filter."""
    nyq = fs / 2
    b, a = signal.ellip(order, ripple, attenuation, cutoff / nyq, btype="high")
    return IIRFilter(b, a, fs)


def elliptic_bandpass(
    low_cutoff: float,
    high_cutoff: float,
    order: int = 4,
    ripple: float = 1.0,
    attenuation: float = 40.0,
    fs: float = 1.0,
) -> IIRFilter:
    """Design an elliptic band-pass filter."""
    nyq = fs / 2
    b, a = signal.ellip(order, ripple, attenuation,
                         [low_cutoff / nyq, high_cutoff / nyq], btype="band")
    return IIRFilter(b, a, fs)
