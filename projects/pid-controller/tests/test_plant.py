"""
Tests for Plant models (FirstOrderPlant, SecondOrderPlant, DelaySystem).

Tests cover:
- Initialization and parameter validation
- Step response behavior
- Steady-state response
- Reset functionality
- Different damping ratios for second-order system
- Delay system behavior
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import numpy as np
from src.plant import FirstOrderPlant, SecondOrderPlant, DelaySystem


class TestFirstOrderPlant:
    """Tests for first-order plant model."""

    def test_default_values(self):
        plant = FirstOrderPlant()
        assert plant.K == 1.0
        assert plant.tau == 1.0
        assert plant.dt == 0.01

    def test_custom_values(self):
        plant = FirstOrderPlant(K=2.0, tau=3.0, dt=0.02)
        assert plant.K == 2.0
        assert plant.tau == 3.0
        assert plant.dt == 0.02

    def test_invalid_tau(self):
        with pytest.raises(ValueError, match="tau must be positive"):
            FirstOrderPlant(tau=0)
        with pytest.raises(ValueError, match="tau must be positive"):
            FirstOrderPlant(tau=-1)

    def test_invalid_dt(self):
        with pytest.raises(ValueError, match="dt must be positive"):
            FirstOrderPlant(dt=0)

    def test_initial_output(self):
        plant = FirstOrderPlant(initial_output=5.0)
        assert plant.output == 5.0

    def test_steady_state_response(self):
        """At steady state, output should equal K * input."""
        plant = FirstOrderPlant(K=2.0, tau=1.0, dt=0.01)

        # Apply constant input for many time steps (5x time constant)
        for _ in range(5000):
            plant.update(3.0)

        # After 50 time constants, should be very close to steady state
        expected = 2.0 * 3.0  # K * input
        assert abs(plant.output - expected) < 0.01

    def test_step_response_shape(self):
        """First-order step response should be exponential."""
        plant = FirstOrderPlant(K=1.0, tau=1.0, dt=0.01)
        outputs = []

        for _ in range(1000):
            plant.update(1.0)
            outputs.append(plant.output)

        outputs = np.array(outputs)

        # Should be monotonically increasing
        assert all(outputs[i] <= outputs[i + 1] for i in range(len(outputs) - 1))

        # Should approach 1.0 (K * input)
        assert abs(outputs[-1] - 1.0) < 0.01

    def test_zero_input(self):
        plant = FirstOrderPlant(K=1.0, tau=1.0, dt=0.01)
        for _ in range(100):
            output = plant.update(0.0)

        # With zero input, output should approach zero
        assert abs(output) < 0.01

    def test_reset(self):
        plant = FirstOrderPlant(initial_output=0.0)
        for _ in range(100):
            plant.update(1.0)

        plant.reset()
        assert plant.output == 0.0

    def test_repr(self):
        plant = FirstOrderPlant(K=2.0, tau=3.0)
        assert "FirstOrderPlant" in repr(plant)
        assert "2.0" in repr(plant)
        assert "3.0" in repr(plant)


class TestSecondOrderPlant:
    """Tests for second-order plant model."""

    def test_default_values(self):
        plant = SecondOrderPlant()
        assert plant.K == 1.0
        assert plant.omega_n == 1.0
        assert plant.zeta == 0.7
        assert plant.dt == 0.01

    def test_custom_values(self):
        plant = SecondOrderPlant(K=2.0, omega_n=3.0, zeta=0.5, dt=0.02)
        assert plant.K == 2.0
        assert plant.omega_n == 3.0
        assert plant.zeta == 0.5
        assert plant.dt == 0.02

    def test_invalid_omega_n(self):
        with pytest.raises(ValueError, match="omega_n must be positive"):
            SecondOrderPlant(omega_n=0)

    def test_invalid_zeta(self):
        with pytest.raises(ValueError, match="zeta must be non-negative"):
            SecondOrderPlant(zeta=-0.1)

    def test_invalid_dt(self):
        with pytest.raises(ValueError, match="dt must be positive"):
            SecondOrderPlant(dt=0)

    def test_steady_state_response(self):
        """At steady state, second-order output should equal K * input."""
        plant = SecondOrderPlant(K=1.0, omega_n=1.0, zeta=1.0, dt=0.01)

        # Run for long enough (critically damped, ~10 seconds)
        for _ in range(10000):
            plant.update(1.0)

        assert abs(plant.output - 1.0) < 0.01

    def test_underdamped_oscillation(self):
        """Underdamped system should overshoot."""
        plant = SecondOrderPlant(K=1.0, omega_n=2.0, zeta=0.2, dt=0.001)
        outputs = []

        for _ in range(10000):
            plant.update(1.0)
            outputs.append(plant.output)

        max_output = max(outputs)

        # Underdamped system should overshoot (max > 1.0)
        assert max_output > 1.0

    def test_overdamped_no_overshoot(self):
        """Overdamped system should not overshoot."""
        plant = SecondOrderPlant(K=1.0, omega_n=2.0, zeta=2.0, dt=0.001)
        outputs = []

        for _ in range(10000):
            plant.update(1.0)
            outputs.append(plant.output)

        # Overdamped system should not overshoot
        assert all(o <= 1.0 + 1e-6 for o in outputs)

    def test_critically_damped(self):
        """Critically damped should be fastest without overshoot."""
        plant = SecondOrderPlant(K=1.0, omega_n=2.0, zeta=1.0, dt=0.001)
        outputs = []

        for _ in range(10000):
            plant.update(1.0)
            outputs.append(plant.output)

        # Should not overshoot
        assert all(o <= 1.0 + 1e-6 for o in outputs)

        # Should reach steady state
        assert abs(outputs[-1] - 1.0) < 0.01

    def test_velocity_property(self):
        plant = SecondOrderPlant(initial_velocity=5.0)
        assert plant.velocity == 5.0

    def test_reset(self):
        plant = SecondOrderPlant(initial_position=0.0, initial_velocity=0.0)
        for _ in range(100):
            plant.update(1.0)

        plant.reset()
        assert plant.output == 0.0
        assert plant.velocity == 0.0

    def test_repr(self):
        plant = SecondOrderPlant(K=1.0, omega_n=2.0, zeta=0.5)
        repr_str = repr(plant)
        assert "SecondOrderPlant" in repr_str
        assert "1.0" in repr_str
        assert "2.0" in repr_str
        assert "0.5" in repr_str


class TestDelaySystem:
    """Tests for delay system plant model."""

    def test_default_values(self):
        plant = DelaySystem()
        assert plant.K == 1.0
        assert plant.tau == 1.0
        assert plant.delay == 1.0
        assert plant.dt == 0.01

    def test_custom_values(self):
        plant = DelaySystem(K=2.0, tau=3.0, delay=5.0, dt=0.02)
        assert plant.K == 2.0
        assert plant.tau == 3.0
        assert plant.delay == 5.0
        assert plant.dt == 0.02

    def test_invalid_tau(self):
        with pytest.raises(ValueError, match="tau must be positive"):
            DelaySystem(tau=0)
        with pytest.raises(ValueError, match="tau must be positive"):
            DelaySystem(tau=-1)

    def test_invalid_delay(self):
        with pytest.raises(ValueError, match="delay must be non-negative"):
            DelaySystem(delay=-1)

    def test_invalid_dt(self):
        with pytest.raises(ValueError, match="dt must be positive"):
            DelaySystem(dt=0)

    def test_initial_output(self):
        plant = DelaySystem(initial_output=5.0)
        assert plant.output == 5.0

    def test_delay_effect(self):
        """Output should not respond immediately due to delay."""
        plant = DelaySystem(K=1.0, tau=1.0, delay=1.0, dt=0.1)

        # Apply step input
        outputs = []
        for _ in range(20):
            outputs.append(plant.update(1.0))

        # During the delay period (first 10 steps), output should be near zero
        # (only the delayed input affects the plant)
        delay_steps = int(1.0 / 0.1)
        for i in range(delay_steps - 1):
            assert abs(outputs[i]) < 0.1

    def test_steady_state_response(self):
        """At steady state, output should equal K * input."""
        plant = DelaySystem(K=2.0, tau=1.0, delay=0.5, dt=0.01)

        # Apply constant input for long enough (delay + 5*tau)
        total_steps = int((0.5 + 5.0) / 0.01)
        for _ in range(total_steps):
            plant.update(3.0)

        # Should approach K * input = 6.0
        assert abs(plant.output - 6.0) < 0.1

    def test_reset(self):
        plant = DelaySystem(initial_output=0.0)
        for _ in range(100):
            plant.update(1.0)

        plant.reset()
        assert plant.output == 0.0

    def test_zero_delay(self):
        """With zero delay, should behave like first-order system."""
        plant_delay = DelaySystem(K=1.0, tau=1.0, delay=0.0, dt=0.01)
        plant_first = FirstOrderPlant(K=1.0, tau=1.0, dt=0.01)

        for _ in range(1000):
            out_delay = plant_delay.update(1.0)
            out_first = plant_first.update(1.0)

        # Should be approximately equal
        assert abs(out_delay - out_first) < 0.01

    def test_repr(self):
        plant = DelaySystem(K=2.0, tau=3.0, delay=5.0)
        repr_str = repr(plant)
        assert "DelaySystem" in repr_str
        assert "2.0" in repr_str
        assert "3.0" in repr_str
        assert "5.0" in repr_str
