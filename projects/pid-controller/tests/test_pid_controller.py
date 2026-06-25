"""
Tests for PIDController.

Tests cover:
- Basic proportional control
- Integral accumulation and steady-state error elimination
- Derivative action and damping
- Anti-windup protection
- Output clamping
- Reset functionality
- Edge cases (zero gains, negative values)
- Integral separation
- Incomplete derivative
- Dead zone
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import numpy as np
from src.pid_controller import PIDController


class TestPIDControllerInit:
    """Test PIDController initialization."""

    def test_default_values(self):
        controller = PIDController()
        assert controller.Kp == 1.0
        assert controller.Ki == 0.0
        assert controller.Kd == 0.0
        assert controller.dt == 0.01
        assert controller.integral_separation is False
        assert controller.incomplete_derivative is False
        assert controller.dead_zone == 0.0

    def test_custom_values(self):
        controller = PIDController(
            Kp=2.0, Ki=0.5, Kd=0.1,
            output_min=-10, output_max=10,
            dt=0.02
        )
        assert controller.Kp == 2.0
        assert controller.Ki == 0.5
        assert controller.Kd == 0.1
        assert controller.output_min == -10
        assert controller.output_max == 10
        assert controller.dt == 0.02

    def test_improved_variant_params(self):
        controller = PIDController(
            integral_separation=True,
            integral_separation_threshold=5.0,
            incomplete_derivative=True,
            incomplete_derivative_coeff=0.3,
            dead_zone=0.1,
        )
        assert controller.integral_separation is True
        assert controller.integral_separation_threshold == 5.0
        assert controller.incomplete_derivative is True
        assert controller.incomplete_derivative_coeff == 0.3
        assert controller.dead_zone == 0.1

    def test_invalid_dt(self):
        with pytest.raises(ValueError, match="dt must be positive"):
            PIDController(dt=0)
        with pytest.raises(ValueError, match="dt must be positive"):
            PIDController(dt=-1)

    def test_invalid_filter_coeff(self):
        with pytest.raises(ValueError, match="derivative_filter_coeff"):
            PIDController(derivative_filter_coeff=0)
        with pytest.raises(ValueError, match="derivative_filter_coeff"):
            PIDController(derivative_filter_coeff=1.5)

    def test_invalid_separation_threshold(self):
        with pytest.raises(ValueError, match="integral_separation_threshold"):
            PIDController(integral_separation_threshold=-1.0)

    def test_invalid_incomplete_derivative_coeff(self):
        with pytest.raises(ValueError, match="incomplete_derivative_coeff"):
            PIDController(incomplete_derivative_coeff=0)
        with pytest.raises(ValueError, match="incomplete_derivative_coeff"):
            PIDController(incomplete_derivative_coeff=1.5)

    def test_invalid_dead_zone(self):
        with pytest.raises(ValueError, match="dead_zone"):
            PIDController(dead_zone=-0.1)


class TestProportionalControl:
    """Test proportional-only control behavior."""

    def test_positive_error_gives_positive_output(self):
        controller = PIDController(Kp=2.0, Ki=0, Kd=0)
        output = controller.update(setpoint=1.0, measurement=0.5)
        assert output > 0

    def test_negative_error_gives_negative_output(self):
        controller = PIDController(Kp=2.0, Ki=0, Kd=0)
        output = controller.update(setpoint=0.5, measurement=1.0)
        assert output < 0

    def test_proportional_gain_scales_output(self):
        c1 = PIDController(Kp=1.0, Ki=0, Kd=0)
        c2 = PIDController(Kp=2.0, Ki=0, Kd=0)

        out1 = c1.update(setpoint=1.0, measurement=0.5)
        out2 = c2.update(setpoint=1.0, measurement=0.5)

        # Kp=2 should give double the output of Kp=1
        assert abs(out2 - 2 * out1) < 1e-10

    def test_zero_error_gives_zero_output(self):
        controller = PIDController(Kp=2.0, Ki=0, Kd=0)
        output = controller.update(setpoint=1.0, measurement=1.0)
        assert abs(output) < 1e-10


class TestIntegralControl:
    """Test integral term behavior."""

    def test_integral_accumulates_error(self):
        controller = PIDController(Kp=0, Ki=1.0, Kd=0, dt=0.1)

        # Apply constant error for several steps
        for _ in range(10):
            output = controller.update(setpoint=1.0, measurement=0.5)

        # Integral should have accumulated
        assert abs(output) > 0

    def test_integral_eliminates_steady_state_error(self):
        """P-only cannot reach setpoint; PI can."""
        # P-only
        p_only = PIDController(Kp=1.0, Ki=0, Kd=0, dt=0.01)
        for _ in range(10000):
            # Simulate: output approaches Kp*error asymptotically
            measurement = p_only.update(1.0, 0.0, 0) * 0.01
            p_only.update(1.0, measurement, 0)

        # PI controller
        pi = PIDController(Kp=1.0, Ki=0.5, Kd=0, dt=0.01)
        for _ in range(10000):
            measurement = pi.update(1.0, 0.0, 0) * 0.01
            pi.update(1.0, measurement, 0)

        # PI should have less steady-state error
        p_error = abs(p_only.history["error"][-1])
        pi_error = abs(pi.history["error"][-1])
        assert pi_error <= p_error

    def test_anti_windup_clamps_integral(self):
        controller = PIDController(
            Kp=0, Ki=1.0, Kd=0,
            integral_min=-5, integral_max=5,
            dt=0.1
        )

        # Apply large error for many steps
        for _ in range(100):
            controller.update(setpoint=100.0, measurement=0.0)

        # Integral should be clamped
        assert abs(controller._integral) <= 5.0 + 1e-10


class TestDerivativeControl:
    """Test derivative term behavior."""

    def test_derivative_reacts_to_rate_of_change(self):
        controller = PIDController(Kp=0, Ki=0, Kd=1.0, dt=0.01)

        # First step: no derivative (no previous measurement)
        out1 = controller.update(setpoint=1.0, measurement=1.0)

        # Rapid change in measurement
        out2 = controller.update(setpoint=1.0, measurement=0.5)

        # Should have non-zero derivative response
        assert abs(out2) > abs(out1)

    def test_derivative_on_measurement_not_error(self):
        """Derivative should be on measurement, not error, to avoid kick."""
        controller = PIDController(Kp=0, Ki=0, Kd=1.0, dt=0.01)

        # First step
        controller.update(setpoint=1.0, measurement=1.0)

        # Step change in setpoint only (measurement unchanged)
        output = controller.update(setpoint=2.0, measurement=1.0)

        # With derivative on measurement, step in setpoint should not cause
        # a large derivative kick (measurement didn't change)
        assert abs(output) < 10  # Should be small


class TestOutputClamping:
    """Test output clamping behavior."""

    def test_output_clamped_to_max(self):
        controller = PIDController(
            Kp=100.0, Ki=0, Kd=0,
            output_max=5.0
        )
        output = controller.update(setpoint=10.0, measurement=0.0)
        assert output == 5.0

    def test_output_clamped_to_min(self):
        controller = PIDController(
            Kp=100.0, Ki=0, Kd=0,
            output_min=-5.0
        )
        output = controller.update(setpoint=-10.0, measurement=0.0)
        assert output == -5.0

    def test_output_within_range(self):
        controller = PIDController(
            Kp=1.0, Ki=0, Kd=0,
            output_min=-10, output_max=10
        )
        output = controller.update(setpoint=1.0, measurement=0.5)
        assert -10 <= output <= 10


class TestReset:
    """Test reset functionality."""

    def test_reset_clears_state(self):
        controller = PIDController(Kp=1.0, Ki=1.0, Kd=1.0, dt=0.1)

        # Run some steps
        for _ in range(100):
            controller.update(setpoint=1.0, measurement=0.5)

        # Verify state is non-zero
        assert controller._integral != 0
        assert len(controller._history["time"]) == 100

        # Reset
        controller.reset()

        # Verify state is cleared
        assert controller._integral == 0
        assert controller._prev_error == 0
        assert controller._first_update is True
        assert len(controller._history["time"]) == 0

    def test_reset_allows_fresh_start(self):
        controller = PIDController(Kp=1.0, Ki=0, Kd=0, dt=0.1)

        # First run
        out1 = controller.update(setpoint=1.0, measurement=0.5)
        controller.reset()

        # Second run should give same result
        out2 = controller.update(setpoint=1.0, measurement=0.5)
        assert abs(out1 - out2) < 1e-10


class TestHistory:
    """Test history recording."""

    def test_history_records_all_signals(self):
        controller = PIDController(Kp=1.0, Ki=0.5, Kd=0.1, dt=0.1)

        for i in range(10):
            controller.update(setpoint=1.0, measurement=0.5, t=i * 0.1)

        history = controller.history

        assert len(history["time"]) == 10
        assert len(history["setpoint"]) == 10
        assert len(history["measurement"]) == 10
        assert len(history["error"]) == 10
        assert len(history["p_term"]) == 10
        assert len(history["i_term"]) == 10
        assert len(history["d_term"]) == 10
        assert len(history["output"]) == 10

    def test_history_as_numpy_arrays(self):
        controller = PIDController(Kp=1.0, Ki=0, Kd=0, dt=0.1)

        for i in range(5):
            controller.update(setpoint=1.0, measurement=0.5, t=i * 0.1)

        history = controller.history
        assert isinstance(history["time"], np.ndarray)
        assert isinstance(history["error"], np.ndarray)


class TestGainsProperty:
    """Test gains getter and setter."""

    def test_get_gains(self):
        controller = PIDController(Kp=1.0, Ki=2.0, Kd=3.0)
        assert controller.gains == (1.0, 2.0, 3.0)

    def test_set_gains(self):
        controller = PIDController(Kp=1.0, Ki=2.0, Kd=3.0)
        controller.gains = (4.0, 5.0, 6.0)
        assert controller.Kp == 4.0
        assert controller.Ki == 5.0
        assert controller.Kd == 6.0

    def test_tuning_params(self):
        controller = PIDController(Kp=1.0, Ki=2.0, Kd=3.0)
        params = controller.get_tuning_params()
        assert params == {"Kp": 1.0, "Ki": 2.0, "Kd": 3.0}

    def test_set_tuning_params(self):
        controller = PIDController()
        controller.set_tuning_params({"Kp": 4.0, "Ki": 5.0})
        assert controller.Kp == 4.0
        assert controller.Ki == 5.0
        assert controller.Kd == 0.0  # unchanged (default)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_all_gains(self):
        controller = PIDController(Kp=0, Ki=0, Kd=0)
        output = controller.update(setpoint=1.0, measurement=0.0)
        assert output == 0.0

    def test_very_small_dt(self):
        controller = PIDController(Kp=1.0, Ki=0, Kd=0, dt=0.001)
        output = controller.update(setpoint=1.0, measurement=0.5)
        assert isinstance(output, float)

    def test_large_error(self):
        controller = PIDController(
            Kp=1.0, Ki=0, Kd=0,
            output_min=-1000, output_max=1000
        )
        output = controller.update(setpoint=1000.0, measurement=0.0)
        assert output == 1000.0

    def test_repr(self):
        controller = PIDController(Kp=1.0, Ki=2.0, Kd=3.0)
        repr_str = repr(controller)
        assert "PIDController" in repr_str
        assert "1.0" in repr_str
        assert "2.0" in repr_str
        assert "3.0" in repr_str


class TestIntegralSeparation:
    """Test integral separation feature."""

    def test_integral_separation_disables_when_error_large(self):
        """Integral should not accumulate when error exceeds threshold."""
        controller = PIDController(
            Kp=1.0, Ki=1.0, Kd=0, dt=0.1,
            integral_separation=True,
            integral_separation_threshold=5.0,
        )

        # Large error (|error| > 5.0): integral should NOT accumulate
        controller.update(setpoint=100.0, measurement=0.0)  # error=100
        assert controller._integral == 0.0

    def test_integral_separation_enables_when_error_small(self):
        """Integral should accumulate when error is within threshold."""
        controller = PIDController(
            Kp=1.0, Ki=1.0, Kd=0, dt=0.1,
            integral_separation=True,
            integral_separation_threshold=5.0,
        )

        # Small error (|error| < 5.0): integral should accumulate
        controller.update(setpoint=2.0, measurement=1.0)  # error=1.0
        assert controller._integral != 0.0

    def test_integral_separation_transitions(self):
        """Integral should start accumulating when error drops below threshold."""
        controller = PIDController(
            Kp=1.0, Ki=1.0, Kd=0, dt=0.1,
            integral_separation=True,
            integral_separation_threshold=5.0,
        )

        # Large error: no integral
        controller.update(setpoint=100.0, measurement=0.0)
        assert controller._integral == 0.0

        # Small error: integral accumulates
        controller.update(setpoint=2.0, measurement=1.0)
        assert controller._integral != 0.0

    def test_without_integral_separation(self):
        """Without integral separation, integral should always accumulate."""
        controller = PIDController(
            Kp=1.0, Ki=1.0, Kd=0, dt=0.1,
            integral_separation=False,
        )

        # Large error: integral should still accumulate
        controller.update(setpoint=100.0, measurement=0.0)
        assert controller._integral != 0.0


class TestIncompleteDerivative:
    """Test incomplete derivative feature."""

    def test_incomplete_derivative_filters_more(self):
        """Incomplete derivative should provide additional filtering."""
        # Without incomplete derivative
        c1 = PIDController(Kp=0, Ki=0, Kd=1.0, dt=0.01, incomplete_derivative=False)
        c1.update(setpoint=1.0, measurement=1.0)
        out1 = c1.update(setpoint=1.0, measurement=0.5)

        # With incomplete derivative
        c2 = PIDController(
            Kp=0, Ki=0, Kd=1.0, dt=0.01,
            incomplete_derivative=True,
            incomplete_derivative_coeff=0.3,
        )
        c2.update(setpoint=1.0, measurement=1.0)
        out2 = c2.update(setpoint=1.0, measurement=0.5)

        # Incomplete derivative should give smaller output (more filtered)
        assert abs(out2) < abs(out1)

    def test_incomplete_derivative_coeff_effect(self):
        """Lower coefficient = more filtering = smaller output."""
        # Higher coefficient (less filtering)
        c1 = PIDController(
            Kp=0, Ki=0, Kd=1.0, dt=0.01,
            incomplete_derivative=True,
            incomplete_derivative_coeff=0.9,
        )
        c1.update(setpoint=1.0, measurement=1.0)
        out1 = c1.update(setpoint=1.0, measurement=0.5)

        # Lower coefficient (more filtering)
        c2 = PIDController(
            Kp=0, Ki=0, Kd=1.0, dt=0.01,
            incomplete_derivative=True,
            incomplete_derivative_coeff=0.1,
        )
        c2.update(setpoint=1.0, measurement=1.0)
        out2 = c2.update(setpoint=1.0, measurement=0.5)

        assert abs(out1) > abs(out2)


class TestDeadZone:
    """Test dead zone feature."""

    def test_dead_zone_zero_output_within_zone(self):
        """Output should be zero when error is within dead zone."""
        controller = PIDController(
            Kp=2.0, Ki=1.0, Kd=0.5, dt=0.1,
            dead_zone=0.5,
        )

        # Error = 0.3, within dead zone of 0.5
        output = controller.update(setpoint=1.0, measurement=0.7)
        assert output == 0.0

    def test_dead_zone_active_outside_zone(self):
        """Output should be non-zero when error exceeds dead zone."""
        controller = PIDController(
            Kp=2.0, Ki=1.0, Kd=0.5, dt=0.1,
            dead_zone=0.5,
        )

        # Error = 2.0, outside dead zone
        output = controller.update(setpoint=3.0, measurement=1.0)
        assert output != 0.0

    def test_dead_zone_boundary(self):
        """Test behavior at dead zone boundary."""
        controller = PIDController(
            Kp=2.0, Ki=0, Kd=0, dt=0.1,
            dead_zone=1.0,
        )

        # Error = 1.0, exactly at boundary (not inside)
        output = controller.update(setpoint=2.0, measurement=1.0)
        assert output != 0.0  # At boundary, should be active

        # Error = 0.99, just inside
        controller2 = PIDController(
            Kp=2.0, Ki=0, Kd=0, dt=0.1,
            dead_zone=1.0,
        )
        output2 = controller2.update(setpoint=1.99, measurement=1.0)
        assert output2 == 0.0

    def test_dead_zone_records_history(self):
        """Dead zone should still record history."""
        controller = PIDController(
            Kp=2.0, Ki=0, Kd=0, dt=0.1,
            dead_zone=0.5,
        )

        controller.update(setpoint=1.0, measurement=0.7)  # In dead zone
        history = controller.history

        assert len(history["time"]) == 1
        assert history["output"][0] == 0.0
        assert abs(history["error"][0] - 0.3) < 1e-10

    def test_dead_zone_disabled_by_default(self):
        """Dead zone should be disabled (0.0) by default."""
        controller = PIDController()
        assert controller.dead_zone == 0.0

        # Normal error should produce output
        output = controller.update(setpoint=1.0, measurement=0.5)
        assert output != 0.0
