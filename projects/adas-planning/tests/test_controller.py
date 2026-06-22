"""
Tests for Control Module.
"""

import unittest
import numpy as np
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.controller import PIDController, MPCController, StanleyController, LQRController


class TestPIDController(unittest.TestCase):
    """Tests for PID controller."""

    def test_proportional_only(self):
        """Test P-only controller."""
        controller = PIDController(Kp=1.0, Ki=0.0, Kd=0.0)

        # Positive error should give positive output
        output = controller.compute(1.0, 0.1)
        self.assertGreater(output, 0)

        # Negative error should give negative output
        controller.reset()
        output = controller.compute(-1.0, 0.1)
        self.assertLess(output, 0)

    def test_integral_accumulation(self):
        """Test that integral term accumulates."""
        controller = PIDController(Kp=0.0, Ki=1.0, Kd=0.0)

        # Accumulate error
        controller.compute(1.0, 0.1)
        controller.compute(1.0, 0.1)
        output = controller.compute(1.0, 0.1)

        # Output should increase due to integral
        self.assertGreater(output, 0.0)

    def test_derivative_response(self):
        """Test derivative term response."""
        controller = PIDController(Kp=0.0, Ki=0.0, Kd=1.0)

        # First step
        controller.compute(0.0, 0.1)

        # Rapid error change should give derivative response
        output = controller.compute(1.0, 0.1)
        self.assertGreater(output, 0)

    def test_output_limits(self):
        """Test output limiting."""
        controller = PIDController(
            Kp=100.0, Ki=0.0, Kd=0.0,
            output_limits=(-1.0, 1.0)
        )

        output = controller.compute(100.0, 0.1)
        self.assertAlmostEqual(output, 1.0, places=5)

        output = controller.compute(-100.0, 0.1)
        self.assertAlmostEqual(output, -1.0, places=5)

    def test_integral_limits(self):
        """Test integral windup protection."""
        controller = PIDController(
            Kp=0.0, Ki=1.0, Kd=0.0,
            integral_limits=(-10.0, 10.0)
        )

        # Accumulate large error
        for _ in range(100):
            controller.compute(1.0, 0.1)

        # Integral should be limited
        self.assertLessEqual(abs(controller.integral), 10.0)

    def test_reset(self):
        """Test controller reset."""
        controller = PIDController(Kp=1.0, Ki=1.0, Kd=1.0)

        # Use controller
        controller.compute(1.0, 0.1)
        controller.compute(1.0, 0.1)

        # Reset
        controller.reset()

        self.assertEqual(controller.integral, 0.0)
        self.assertEqual(controller.prev_error, 0.0)

    def test_convergence(self):
        """Test that PID can converge to zero error."""
        controller = PIDController(Kp=2.0, Ki=0.5, Kd=0.1)

        error = 10.0
        dt = 0.1

        # Simulate for 100 steps
        for _ in range(100):
            output = controller.compute(error, dt)
            # Simulate system response (simplified)
            error -= output * dt

        # Error should be small
        self.assertLess(abs(error), 1.0)


class TestMPCController(unittest.TestCase):
    """Tests for MPC controller."""

    def test_initialization(self):
        """Test MPC initialization."""
        controller = MPCController(horizon=10, dt=0.1)

        self.assertEqual(controller.horizon, 10)
        self.assertEqual(controller.dt, 0.1)

    def test_compute_output(self):
        """Test MPC produces output."""
        controller = MPCController(horizon=5, dt=0.1)

        state = np.array([0.0, 0.0, 0.0])
        reference = [np.array([1.0, 0.0, 0.0])] * 5
        speed = 5.0

        steering = controller.compute(state, reference, speed)

        self.assertIsInstance(steering, float)
        self.assertGreaterEqual(steering, -np.pi / 4)
        self.assertLessEqual(steering, np.pi / 4)

    def test_reset(self):
        """Test MPC reset."""
        controller = MPCController()

        # Use controller
        state = np.array([0.0, 0.0, 0.0])
        reference = [np.array([1.0, 0.0, 0.0])] * 10
        controller.compute(state, reference, 5.0)

        # Reset
        controller.reset()

        self.assertEqual(controller.prev_steering, 0.0)


class TestStanleyController(unittest.TestCase):
    """Tests for Stanley controller."""

    def test_initialization(self):
        """Test Stanley controller initialization."""
        controller = StanleyController(k=1.0, wheelbase=2.5)

        self.assertEqual(controller.k, 1.0)
        self.assertEqual(controller.wheelbase, 2.5)

    def test_steering_computation(self):
        """Test steering angle computation."""
        controller = StanleyController(k=1.0)

        current_pos = np.array([0.0, 0.0])
        current_heading = 0.0
        path = [np.array([0.0, 0.0]), np.array([1.0, 0.0]), np.array([2.0, 0.0])]
        speed = 5.0

        steering = controller.compute_steering(current_pos, current_heading, path, speed)

        self.assertIsInstance(steering, float)
        self.assertGreaterEqual(steering, -np.pi / 4)
        self.assertLessEqual(steering, np.pi / 4)

    def test_cross_track_error_correction(self):
        """Test that controller corrects cross-track error."""
        controller = StanleyController(k=2.0)

        # Vehicle offset to the right of path
        current_pos = np.array([0.5, 1.0])
        current_heading = 0.0
        path = [np.array([0.0, 0.0]), np.array([1.0, 0.0]), np.array([2.0, 0.0])]
        speed = 5.0

        steering = controller.compute_steering(current_pos, current_heading, path, speed)

        # Should produce non-zero steering to correct error
        self.assertNotAlmostEqual(steering, 0.0, places=2)


class TestLQRController(unittest.TestCase):
    """Tests for LQR controller."""

    def test_initialization(self):
        """Test LQR initialization."""
        controller = LQRController()

        self.assertEqual(controller.Q.shape, (2, 2))
        self.assertEqual(controller.R.shape, (1, 1))

    def test_compute_output(self):
        """Test LQR produces output."""
        controller = LQRController()

        steering = controller.compute(
            lateral_error=1.0,
            heading_error=0.1,
            speed=5.0,
            dt=0.1
        )

        self.assertIsInstance(steering, float)
        self.assertGreaterEqual(steering, -np.pi / 4)
        self.assertLessEqual(steering, np.pi / 4)

    def test_error_response(self):
        """Test LQR response to errors."""
        controller = LQRController()

        # Positive lateral error should give steering response
        steering = controller.compute(
            lateral_error=1.0,
            heading_error=0.1,
            speed=5.0,
            dt=0.1
        )

        # Should produce some steering output
        self.assertIsInstance(steering, float)
        # Check that it's within valid range
        self.assertGreaterEqual(steering, -np.pi / 4)
        self.assertLessEqual(steering, np.pi / 4)


if __name__ == "__main__":
    unittest.main()
