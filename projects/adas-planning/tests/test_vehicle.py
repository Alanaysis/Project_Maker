"""
Tests for Vehicle Model Module.
"""

import unittest
import numpy as np
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.vehicle import (
    VehicleParameters, PointMassModel, BicycleModel,
    KinematicModel, DynamicBicycleModel, create_vehicle_model
)


class TestVehicleParameters(unittest.TestCase):
    """Tests for VehicleParameters."""

    def test_default_values(self):
        """Test default parameter values."""
        params = VehicleParameters()

        self.assertEqual(params.wheelbase, 2.5)
        self.assertEqual(params.max_steer, np.pi / 4)
        self.assertEqual(params.max_speed, 30.0)

    def test_custom_values(self):
        """Test custom parameter values."""
        params = VehicleParameters(wheelbase=3.0, max_speed=20.0)

        self.assertEqual(params.wheelbase, 3.0)
        self.assertEqual(params.max_speed, 20.0)


class TestPointMassModel(unittest.TestCase):
    """Tests for PointMassModel."""

    def test_initialization(self):
        """Test model initialization."""
        model = PointMassModel()

        self.assertEqual(model.get_state_dim(), 4)
        self.assertEqual(model.get_control_dim(), 2)

    def test_update_position(self):
        """Test position update."""
        model = PointMassModel()
        state = np.array([0.0, 0.0, 5.0, 0.0])  # x, y, v, theta
        control = np.array([0.0, 0.0])  # accel, steering_rate

        new_state = model.update(state, control, 0.1)

        # Should move forward
        self.assertGreater(new_state[0], 0.0)

    def test_speed_limit(self):
        """Test speed limiting."""
        model = PointMassModel()
        state = np.array([0.0, 0.0, 29.0, 0.0])
        control = np.array([10.0, 0.0])  # Large acceleration

        new_state = model.update(state, control, 1.0)

        # Speed should be limited
        self.assertLessEqual(new_state[2], model.params.max_speed)


class TestBicycleModel(unittest.TestCase):
    """Tests for BicycleModel."""

    def test_initialization(self):
        """Test model initialization."""
        model = BicycleModel()

        self.assertEqual(model.get_state_dim(), 4)
        self.assertEqual(model.get_control_dim(), 2)

    def test_straight_line(self):
        """Test straight line motion."""
        model = BicycleModel()
        state = np.array([0.0, 0.0, 0.0, 5.0])  # x, y, theta, v
        control = np.array([0.0, 0.0])  # accel, steering

        new_state = model.update(state, control, 0.1)

        # Should move forward in x direction
        self.assertGreater(new_state[0], 0.0)
        # y should stay near zero
        self.assertLess(abs(new_state[1]), 0.01)

    def test_turning(self):
        """Test turning behavior."""
        model = BicycleModel()
        state = np.array([0.0, 0.0, 0.0, 5.0])
        control = np.array([0.0, 0.5])  # Positive steering

        new_state = model.update(state, control, 0.1)

        # Heading should change
        self.assertGreater(new_state[2], 0.0)

    def test_predict_trajectory(self):
        """Test trajectory prediction."""
        model = BicycleModel()
        state = np.array([0.0, 0.0, 0.0, 5.0])
        controls = np.array([
            [0.0, 0.1],
            [0.0, 0.1],
            [0.0, 0.1],
        ])

        trajectory = model.predict_trajectory(state, controls, 0.1)

        self.assertEqual(trajectory.shape, (4, 4))  # 4 states (initial + 3 steps)
        self.assertEqual(trajectory[0, 0], 0.0)  # Initial x


class TestKinematicModel(unittest.TestCase):
    """Tests for KinematicModel."""

    def test_initialization(self):
        """Test model initialization."""
        model = KinematicModel()

        self.assertEqual(model.get_state_dim(), 5)
        self.assertEqual(model.get_control_dim(), 2)

    def test_update(self):
        """Test state update."""
        model = KinematicModel()
        state = np.array([0.0, 0.0, 0.0, 5.0, 0.0])  # x, y, theta, v, delta
        control = np.array([0.0, 0.1])  # accel, steering_rate

        new_state = model.update(state, control, 0.1)

        self.assertEqual(len(new_state), 5)
        self.assertGreater(new_state[0], 0.0)  # Should move


class TestDynamicBicycleModel(unittest.TestCase):
    """Tests for DynamicBicycleModel."""

    def test_initialization(self):
        """Test model initialization."""
        model = DynamicBicycleModel()

        self.assertEqual(model.get_state_dim(), 6)
        self.assertEqual(model.get_control_dim(), 2)

    def test_update(self):
        """Test state update."""
        model = DynamicBicycleModel()
        state = np.array([0.0, 0.0, 0.0, 5.0, 0.0, 0.0])
        control = np.array([0.0, 0.0])

        new_state = model.update(state, control, 0.1)

        self.assertEqual(len(new_state), 6)


class TestCreateVehicleModel(unittest.TestCase):
    """Tests for factory function."""

    def test_create_bicycle(self):
        """Test creating bicycle model."""
        model = create_vehicle_model("bicycle")

        self.assertIsInstance(model, BicycleModel)

    def test_create_pointmass(self):
        """Test creating point mass model."""
        model = create_vehicle_model("pointmass")

        self.assertIsInstance(model, PointMassModel)

    def test_create_kinematic(self):
        """Test creating kinematic model."""
        model = create_vehicle_model("kinematic")

        self.assertIsInstance(model, KinematicModel)

    def test_create_dynamic(self):
        """Test creating dynamic model."""
        model = create_vehicle_model("dynamic")

        self.assertIsInstance(model, DynamicBicycleModel)

    def test_invalid_type(self):
        """Test invalid model type."""
        with self.assertRaises(ValueError):
            create_vehicle_model("invalid")


if __name__ == "__main__":
    unittest.main()
