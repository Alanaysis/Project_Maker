"""Tests for SystemIdentifier."""

import numpy as np
import pytest
from scipy import signal

from src.transfer_function import TransferFunction
from src.system_id import SystemIdentifier


class TestSystemIdentifier:
    """Test system identification methods."""

    def test_from_step_response_first_order(self):
        # Generate step response of 5/(2s+1)
        tf_true = TransferFunction([5], [2, 1])
        sys_true = signal.lti(tf_true.num, tf_true.den)
        t = np.linspace(0, 15, 1000)
        _, y = signal.step(sys_true, T=t)

        result = SystemIdentifier.from_step_response(t, y, model_order=1)
        assert result.order == (1, 1)
        # Gain should be close to 5
        assert abs(result.tf.dc_gain - 5.0) < 1.0
        # Residual should be small
        assert result.residual < 0.5

    def test_from_step_response_second_order(self):
        # Generate step response of 1/(s^2 + s + 1)
        tf_true = TransferFunction([1], [1, 1, 1])
        sys_true = signal.lti(tf_true.num, tf_true.den)
        t = np.linspace(0, 20, 2000)
        _, y = signal.step(sys_true, T=t)

        result = SystemIdentifier.from_step_response(t, y, model_order=2)
        assert result.order == (2, 2)
        assert result.residual < 0.5  # Good fit

    def test_from_step_response_residual(self):
        tf_true = TransferFunction([1], [1, 1])
        sys_true = signal.lti(tf_true.num, tf_true.den)
        t = np.linspace(0, 10, 1000)
        _, y = signal.step(sys_true, T=t)

        result = SystemIdentifier.from_step_response(t, y, model_order=1)
        # For first-order to first-order, residual should be very small
        assert result.residual < 0.1

    def test_from_frequency_response(self):
        # Generate frequency response data
        omega = np.logspace(-1, 1, 50)
        tf_true = TransferFunction([1], [1, 1])
        resp = tf_true.eval_freq(omega)
        mag_db = 20 * np.log10(np.abs(resp))
        phase_deg = np.degrees(np.angle(resp))

        result = SystemIdentifier.from_frequency_response(
            omega, mag_db, phase_deg, order=1
        )
        assert result.order == (1, 1)

    def test_from_impulse_response(self):
        # Generate impulse response
        tf_true = TransferFunction([1], [1, 3, 2])
        sys_true = signal.lti(tf_true.num, tf_true.den)
        t = np.linspace(0, 10, 1000)
        _, y = signal.impulse(sys_true, T=t)

        result = SystemIdentifier.from_impulse_response(t, y, n_poles=2)
        assert result.order == (0, 2)

    def test_invalid_model_order(self):
        t = np.linspace(0, 10, 100)
        y = np.ones(100)
        with pytest.raises(ValueError):
            SystemIdentifier.from_step_response(t, y, model_order=3)
