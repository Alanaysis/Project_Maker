"""Tests for PerformanceMetrics."""

import numpy as np
import pytest

from src.transfer_function import TransferFunction
from src.performance import PerformanceMetrics


class TestPerformanceMetrics:
    """Test step-response performance metrics."""

    def test_first_order_metrics(self):
        # 1/(s+1): tau=1, no overshoot
        tf = TransferFunction([1], [1, 1])
        pm = PerformanceMetrics(tf)
        metrics = pm.step_metrics(t_final=10)

        assert metrics.overshoot_pct < 1.0  # No overshoot
        assert metrics.steady_state_error < 0.01
        assert abs(metrics.final_value - 1.0) < 0.01
        # Rise time ~ 2.2*tau = 2.2 for first order
        assert 1.5 < metrics.rise_time < 3.0

    def test_second_order_underdamped(self):
        # 1/(s^2 + 0.5s + 1): zeta=0.25, should have overshoot
        tf = TransferFunction([1], [1, 0.5, 1])
        pm = PerformanceMetrics(tf)
        metrics = pm.step_metrics(t_final=20)

        assert metrics.overshoot_pct > 20  # Significant overshoot
        assert abs(metrics.final_value - 1.0) < 0.05

    def test_second_order_overdamped(self):
        # 1/(s^2 + 4s + 1): zeta=2, no overshoot
        tf = TransferFunction([1], [1, 4, 1])
        pm = PerformanceMetrics(tf)
        metrics = pm.step_metrics(t_final=20)

        assert metrics.overshoot_pct < 1.0
        assert abs(metrics.final_value - 1.0) < 0.05

    def test_analytical_second_order(self):
        # Standard second-order with zeta=0.5, omega_n=2
        metrics = PerformanceMetrics.second_order_metrics(omega_n=2, zeta=0.5)

        # Analytical overshoot: exp(-pi*zeta/sqrt(1-zeta^2)) ~ 16.3%
        expected_os = np.exp(-0.5 * np.pi / np.sqrt(0.75)) * 100
        assert abs(metrics.overshoot_pct - expected_os) < 1.0

        # Settling time: 4/(zeta*omega_n) = 4/(0.5*2) = 4
        assert abs(metrics.settling_time - 4.0) < 0.5

    def test_steady_state_error_step(self):
        # Type 0 system: G(s) = 1/(s+1), Kp=1, SSE = 1/(1+Kp) = 0.5
        tf = TransferFunction([1], [1, 1])
        pm = PerformanceMetrics(tf)
        sse = pm.steady_state_error("step")
        assert abs(sse - 0.5) < 0.01  # SSE = 1/(1+1) = 0.5

    def test_steady_state_error_ramp(self):
        # Type 0 system has infinite SSE for ramp
        tf = TransferFunction([1], [1, 1])
        pm = PerformanceMetrics(tf)
        sse = pm.steady_state_error("ramp")
        assert abs(sse) > 1e6  # Effectively infinite for type 0

    def test_steady_state_error_integrator(self):
        # Type 1 system: 1/(s(s+1)) has zero SSE for step
        tf = TransferFunction([1], [1, 1, 0])
        pm = PerformanceMetrics(tf)
        sse = pm.steady_state_error("step")
        assert abs(sse) < 0.01

    def test_peak_value(self):
        # System with overshoot
        tf = TransferFunction([1], [1, 0.2, 1])
        pm = PerformanceMetrics(tf)
        metrics = pm.step_metrics(t_final=30)
        assert metrics.peak_value > 1.0  # Overshoot means peak > final
        assert metrics.peak_time > 0

    def test_analytical_invalid_zeta(self):
        with pytest.raises(ValueError):
            PerformanceMetrics.second_order_metrics(omega_n=1, zeta=1.5)

    def test_invalid_input_type(self):
        tf = TransferFunction([1], [1, 1])
        pm = PerformanceMetrics(tf)
        with pytest.raises(ValueError):
            pm.steady_state_error("invalid")
