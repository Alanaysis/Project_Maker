"""
Vehicle Model Module
====================

This module provides vehicle dynamics models:
- VehicleModel: Basic point-mass model
- BicycleModel: Bicycle dynamics model
- KinematicModel: Kinematic bicycle model
"""

import numpy as np
from typing import Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod


class VehicleModel(ABC):
    """Abstract base class for vehicle models."""

    @abstractmethod
    def update(self, state: np.ndarray, control: np.ndarray, dt: float) -> np.ndarray:
        """Update vehicle state given control input."""
        pass

    @abstractmethod
    def get_state_dim(self) -> int:
        """Get state dimension."""
        pass

    @abstractmethod
    def get_control_dim(self) -> int:
        """Get control dimension."""
        pass


@dataclass
class VehicleParameters:
    """Vehicle physical parameters."""
    wheelbase: float = 2.5  # Distance between front and rear axles (m)
    length: float = 4.5     # Vehicle length (m)
    width: float = 1.8      # Vehicle width (m)
    max_steer: float = np.pi / 4  # Maximum steering angle (rad)
    max_speed: float = 30.0  # Maximum speed (m/s)
    max_accel: float = 3.0   # Maximum acceleration (m/s^2)
    max_decel: float = -5.0  # Maximum deceleration (m/s^2)


class PointMassModel(VehicleModel):
    """
    Point-mass vehicle model.

    Simple model treating vehicle as a point mass.
    State: [x, y, v, theta]
    Control: [acceleration, steering_rate]
    """

    def __init__(self, params: VehicleParameters = None):
        """Initialize point-mass model."""
        self.params = params or VehicleParameters()

    def update(self, state: np.ndarray, control: np.ndarray, dt: float) -> np.ndarray:
        """
        Update vehicle state.

        Args:
            state: Current state [x, y, v, theta]
            control: Control input [acceleration, steering_rate]
            dt: Time step

        Returns:
            New state
        """
        x, y, v, theta = state
        accel, steering_rate = control

        # Update speed
        v_new = v + accel * dt
        v_new = np.clip(v_new, 0, self.params.max_speed)

        # Update heading
        theta_new = theta + steering_rate * dt

        # Update position
        x_new = x + v_new * np.cos(theta_new) * dt
        y_new = y + v_new * np.sin(theta_new) * dt

        return np.array([x_new, y_new, v_new, theta_new])

    def get_state_dim(self) -> int:
        return 4

    def get_control_dim(self) -> int:
        return 2


class BicycleModel(VehicleModel):
    """
    Bicycle dynamics model.

    Commonly used model for autonomous vehicle simulation.
    State: [x, y, theta, v]
    Control: [acceleration, steering_angle]
    """

    def __init__(self, params: VehicleParameters = None):
        """Initialize bicycle model."""
        self.params = params or VehicleParameters()

    def update(self, state: np.ndarray, control: np.ndarray, dt: float) -> np.ndarray:
        """
        Update vehicle state using bicycle model dynamics.

        Args:
            state: Current state [x, y, theta, v]
            control: Control input [acceleration, steering_angle]
            dt: Time step

        Returns:
            New state
        """
        x, y, theta, v = state
        accel, steering = control

        # Limit inputs
        accel = np.clip(accel, self.params.max_decel, self.params.max_accel)
        steering = np.clip(steering, -self.params.max_steer, self.params.max_steer)

        # Update speed
        v_new = v + accel * dt
        v_new = np.clip(v_new, 0, self.params.max_speed)

        # Bicycle model dynamics
        L = self.params.wheelbase

        # Update heading
        if abs(v_new) > 0.01:
            theta_dot = (v_new / L) * np.tan(steering)
        else:
            theta_dot = 0.0
        theta_new = theta + theta_dot * dt

        # Update position
        x_new = x + v_new * np.cos(theta_new) * dt
        y_new = y + v_new * np.sin(theta_new) * dt

        return np.array([x_new, y_new, theta_new, v_new])

    def predict_trajectory(self, state: np.ndarray, controls: np.ndarray,
                           dt: float) -> np.ndarray:
        """
        Predict trajectory given a sequence of controls.

        Args:
            state: Initial state [x, y, theta, v]
            controls: Array of control inputs [[accel, steering], ...]
            dt: Time step

        Returns:
            Array of predicted states
        """
        trajectory = [state.copy()]
        current_state = state.copy()

        for control in controls:
            current_state = self.update(current_state, control, dt)
            trajectory.append(current_state.copy())

        return np.array(trajectory)

    def get_state_dim(self) -> int:
        return 4

    def get_control_dim(self) -> int:
        return 2


