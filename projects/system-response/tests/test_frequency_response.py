"""Tests for FrequencyResponse."""

import numpy as np
import pytest

from src.transfer_function import TransferFunction
from src.frequency_response import FrequencyResponse


class TestFrequencyResponse:
    """Test frequency-domain analysis."""

    def setup_method(self):
        # G(s) = 1 / (s+1)
        self.tf1 = TransferFunction([1], [1, 1])
        self.fr1 = FrequencyResponse(self.tf1)

        # G(s) = 1 / (s^2 + 0.2s + 1) -- resonant system
        self.tf2 = TransferFunction([1], [1, 0.2, 1])
        self.fr2 = FrequencyResponse(self.tf2)

    def test_bode_data(self):
        bode = self.fr1.bode()
        assert len(bode.omega) > 0
        assert len(bode.magnitude_db) == len(bode.omega)
        assert len(bode.phase_deg) == len(bode.omega)

    def test_bode_dc_magnitude(self):
        bode = self.fr1.bode(omega=np.array([0.001]))
        # At very low freq, magnitude should be ~0 dB (gain=1)
        assert abs(bode.magnitude_db[0]) < 1.0

    def test_bode_high_freq_roll_off(self):
        omega = np.array([0.01, 100.0])
        bode = self.fr1.bode(omega=omega)
        # First-order: -20 dB/decade
        assert bode.magnitude_db[1] < bode.magnitude_db[0]

    def test_bode_phase_first_order(self):
        omega = np.array([0.001, 1.0, 1000.0])
        bode = self.fr1.bode(omega=omega)
        # Phase goes from 0 to -90
        assert bode.phase_deg[0] > -10
        assert bode.phase_deg[2] < -80

    def test_nyquist_data(self):
        nyq = self.fr1.nyquist()
        assert len(nyq.real) > 0
        assert len(nyq.imag) == len(nyq.real)

    def test_nyquist_shape(self):
        # First-order: Nyquist is a semicircle in the lower half
        nyq = self.fr1.nyquist(omega=np.logspace(-2, 2, 1000))
        # All imag parts should be negative (for stable first-order)
        assert np.all(nyq.imag <= 0.01)

    def test_margins_stable_system(self):
        # G(s) = 10/(s+1)(s+2)(s+3) -- proper system with finite margins
        tf = TransferFunction([10], [1, 6, 11, 6])
        fr = FrequencyResponse(tf)
        margins = fr.margins()
        # Should have positive gain margin for this stable system
        if margins.gain_margin_db is not None:
            assert margins.gain_margin_db > 0

    def test_eval(self):
        # G(j*0) = 1
        val = self.fr1.eval(0.001)
        assert abs(abs(val) - 1.0) < 0.01

    def test_magnitude(self):
        mag = self.fr1.magnitude(0.001)
        assert abs(mag) < 0.1  # ~0 dB

    def test_phase(self):
        phase = self.fr1.phase(0.001)
        assert abs(phase) < 5.0  # ~0 degrees

    def test_resonance_peak(self):
        # Second-order with low damping should have resonance
        result = self.fr2.resonance_peak()
        assert "peak_db" in result
        assert "peak_freq" in result
        assert result["peak_db"] > 0  # Should have a peak above 0 dB

    def test_bandwidth(self):
        bw = self.fr1.bandwidth()
        assert bw > 0
        assert bw < 100

    def test_custom_omega(self):
        omega = np.logspace(-1, 1, 50)
        bode = self.fr1.bode(omega=omega)
        np.testing.assert_allclose(bode.omega, omega, atol=1e-10)
