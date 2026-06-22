"""
Control Module
==============

This module implements control algorithms for trajectory tracking:
- PIDController: Proportional-Integral-Derivative controller
- MPCController: Model Predictive Controller
- StanleyController: Stanley lateral controller
"""

from typing import List, Tuple, Optional
import numpy as np
from abc import ABC, abstractmethod
from dataclasses import dataclass
from collections import deque


class Controller(ABC):
    """Abstract base class for controllers."""

    @abstractmethod
    def compute(self, error: float, dt: float) -> float:
        """Compute control output given error and time step."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset controller state."""
        pass


@dataclass
class PIDGains:
    """PID controller gains."""
    Kp: float = 1.0
    Ki: float = 0.0
    Kd: float = 0.0


class PIDController(Controller):
    """
    PID (Proportional-Integral-Derivative) Controller.

    The PID controller computes a control output based on:
    - Proportional term: responds to current error
    - Integral term: responds to accumulated error
    - Derivative term: responds to rate of error change

    Output = Kp * error + Ki * integral(error) + Kd * d(error)/dt
    """

    def __init__(self, Kp: float = 1.0, Ki: float = 0.0, Kd: float = 0.0,
                 output_limits: Optional[Tuple[float, float]] = None,
                 integral_limits: Optional[Tuple[float, float]] = None):
        """
        Initialize PID controller.

        Args:
            Kp: Proportional gain
            Ki: Integral gain
            Kd: Derivative gain
            output_limits: (min, max) output limits
            integral_limits: (min, max) integral term limits
        """
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.output_limits = output_limits
        self.integral_limits = integral_limits

        # State variables
        self.integral = 0.0
        self.prev_error = 0.0
        self.prev_time = None
        self.error_history = deque(maxlen=100)

    def compute(self, error: float, dt: float) -> float:
        """
        Compute PID control output.

        Args:
            error: Current error (target - actual)
            dt: Time step since last computation

        Returns:
            Control output
        """
        # Proportional term
        P = self.Kp * error

        # Integral term
        self.integral += error * dt
        if self.integral_limits:
            self.integral = np.clip(self.integral, self.integral_limits[0], self.integral_limits[1])
        I = self.Ki * self.integral

        # Derivative term (with filtering to avoid spikes)
        if dt > 0:
            derivative = (error - self.prev_error) / dt
        else:
            derivative = 0.0
        D = self.Kd * derivative

        # Compute output
        output = P + I + D

        # Apply output limits
        if self.output_limits:
            output = np.clip(output, self.output_limits[0], self.output_limits[1])

        # Update state
        self.prev_error = error
        self.error_history.append(error)

        return output

    def reset(self) -> None:
        """Reset controller state."""
        self.integral = 0.0
        self.prev_error = 0.0
        self.prev_time = None
        self.error_history.clear()


