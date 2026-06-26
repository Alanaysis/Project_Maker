"""
Tests for Spectrum analysis module
频谱分析模块测试
"""

import numpy as np
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.fft import fft
from src.dft import magnitude_spectrum, frequency_axis_positive
from src.spectrum import (
    power_spectral_density,
    magnitude_to_db,
    detect_peaks,
    apply_window,
    spectral_leakage_example,
    estimate_frequency,
    compute_frequency_resolution,
    compute_dynamic_range,
)


class TestPSD:
    """Test Power Spectral Density computation."""

    def test_psd_non_negative(self):
        """PSD should be non-negative."""
        N = 16
        x = np.random.randn(N)
        X = fft(x)
        freqs, power = power_spectral_density(X, 1000)
        assert np.all(power >= 0)

    def test_psd_dc_component(self):
        """PSD of constant signal should have energy only at DC."""
        N = 16
        x = np.ones(N)
        X = fft(x)
        freqs, power = power_spectral_density(X, 1000)
        assert power[0] > 0
        assert np.all(power[1:] < 1e-10)

    def test_psd_frequency_axis(self):
        """PSD frequency axis should be correctly spaced."""
        N = 16
        sr = 1000
        x = np.random.randn(N)
        X = fft(x)
        freqs, power = power_spectral_density(X, sr)
        assert freqs[0] == 0
        assert abs(freqs[1] - sr / N) < 1e-10


class TestMagnitudeToDB:
    """Test magnitude to dB conversion."""

    def test_db_conversion(self):
        """Magnitude of 1 should give 0 dB."""
        mag = np.array([1.0, 2.0, 0.5])
        db = magnitude_to_db(mag)
        assert abs(db[0]) < 1e-10
        assert abs(db[1] - 20 * np.log10(2)) < 1e-10
        assert abs(db[2] + 20 * np.log10(2)) < 1e-10

    def test_db_zero_handling(self):
        """Magnitude of 0 should not cause errors (should use eps)."""
        mag = np.array([0.0, 1e-15, 1.0])
        db = magnitude_to_db(mag)
        assert np.all(np.isfinite(db))


class TestPeakDetection:
    """Test peak detection in magnitude spectrum."""

    def test_peak_detection_simple(self):
        """Should detect a clear peak."""
        N = 16
        freqs = np.arange(N) * 10
        # Create a spectrum with a clear peak at index 5
        magnitudes = np.zeros(N)
        magnitudes[5] = 10.0
        magnitudes[4] = 1.0
        magnitudes[6] = 1.0
        peaks = detect_peaks(freqs, magnitudes)
        assert len(peaks) >= 1
        assert abs(peaks[0][0] - 50) < 1

    def test_peak_detection_multiple(self):
        """Should detect multiple peaks."""
        N = 32
        freqs = np.arange(N) * 10
        magnitudes = np.zeros(N)
        magnitudes[5] = 10.0
        magnitudes[15] = 8.0
        magnitudes[25] = 6.0
        peaks = detect_peaks(freqs, magnitudes, threshold_ratio=0.1)
        assert len(peaks) >= 3

    def test_peak_detection_no_peaks(self):
        """Should return empty list when no peaks above threshold."""
        N = 16
        freqs = np.arange(N)
        magnitudes = np.ones(N) * 0.01  # All equal, low magnitude
        peaks = detect_peaks(freqs, magnitudes, threshold_ratio=0.5)
        assert len(peaks) == 0


class TestWindowFunctions:
    """Test window function application."""

    def test_window_energy(self):
        """Window should not change signal energy drastically."""
        N = 64
        x = np.ones(N)
        for wtype in ['hann', 'hamming', 'blackman', 'bartlett', 'rectangular']:
            w = apply_window(x, wtype)
            assert len(w) == N
            assert np.all(np.isfinite(w))

    def test_rectangular_window(self):
        """Rectangular window should be all ones."""
        N = 16
        x = np.random.randn(N)
        w = apply_window(x, 'rectangular')
        assert np.allclose(w, x)

    def test_hann_window_properties(self):
        """Hann window should start and end at zero."""
        N = 64
        x = np.ones(N)
        w = apply_window(x, 'hann')
        assert abs(w[0]) < 1e-10
        assert abs(w[-1]) < 1e-10


class TestSpectralLeakage:
    """Test spectral leakage analysis."""

    def test_leakage_detection(self):
        """Should detect leakage when freq doesn't align with bins."""
        sample_rate = 1000
        N = 256
        # 37.5 Hz doesn't align with bin frequency (1000/256 = 3.90625 Hz)
        data = spectral_leakage_example(sample_rate, 37.5, N)
        assert data['leakage'] is True

    def test_no_leakage(self):
        """Should not detect leakage when freq aligns with bins."""
        sample_rate = 1000
        N = 256
        # 39.0625 Hz = 10 * (1000/256) aligns perfectly
        data = spectral_leakage_example(sample_rate, 39.0625, N)
        assert data['leakage'] is False


class TestFrequencyEstimation:
    """Test frequency estimation utilities."""

    def test_frequency_resolution(self):
        """Frequency resolution should be sample_rate / N."""
        assert compute_frequency_resolution(1000, 100) == 10.0
        assert compute_frequency_resolution(44100, 1024) == pytest.approx(43.0664, abs=1e-4)

    def test_estimate_frequency_peak_given(self):
        """Should return the frequency at the given peak index."""
        freqs = np.array([0, 10, 20, 30, 40])
        mags = np.array([1, 2, 10, 3, 1])
        freq = estimate_frequency(freqs, mags, peak_idx=2)
        assert abs(freq - 20) < 1

    def test_estimate_frequency_auto(self):
        """Should find the peak automatically."""
        freqs = np.array([0, 10, 20, 30, 40])
        mags = np.array([1, 2, 10, 3, 1])
        freq = estimate_frequency(freqs, mags)
        assert abs(freq - 20) < 1


class TestDynamicRange:
    """Test dynamic range computation."""

    def test_dynamic_range(self):
        """Dynamic range should be max - min in dB."""
        mag = np.array([1.0, 0.1, 0.01])
        dr = compute_dynamic_range(mag)
        expected = 20 * np.log10(1.0 / 0.01)
        assert abs(dr - expected) < 1

    def test_dynamic_range_constant(self):
        """Dynamic range of constant signal should be 0."""
        mag = np.ones(10)
        dr = compute_dynamic_range(mag)
        assert abs(dr) < 1e-10
