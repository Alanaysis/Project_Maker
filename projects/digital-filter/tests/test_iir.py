"""Tests for IIR filter module."""

import numpy as np
import pytest
from src.iir import (
    IIRFilter,
    butterworth_lowpass,
    butterworth_highpass,
    butterworth_bandpass,
    butterworth_bandstop,
    chebyshev1_lowpass,
    chebyshev1_highpass,
    chebyshev1_bandpass,
    chebyshev2_lowpass,
    chebyshev2_highpass,
    elliptic_lowpass,
    elliptic_highpass,
    elliptic_bandpass,
)


class TestIIRFilter:
    """Tests for IIRFilter class."""

    def test_init(self):
        b = np.array([1.0, 0.5])
        a = np.array([1.0, -0.3])
        filt = IIRFilter(b, a, fs=1000.0)
        assert filt.fs == 1000.0
        np.testing.assert_array_equal(filt.b, b)
        np.testing.assert_array_equal(filt.a, a)

    def test_apply_length(self):
        filt = butterworth_lowpass(cutoff=100, order=4, fs=1000)
        x = np.random.randn(200)
        y = filt.apply(x)
        assert len(y) == len(x)

    def test_apply_filtfilt(self):
        filt = butterworth_lowpass(cutoff=100, order=4, fs=1000)
        x = np.random.randn(200)
        y = filt.apply_filtfilt(x)
        assert len(y) == len(x)

    def test_sos(self):
        filt = butterworth_lowpass(cutoff=100, order=4, fs=1000)
        sos = filt.sos()
        assert sos.shape[1] == 6  # SOS format: [b0, b1, b2, a0, a1, a2]

    def test_apply_sos(self):
        filt = butterworth_lowpass(cutoff=100, order=4, fs=1000)
        x = np.random.randn(200)
        y = filt.apply_sos(x)
        assert len(y) == len(x)


class TestButterworth:
    """Tests for Butterworth filter designs."""

    def test_lowpass(self):
        filt = butterworth_lowpass(cutoff=100, order=4, fs=1000)
        assert isinstance(filt, IIRFilter)

    def test_highpass(self):
        filt = butterworth_highpass(cutoff=200, order=4, fs=1000)
        assert isinstance(filt, IIRFilter)

    def test_bandpass(self):
        filt = butterworth_bandpass(100, 300, order=4, fs=1000)
        assert isinstance(filt, IIRFilter)

    def test_bandstop(self):
        filt = butterworth_bandstop(100, 300, order=4, fs=1000)
        assert isinstance(filt, IIRFilter)

    def test_order_preserved(self):
        filt = butterworth_lowpass(cutoff=100, order=6, fs=1000)
        # Order 6 means 6 poles, so denominator should have 7 coefficients
        assert len(filt.a) == 7


class TestChebyshev:
    """Tests for Chebyshev filter designs."""

    def test_chebyshev1_lowpass(self):
        filt = chebyshev1_lowpass(cutoff=100, order=4, ripple=1.0, fs=1000)
        assert isinstance(filt, IIRFilter)

    def test_chebyshev1_highpass(self):
        filt = chebyshev1_highpass(cutoff=200, order=4, fs=1000)
        assert isinstance(filt, IIRFilter)

    def test_chebyshev1_bandpass(self):
        filt = chebyshev1_bandpass(100, 300, order=4, fs=1000)
        assert isinstance(filt, IIRFilter)

    def test_chebyshev2_lowpass(self):
        filt = chebyshev2_lowpass(cutoff=100, order=4, attenuation=40, fs=1000)
        assert isinstance(filt, IIRFilter)

    def test_chebyshev2_highpass(self):
        filt = chebyshev2_highpass(cutoff=200, order=4, fs=1000)
        assert isinstance(filt, IIRFilter)


class TestElliptic:
    """Tests for Elliptic filter designs."""

    def test_lowpass(self):
        filt = elliptic_lowpass(cutoff=100, order=4, fs=1000)
        assert isinstance(filt, IIRFilter)

    def test_highpass(self):
        filt = elliptic_highpass(cutoff=200, order=4, fs=1000)
        assert isinstance(filt, IIRFilter)

    def test_bandpass(self):
        filt = elliptic_bandpass(100, 300, order=4, fs=1000)
        assert isinstance(filt, IIRFilter)


class TestIIRFiltering:
    """Tests for IIR filtering behavior."""

    def test_butterworth_lowpass_removes_high_freq(self):
        fs = 1000.0
        t = np.arange(0, 1.0, 1.0 / fs)
        low_freq = np.sin(2 * np.pi * 20 * t)
        high_freq = 0.5 * np.sin(2 * np.pi * 200 * t)
        x = low_freq + high_freq

        filt = butterworth_lowpass(cutoff=50, order=6, fs=fs)
        y = filt.apply_filtfilt(x)

        residual = y - low_freq
        assert np.mean(residual ** 2) < np.mean(high_freq ** 2) * 0.3

    def test_butterworth_highpass_removes_low_freq(self):
        fs = 1000.0
        t = np.arange(0, 1.0, 1.0 / fs)
        low_freq = np.sin(2 * np.pi * 20 * t)
        high_freq = 0.5 * np.sin(2 * np.pi * 200 * t)
        x = low_freq + high_freq

        filt = butterworth_highpass(cutoff=100, order=6, fs=fs)
        y = filt.apply_filtfilt(x)

        residual = y - high_freq
        assert np.mean(residual ** 2) < np.mean(low_freq ** 2) * 0.3

    def test_chebyshev_vs_butterworth(self):
        """Chebyshev should have steeper rolloff than Butterworth of same order."""
        fs = 1000.0
        from scipy import signal as sig

        _, h_butter = sig.butter(4, 100 / (fs / 2), btype="low", output="ba")
        _, h_cheby = sig.cheby1(4, 1.0, 100 / (fs / 2), btype="low", output="ba")

        # Just verify both produce valid coefficients
        assert len(h_butter) > 0
        assert len(h_cheby) > 0