class MPCController(Controller):
    """
    Model Predictive Controller (MPC).

    MPC optimizes control inputs over a prediction horizon by:
    1. Predicting future states using a vehicle model
    2. Minimizing a cost function over the horizon
    3. Applying only the first control input

    This is a simplified implementation for trajectory tracking.
    """

    def __init__(self, horizon: int = 10, dt: float = 0.1,
                 Q: np.ndarray = None, R: np.ndarray = None,
                 Rd: np.ndarray = None, wheelbase: float = 2.0):
        """
        Initialize MPC controller.

        Args:
            horizon: Prediction horizon length
            dt: Time step
            Q: State cost matrix (penalizes tracking error)
            R: Control cost matrix (penalizes control effort)
            Rd: Control change cost matrix (penalizes jerky control)
            wheelbase: Vehicle wheelbase
        """
        self.horizon = horizon
        self.dt = dt
        self.wheelbase = wheelbase

        # Cost matrices
        self.Q = Q if Q is not None else np.diag([1.0, 1.0, 0.5])
        self.R = R if R is not None else np.array([[0.01]])
        self.Rd = Rd if Rd is not None else np.array([[0.1]])

        # Previous control inputs for smoothness
        self.prev_steering = 0.0

    def compute(self, state: np.ndarray, reference_trajectory: List[np.ndarray],
                current_speed: float) -> float:
        """
        Compute MPC control output.

        Args:
            state: Current vehicle state [x, y, theta]
            reference_trajectory: List of reference states
            current_speed: Current vehicle speed

        Returns:
            Optimal steering angle
        """
        if len(reference_trajectory) < self.horizon:
            # Pad trajectory with last point
            while len(reference_trajectory) < self.horizon:
                reference_trajectory.append(reference_trajectory[-1])

        # Simple gradient descent optimization
        # Initialize steering sequence
        steering_seq = np.zeros(self.horizon)

        # Optimization loop
        for _ in range(10):  # Number of iterations
            # Compute gradient numerically
            grad = np.zeros(self.horizon)
            cost_current = self._compute_cost(state, steering_seq, reference_trajectory, current_speed)

            for i in range(self.horizon):
                steering_plus = steering_seq.copy()
                steering_plus[i] += 0.01
                cost_plus = self._compute_cost(state, steering_plus, reference_trajectory, current_speed)
                grad[i] = (cost_plus - cost_current) / 0.01

            # Update steering sequence
            steering_seq -= 0.1 * grad

            # Apply limits
            steering_seq = np.clip(steering_seq, -np.pi / 4, np.pi / 4)

        # Return first control input
        optimal_steering = steering_seq[0]
        self.prev_steering = optimal_steering

        return optimal_steering

    def _compute_cost(self, state: np.ndarray, steering_seq: np.ndarray,
                      reference: List[np.ndarray], speed: float) -> float:
        """Compute total cost for a steering sequence."""
        cost = 0.0
        current_state = state.copy()

        for t in range(self.horizon):
            # Predict next state using bicycle model
            theta = current_state[2]
            v = speed

            # State update
            dx = v * np.cos(theta) * self.dt
            dy = v * np.sin(theta) * self.dt
            dtheta = (v / self.wheelbase) * np.tan(steering_seq[t]) * self.dt

            current_state[0] += dx
            current_state[1] += dy
            current_state[2] += dtheta

            # Tracking error cost
            ref = reference[t]
            error = current_state - ref
            cost += error.T @ self.Q @ error

            # Control effort cost
            cost += steering_seq[t] * self.R[0, 0] * steering_seq[t]

            # Control change cost (smoothness)
            if t > 0:
                delta_steer = steering_seq[t] - steering_seq[t - 1]
                cost += delta_steer * self.Rd[0, 0] * delta_steer

        return cost

    def reset(self) -> None:
        """Reset controller state."""
        self.prev_steering = 0.0


