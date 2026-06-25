"""Tests for TimeResponse."""

import numpy as np
import pytest

from src.transfer_function import TransferFunction
from src.time_response import TimeResponse


class TestTimeResponse:
    """Test time-domain response computations."""

    def setup_method(self):
        # First-order system: 1/(s+1)
        self.tf1 = TransferFunction([1], [1, 1])
        self.tr1 = TimeResponse(self.tf1)

        # Second-order system: 1/(s^2 + s + 1)
        self.tf2 = TransferFunction([1], [1, 1, 1])
        self.tr2 = TimeResponse(self.tf2)

    def test_step_response_first_order(self):
        data = self.tr1.step(t_final=5)
        # Should approach DC gain (1.0)
        assert abs(data.y[-1] - 1.0) < 0.01
        assert data.u is not None
        assert len(data.t) == len(data.y)

    def test_step_response_second_order(self):
        data = self.tr2.step(t_final=10)
        # Should approach DC gain (1.0)
        assert abs(data.y[-1] - 1.0) < 0.05

    def test_impulse_response_first_order(self):
        data = self.tr1.impulse(t_final=5)
        # Impulse response of 1/(s+1) is e^{-t}, starts at 1
        assert abs(data.y[0] - 1.0) < 0.05
        # Should decay to 0
        assert abs(data.y[-1]) < 0.05

    def test_impulse_response_second_order(self):
        data = self.tr2.impulse(t_final=10)
        # Should decay to 0
        assert abs(data.y[-1]) < 0.05

    def test_ramp_response(self):
        data = self.tr1.ramp(t_final=5)
        # Ramp input should be t
        assert data.u is not None
        np.testing.assert_allclose(data.u, data.t, atol=1e-10)

    def test_lsim(self):
        T = np.linspace(0, 5, 1000)
        u = np.sin(T)
        data = self.tr1.lsim(u, T)
        assert len(data.y) == len(T)

    def test_initial_response(self):
        data = self.tr1.initial(x0=[1.0], t_final=5)
        # Should start at 1 and decay
        assert abs(data.y[0] - 1.0) < 0.1

    def test_custom_time_vector(self):
        T = np.linspace(0, 3, 500)
        data = self.tr1.step(T=T)
        np.testing.assert_allclose(data.t, T, atol=1e-10)

    def test_auto_tfinal(self):
        # For 1/(s+1), dominant pole at -1, tfinal ~ 5
        tf = self.tr1._auto_tfinal()
        assert tf > 0
        assert tf < 100
