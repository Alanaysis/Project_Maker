"""Tests for FIR filter module."""

import numpy as np
import pytest
from src.fir import (
    FIRFilter,
    fir_lowpass,
    fir_highpass,
    fir_bandpass,
    fir_bandstop,
    fir_frequency_sampling,
    design_fir_lowpass_freq_sampling,
)


class TestFIRFilter:
    """Tests for FIRFilter class."""

    def test_init(self):
        coeffs = np.array([0.1, 0.2, 0.4, 0.2, 0.1])
        filt = FIRFilter(coeffs, fs=1000.0)
        assert filt.order == 4
        assert filt.fs == 1000.0
        np.testing.assert_array_equal(filt.coefficients, coeffs)

    def test_apply_length(self):
        coeffs = np.array([0.1, 0.2, 0.4, 0.2, 0.1])
        filt = FIRFilter(coeffs)
        x = np.random.randn(100)
        y = filt.apply(x)
        assert len(y) == len(x)

    def test_apply_filtfilt(self):
        coeffs = np.array([0.1, 0.2, 0.4, 0.2, 0.1])
        filt = FIRFilter(coeffs)
        x = np.random.randn(100)
        y = filt.apply_filtfilt(x)
        assert len(y) == len(x)


class TestFIRDesign:
    """Tests for FIR design functions."""

    def test_lowpass(self):
        filt = fir_lowpass(cutoff=100, num_taps=51, fs=1000)
        assert isinstance(filt, FIRFilter)
        assert filt.order == 50

    def test_lowpass_even_taps(self):
        filt = fir_lowpass(cutoff=100, num_taps=50, fs=1000)
        assert filt.order % 2 == 0  # Should be made odd

    def test_highpass(self):
        filt = fir_highpass(cutoff=200, num_taps=51, fs=1000)
        assert isinstance(filt, FIRFilter)

    def test_bandpass(self):
        filt = fir_bandpass(low_cutoff=100, high_cutoff=300, num_taps=51, fs=1000)
        assert isinstance(filt, FIRFilter)

    def test_bandstop(self):
        filt = fir_bandstop(low_cutoff=100, high_cutoff=300, num_taps=51, fs=1000)
        assert isinstance(filt, FIRFilter)

    def test_frequency_sampling(self):
        desired = np.zeros(64)
        desired[:16] = 1.0
        desired[-16:] = 1.0
        filt = fir_frequency_sampling(desired, fs=1000)
        assert isinstance(filt, FIRFilter)
        assert len(filt.coefficients) == 64

    def test_design_fir_lowpass_freq_sampling(self):
        filt = design_fir_lowpass_freq_sampling(cutoff=100, num_taps=64, fs=1000)
        assert isinstance(filt, FIRFilter)


class TestFIRFiltering:
    """Tests for FIR filtering behavior."""

    def test_lowpass_removes_high_freq(self):
        """Low-pass filter should attenuate high-frequency components."""
        fs = 1000.0
        t = np.arange(0, 1.0, 1.0 / fs)
        low_freq = np.sin(2 * np.pi * 20 * t)  # 20 Hz
        high_freq = 0.5 * np.sin(2 * np.pi * 200 * t)  # 200 Hz
        x = low_freq + high_freq

        filt = fir_lowpass(cutoff=50, num_taps=101, fs=fs)
        y = filt.apply_filtfilt(x)

        # After filtering, high-freq power should be much lower
        high_power_in = np.mean(high_freq ** 2)
        residual = y - low_freq
        high_power_out = np.mean(residual ** 2)
        assert high_power_out < high_power_in * 0.5

    def test_highpass_removes_low_freq(self):
        """High-pass filter should attenuate low-frequency components."""
        fs = 1000.0
        t = np.arange(0, 1.0, 1.0 / fs)
        low_freq = np.sin(2 * np.pi * 20 * t)
        high_freq = 0.5 * np.sin(2 * np.pi * 200 * t)
        x = low_freq + high_freq

        filt = fir_highpass(cutoff=100, num_taps=101, fs=fs)
        y = filt.apply_filtfilt(x)

        low_power_in = np.mean(low_freq ** 2)
        residual = y - high_freq
        low_power_out = np.mean(residual ** 2)
        assert low_power_out < low_power_in * 0.5