class StanleyController:
    """
    Stanley Lateral Controller.

    The Stanley controller is commonly used in autonomous vehicles
    for lateral (steering) control. It combines:
    - Heading error correction
    - Cross-track error correction
    """

    def __init__(self, k: float = 1.0, wheelbase: float = 2.0):
        """
        Initialize Stanley controller.

        Args:
            k: Gain parameter
            wheelbase: Vehicle wheelbase
        """
        self.k = k
        self.wheelbase = wheelbase

    def compute_steering(self, current_pos: np.ndarray, current_heading: float,
                         path: List[np.ndarray], speed: float) -> float:
        """
        Compute steering angle using Stanley controller.

        Args:
            current_pos: Current position [x, y]
            current_heading: Current heading angle (radians)
            path: List of path points
            speed: Current speed

        Returns:
            Steering angle (radians)
        """
        if len(path) < 2:
            return 0.0

        # Find nearest point on path
        min_dist = float('inf')
        nearest_idx = 0
        for i, point in enumerate(path):
            dist = np.linalg.norm(current_pos - point)
            if dist < min_dist:
                min_dist = dist
                nearest_idx = i

        # Get path heading at nearest point
        if nearest_idx < len(path) - 1:
            path_dir = path[nearest_idx + 1] - path[nearest_idx]
        else:
            path_dir = path[nearest_idx] - path[nearest_idx - 1]

        path_heading = np.arctan2(path_dir[1], path_dir[0])

        # Compute heading error
        heading_error = path_heading - current_heading
        heading_error = np.arctan2(np.sin(heading_error), np.cos(heading_error))

        # Compute cross-track error
        # Vector from nearest point to current position
        to_vehicle = current_pos - path[nearest_idx]
        # Cross product sign determines which side of path
        cross = np.cross(path_dir, to_vehicle)
        cross_track_error = np.sign(cross) * min_dist

        # Stanley control law
        if abs(speed) < 0.1:
            speed = 0.1  # Avoid division by zero

        steering = heading_error + np.arctan2(self.k * cross_track_error, speed)

        # Limit steering angle
        steering = np.clip(steering, -np.pi / 4, np.pi / 4)

        return steering

    def compute_steering_angle(self, current_pos: np.ndarray, current_heading: float,
                               path_points: List[np.ndarray], speed: float) -> float:
        """
        Compute steering angle for trajectory tracking.

        Args:
            current_pos: Current position [x, y]
            current_heading: Current heading angle (radians)
            path_points: List of path points as numpy arrays
            speed: Current speed

        Returns:
            Steering angle (radians)
        """
        return self.compute_steering(current_pos, current_heading, path_points, speed)


class LQRController:
    """
    Linear Quadratic Regulator (LQR) Controller.

    LQR is an optimal controller that minimizes a quadratic cost function.
    This implementation is for lateral control of a bicycle model.
    """

    def __init__(self, Q: np.ndarray = None, R: np.ndarray = None,
                 wheelbase: float = 2.0):
        """
        Initialize LQR controller.

        Args:
            Q: State cost matrix
            R: Control cost matrix
            wheelbase: Vehicle wheelbase
        """
        self.Q = Q if Q is not None else np.diag([1.0, 10.0])
        self.R = R if R is not None else np.array([[1.0]])
        self.wheelbase = wheelbase

    def compute(self, lateral_error: float, heading_error: float,
                speed: float, dt: float) -> float:
        """
        Compute LQR control output.

        Args:
            lateral_error: Cross-track error
            heading_error: Heading error
            speed: Current speed
            dt: Time step

        Returns:
            Steering angle
        """
        # State: [lateral_error, heading_error]
        x = np.array([lateral_error, heading_error])

        # Linearized bicycle model matrices
        # dx = Ax + Bu
        A = np.array([
            [0, speed],
            [0, 0]
        ])
        B = np.array([
            [0],
            [speed / self.wheelbase]
        ])

        # Solve discrete-time algebraic Riccati equation
        P = self._solve_dare(A, B, self.Q, self.R, dt)

        # Compute optimal gain: K = (R + B'PB)^(-1) B'PA
        K = np.linalg.inv(self.R + B.T @ P @ B) @ B.T @ P @ A

        # Compute control
        u = -K @ x

        # Apply limits
        steering = np.clip(u[0], -np.pi / 4, np.pi / 4)

        return steering

    def _solve_dare(self, A: np.ndarray, B: np.ndarray,
                    Q: np.ndarray, R: np.ndarray, dt: float,
                    max_iter: int = 100, tol: float = 1e-6) -> np.ndarray:
        """Solve Discrete Algebraic Riccati Equation."""
        # Discretize
        Ad = np.eye(2) + A * dt
        Bd = B * dt

        P = Q.copy()
        for _ in range(max_iter):
            P_new = Q + Ad.T @ P @ Ad - Ad.T @ P @ Bd @ np.linalg.inv(R + Bd.T @ P @ Bd) @ Bd.T @ P @ Ad
            if np.max(np.abs(P_new - P)) < tol:
                break
            P = P_new

        return P