class KinematicModel(VehicleModel):
    """
    Kinematic bicycle model.

    Simplified model ignoring tire dynamics.
    State: [x, y, theta, v, delta]
    Control: [acceleration, steering_rate]
    """

    def __init__(self, params: VehicleParameters = None):
        """Initialize kinematic model."""
        self.params = params or VehicleParameters()

    def update(self, state: np.ndarray, control: np.ndarray, dt: float) -> np.ndarray:
        """
        Update vehicle state.

        Args:
            state: Current state [x, y, theta, v, delta]
            control: Control input [acceleration, steering_rate]
            dt: Time step

        Returns:
            New state
        """
        x, y, theta, v, delta = state
        accel, delta_rate = control

        # Limit inputs
        accel = np.clip(accel, self.params.max_decel, self.params.max_accel)
        delta_rate = np.clip(delta_rate, -1.0, 1.0)  # rad/s

        # Update steering angle
        delta_new = delta + delta_rate * dt
        delta_new = np.clip(delta_new, -self.params.max_steer, self.params.max_steer)

        # Update speed
        v_new = v + accel * dt
        v_new = np.clip(v_new, 0, self.params.max_speed)

        # Kinematic bicycle model
        L = self.params.wheelbase
        beta = np.arctan(0.5 * np.tan(delta_new))  # Slip angle

        # Update heading
        theta_dot = (v_new / L) * np.sin(beta) * 2
        theta_new = theta + theta_dot * dt

        # Update position
        x_new = x + v_new * np.cos(theta_new + beta) * dt
        y_new = y + v_new * np.sin(theta_new + beta) * dt

        return np.array([x_new, y_new, theta_new, v_new, delta_new])

    def get_state_dim(self) -> int:
        return 5

    def get_control_dim(self) -> int:
        return 2


class DynamicBicycleModel(VehicleModel):
    """
    Dynamic bicycle model with tire forces.

    More accurate model considering lateral tire dynamics.
    State: [x, y, theta, v_x, v_y, omega]
    Control: [acceleration, steering_angle]
    """

    def __init__(self, params: VehicleParameters = None,
                 Cf: float = 10000.0, Cr: float = 10000.0,
                 mass: float = 1500.0, Iz: float = 2500.0):
        """
        Initialize dynamic bicycle model.

        Args:
            params: Vehicle parameters
            Cf: Front cornering stiffness
            Cr: Rear cornering stiffness
            mass: Vehicle mass
            Iz: Yaw moment of inertia
        """
        self.params = params or VehicleParameters()
        self.Cf = Cf
        self.Cr = Cr
        self.mass = mass
        self.Iz = Iz

    def update(self, state: np.ndarray, control: np.ndarray, dt: float) -> np.ndarray:
        """
        Update vehicle state using dynamic bicycle model.

        Args:
            state: Current state [x, y, theta, v_x, v_y, omega]
            control: Control input [acceleration, steering_angle]
            dt: Time step

        Returns:
            New state
        """
        x, y, theta, vx, vy, omega = state
        accel, steering = control

        # Limit inputs
        accel = np.clip(accel, self.params.max_decel, self.params.max_accel)
        steering = np.clip(steering, -self.params.max_steer, self.params.max_steer)

        # Avoid division by zero
        vx = max(vx, 0.1)

        # Slip angles
        alpha_f = steering - np.arctan2(vy + self.params.wheelbase * omega / 2, vx)
        alpha_r = -np.arctan2(vy - self.params.wheelbase * omega / 2, vx)

        # Lateral forces (linear tire model)
        Fyf = self.Cf * alpha_f
        Fyr = self.Cr * alpha_r

        # State derivatives
        # Position
        x_dot = vx * np.cos(theta) - vy * np.sin(theta)
        y_dot = vx * np.sin(theta) + vy * np.cos(theta)

        # Heading
        theta_dot = omega

        # Longitudinal velocity
        vx_dot = accel - Fyf * np.sin(steering) / self.mass + vy * omega

        # Lateral velocity
        vy_dot = (Fyf * np.cos(steering) + Fyr) / self.mass - vx * omega

        # Yaw rate
        omega_dot = (self.params.wheelbase / 2 * Fyf * np.cos(steering) -
                     self.params.wheelbase / 2 * Fyr) / self.Iz

        # Update state using Euler integration
        x_new = x + x_dot * dt
        y_new = y + y_dot * dt
        theta_new = theta + theta_dot * dt
        vx_new = max(0, vx + vx_dot * dt)
        vy_new = vy + vy_dot * dt
        omega_new = omega + omega_dot * dt

        # Limit speed
        vx_new = np.clip(vx_new, 0, self.params.max_speed)

        return np.array([x_new, y_new, theta_new, vx_new, vy_new, omega_new])

    def get_state_dim(self) -> int:
        return 6

    def get_control_dim(self) -> int:
        return 2


def create_vehicle_model(model_type: str = "bicycle",
                         params: VehicleParameters = None) -> VehicleModel:
    """
    Factory function to create vehicle model.

    Args:
        model_type: Type of model ("pointmass", "bicycle", "kinematic", "dynamic")
        params: Vehicle parameters

    Returns:
        Vehicle model instance
    """
    models = {
        "pointmass": PointMassModel,
        "bicycle": BicycleModel,
        "kinematic": KinematicModel,
        "dynamic": DynamicBicycleModel,
    }

    if model_type not in models:
        raise ValueError(f"Unknown model type: {model_type}. Choose from {list(models.keys())}")

    return models[model_type](params)
