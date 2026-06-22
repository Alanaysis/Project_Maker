"""
Trajectory Module
=================

This module provides trajectory generation and management:
- Trajectory: Represents a planned trajectory
- TrajectoryGenerator: Generates smooth trajectories from waypoints
"""

import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass, field

# Try to import scipy, fallback to numpy-based implementation
try:
    import scipy.interpolate as interp
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


@dataclass
class TrajectoryPoint:
    """Single point in a trajectory."""
    x: float
    y: float
    heading: float = 0.0
    curvature: float = 0.0
    velocity: float = 0.0
    acceleration: float = 0.0
    time: float = 0.0

    def to_numpy(self) -> np.ndarray:
        """Convert to numpy array."""
        return np.array([self.x, self.y, self.heading])

    @classmethod
    def from_numpy(cls, arr: np.ndarray, **kwargs) -> 'TrajectoryPoint':
        """Create from numpy array."""
        return cls(x=arr[0], y=arr[1], heading=arr[2] if len(arr) > 2 else 0.0, **kwargs)


class Trajectory:
    """
    Represents a planned trajectory.

    Contains ordered sequence of trajectory points with
    associated properties like velocity and curvature.
    """

    def __init__(self, points: List[TrajectoryPoint] = None):
        """
        Initialize trajectory.

        Args:
            points: List of trajectory points
        """
        self.points = points or []
        self._length = None
        self._curvatures = None

    @classmethod
    def from_waypoints(cls, waypoints: List[Tuple[float, float]],
                       velocities: Optional[List[float]] = None) -> 'Trajectory':
        """
        Create trajectory from waypoints.

        Args:
            waypoints: List of (x, y) positions
            velocities: Optional list of velocities at each point

        Returns:
            Trajectory object
        """
        points = []
        for i, (x, y) in enumerate(waypoints):
            # Calculate heading from direction to next point
            if i < len(waypoints) - 1:
                dx = waypoints[i + 1][0] - x
                dy = waypoints[i + 1][1] - y
                heading = np.arctan2(dy, dx)
            elif i > 0:
                dx = x - waypoints[i - 1][0]
                dy = y - waypoints[i - 1][1]
                heading = np.arctan2(dy, dx)
            else:
                heading = 0.0

            vel = velocities[i] if velocities else 0.0

            points.append(TrajectoryPoint(
                x=x, y=y, heading=heading, velocity=vel
            ))

        return cls(points)

    @classmethod
    def from_numpy(cls, array: np.ndarray) -> 'Trajectory':
        """
        Create trajectory from numpy array.

        Args:
            array: Nx2 or Nx3 array of positions

        Returns:
            Trajectory object
        """
        points = []
        for i in range(len(array)):
            x, y = array[i, 0], array[i, 1]
            if array.shape[1] > 2:
                heading = array[i, 2]
            else:
                heading = 0.0
            points.append(TrajectoryPoint(x=x, y=y, heading=heading))
        return cls(points)

    def add_point(self, point: TrajectoryPoint) -> None:
        """Add a point to the trajectory."""
        self.points.append(point)
        self._length = None
        self._curvatures = None

    def get_point(self, index: int) -> TrajectoryPoint:
        """Get point at index."""
        return self.points[index]

    def __len__(self) -> int:
        """Get number of points."""
        return len(self.points)

    def __getitem__(self, index: int) -> TrajectoryPoint:
        """Get point at index."""
        return self.points[index]

    def to_numpy(self) -> np.ndarray:
        """Convert trajectory to numpy array."""
        return np.array([[p.x, p.y] for p in self.points])

    def get_positions(self) -> np.ndarray:
        """Get all positions as numpy array."""
        return np.array([[p.x, p.y] for p in self.points])

    def get_headings(self) -> np.ndarray:
        """Get all headings as numpy array."""
        return np.array([p.heading for p in self.points])

    def get_velocities(self) -> np.ndarray:
        """Get all velocities as numpy array."""
        return np.array([p.velocity for p in self.points])

    def get_curvatures(self) -> np.ndarray:
        """Get curvatures at each point."""
        if self._curvatures is None:
            self._curvatures = self._compute_curvatures()
        return self._curvatures

    def _compute_curvatures(self) -> np.ndarray:
        """Compute curvatures using finite differences."""
        n = len(self.points)
        curvatures = np.zeros(n)

        for i in range(1, n - 1):
            # Get three consecutive points
            p1 = np.array([self.points[i - 1].x, self.points[i - 1].y])
            p2 = np.array([self.points[i].x, self.points[i].y])
            p3 = np.array([self.points[i + 1].x, self.points[i + 1].y])

            # Compute curvature using cross product formula
            v1 = p2 - p1
            v2 = p3 - p2
            cross = np.cross(v1, v2)
            norm_v1 = np.linalg.norm(v1)
            norm_v2 = np.linalg.norm(v2)

            if norm_v1 > 1e-6 and norm_v2 > 1e-6:
                # Curvature = |v1 x v2| / (|v1| * |v2| * |v2|) * 2
                curvatures[i] = 2 * abs(cross) / (norm_v1 * norm_v2 * (norm_v1 + norm_v2))

        # Fill endpoints
        curvatures[0] = curvatures[1] if n > 1 else 0
        curvatures[-1] = curvatures[-2] if n > 1 else 0

        return curvatures

    def get_length(self) -> float:
        """Get total trajectory length."""
        if self._length is None:
            total = 0.0
            for i in range(len(self.points) - 1):
                dx = self.points[i + 1].x - self.points[i].x
                dy = self.points[i + 1].y - self.points[i].y
                total += np.sqrt(dx * dx + dy * dy)
            self._length = total
        return self._length

    def get_nearest_index(self, x: float, y: float) -> int:
        """Find index of nearest point to given position."""
        min_dist = float('inf')
        nearest_idx = 0
        for i, p in enumerate(self.points):
            dist = (p.x - x) ** 2 + (p.y - y) ** 2
            if dist < min_dist:
                min_dist = dist
                nearest_idx = i
        return nearest_idx

    def get_lookahead_point(self, x: float, y: float,
                            lookahead_dist: float) -> Optional[TrajectoryPoint]:
        """
        Get lookahead point for pure pursuit controller.

        Args:
            x: Current x position
            y: Current y position
            lookahead_dist: Lookahead distance

        Returns:
            Lookahead point or None
        """
        nearest_idx = self.get_nearest_index(x, y)
        cumulative_dist = 0.0

        for i in range(nearest_idx, len(self.points) - 1):
            dx = self.points[i + 1].x - self.points[i].x
            dy = self.points[i + 1].y - self.points[i].y
            cumulative_dist += np.sqrt(dx * dx + dy * dy)

            if cumulative_dist >= lookahead_dist:
                return self.points[i + 1]

        return self.points[-1]


class TrajectoryGenerator:
    """
    Generates smooth trajectories from waypoints.

    Uses cubic spline interpolation to create smooth paths.
    """

    def __init__(self, ds: float = 0.1):
        """
        Initialize trajectory generator.

        Args:
            ds: Distance between trajectory points
        """
        self.ds = ds

    def _cubic_spline_numpy(self, t, x, t_new):
        """Simple cubic spline interpolation using numpy."""
        n = len(t)
        if n < 2:
            return np.ones_like(t_new) * x[0]

        # Natural cubic spline coefficients
        h = np.diff(t)
        alpha = np.zeros(n)
        for i in range(1, n - 1):
            alpha[i] = (3 / h[i] * (x[i + 1] - x[i]) -
                        3 / h[i - 1] * (x[i] - x[i - 1]))

        l = np.ones(n)
        mu = np.zeros(n)
        z = np.zeros(n)

        for i in range(1, n - 1):
            l[i] = 2 * (t[i + 1] - t[i - 1]) - h[i - 1] * mu[i - 1]
            mu[i] = h[i] / l[i]
            z[i] = (alpha[i] - h[i - 1] * z[i - 1]) / l[i]

        c = np.zeros(n)
        b = np.zeros(n - 1)
        d = np.zeros(n - 1)

        for j in range(n - 2, -1, -1):
            c[j] = z[j] - mu[j] * c[j + 1]
            b[j] = ((x[j + 1] - x[j]) / h[j] -
                    h[j] * (c[j + 1] + 2 * c[j]) / 3)
            d[j] = (c[j + 1] - c[j]) / (3 * h[j])

        # Interpolate
        result = np.zeros_like(t_new)
        for i, s in enumerate(t_new):
            # Find interval
            idx = np.searchsorted(t, s, side='right') - 1
            idx = max(0, min(idx, n - 2))

            ds = s - t[idx]
            result[i] = x[idx] + b[idx] * ds + c[idx] * ds ** 2 + d[idx] * ds ** 3

        return result

    def _cubic_spline_derivative_numpy(self, t, x, t_new):
        """Compute derivative of cubic spline."""
        n = len(t)
        if n < 2:
            return np.zeros_like(t_new)

        h = np.diff(t)
        alpha = np.zeros(n)
        for i in range(1, n - 1):
            alpha[i] = (3 / h[i] * (x[i + 1] - x[i]) -
                        3 / h[i - 1] * (x[i] - x[i - 1]))

        l = np.ones(n)
        mu = np.zeros(n)
        z = np.zeros(n)

        for i in range(1, n - 1):
            l[i] = 2 * (t[i + 1] - t[i - 1]) - h[i - 1] * mu[i - 1]
            mu[i] = h[i] / l[i]
            z[i] = (alpha[i] - h[i - 1] * z[i - 1]) / l[i]

        c = np.zeros(n)
        b = np.zeros(n - 1)

        for j in range(n - 2, -1, -1):
            c[j] = z[j] - mu[j] * c[j + 1]
            b[j] = ((x[j + 1] - x[j]) / h[j] -
                    h[j] * (c[j + 1] + 2 * c[j]) / 3)

        # Compute derivative
        result = np.zeros_like(t_new)
        for i, s in enumerate(t_new):
            idx = np.searchsorted(t, s, side='right') - 1
            idx = max(0, min(idx, n - 2))

            ds = s - t[idx]
            result[i] = b[idx] + 2 * c[idx] * ds

        return result

    def generate(self, waypoints: List[Tuple[float, float]],
                 target_velocity: float = 10.0) -> Trajectory:
        """
        Generate smooth trajectory from waypoints.

        Args:
            waypoints: List of (x, y) waypoints
            target_velocity: Target velocity along trajectory

        Returns:
            Smooth trajectory
        """
        if len(waypoints) < 2:
            return Trajectory.from_waypoints(waypoints)

        # Convert to numpy array
        waypoints_array = np.array(waypoints)
        x = waypoints_array[:, 0]
        y = waypoints_array[:, 1]

        # Compute cumulative distance along waypoints
        dx = np.diff(x)
        dy = np.diff(y)
        distances = np.sqrt(dx ** 2 + dy ** 2)
        cumulative_dist = np.zeros(len(waypoints))
        cumulative_dist[1:] = np.cumsum(distances)

        # Generate smooth trajectory points
        total_length = cumulative_dist[-1]
        num_points = max(int(total_length / self.ds) + 1, 2)
        s_values = np.linspace(0, total_length, num_points)

        # Use scipy if available, otherwise numpy implementation
        if HAS_SCIPY:
            try:
                tck_x = interp.splrep(cumulative_dist, x, k=min(3, len(waypoints) - 1))
                tck_y = interp.splrep(cumulative_dist, y, k=min(3, len(waypoints) - 1))

                x_vals = np.array([float(interp.splev(s, tck_x)) for s in s_values])
                y_vals = np.array([float(interp.splev(s, tck_y)) for s in s_values])
                dx_ds = np.array([float(interp.splev(s, tck_x, der=1)) for s in s_values])
                dy_ds = np.array([float(interp.splev(s, tck_y, der=1)) for s in s_values])
                ddx_ds = np.array([float(interp.splev(s, tck_x, der=2)) for s in s_values])
                ddy_ds = np.array([float(interp.splev(s, tck_y, der=2)) for s in s_values])
            except Exception:
                # Fallback to numpy implementation
                x_vals = self._cubic_spline_numpy(cumulative_dist, x, s_values)
                y_vals = self._cubic_spline_numpy(cumulative_dist, y, s_values)
                dx_ds = self._cubic_spline_derivative_numpy(cumulative_dist, x, s_values)
                dy_ds = self._cubic_spline_derivative_numpy(cumulative_dist, y, s_values)
                ddx_ds = self._cubic_spline_derivative_numpy(cumulative_dist, dx_ds, s_values)
                ddy_ds = self._cubic_spline_derivative_numpy(cumulative_dist, dy_ds, s_values)
        else:
            # Use numpy implementation
            x_vals = self._cubic_spline_numpy(cumulative_dist, x, s_values)
            y_vals = self._cubic_spline_numpy(cumulative_dist, y, s_values)
            dx_ds = self._cubic_spline_derivative_numpy(cumulative_dist, x, s_values)
            dy_ds = self._cubic_spline_derivative_numpy(cumulative_dist, y, s_values)
            ddx_ds = self._cubic_spline_derivative_numpy(cumulative_dist, dx_ds, s_values)
            ddy_ds = self._cubic_spline_derivative_numpy(cumulative_dist, dy_ds, s_values)

        points = []
        for i in range(len(s_values)):
            # Position
            x_val = float(x_vals[i])
            y_val = float(y_vals[i])

            # Heading from derivative
            heading = np.arctan2(dy_ds[i], dx_ds[i])

            # Curvature from second derivative
            denom = (dx_ds[i] ** 2 + dy_ds[i] ** 2) ** 1.5
            if denom > 1e-10:
                curvature = abs(dx_ds[i] * ddy_ds[i] - dy_ds[i] * ddx_ds[i]) / denom
            else:
                curvature = 0.0

            # Velocity (slow down in curves)
            max_curvature = 0.5
            velocity_factor = max(0.3, 1.0 - curvature / max_curvature)
            velocity = target_velocity * velocity_factor

            points.append(TrajectoryPoint(
                x=x_val,
                y=y_val,
                heading=heading,
                curvature=curvature,
                velocity=velocity
            ))

        return Trajectory(points)

    def generate_with_velocity_profile(self, waypoints: List[Tuple[float, float]],
                                       max_velocity: float = 10.0,
                                       max_acceleration: float = 2.0,
                                       max_curvature: float = 0.5) -> Trajectory:
        """
        Generate trajectory with velocity profile considering dynamics.

        Args:
            waypoints: List of (x, y) waypoints
            max_velocity: Maximum velocity
            max_acceleration: Maximum acceleration
            max_curvature: Maximum curvature

        Returns:
            Trajectory with velocity profile
        """
        # First generate smooth path
        trajectory = self.generate(waypoints, max_velocity)

        # Forward pass - limit by acceleration
        for i in range(1, len(trajectory.points)):
            prev_point = trajectory.points[i - 1]
            curr_point = trajectory.points[i]

            # Distance between points
            dx = curr_point.x - prev_point.x
            dy = curr_point.y - prev_point.y
            ds = np.sqrt(dx ** 2 + dy ** 2)

            # Maximum velocity based on curvature
            if curr_point.curvature > 1e-6:
                v_max_curvature = np.sqrt(max_acceleration / curr_point.curvature)
            else:
                v_max_curvature = max_velocity

            # Limit by acceleration
            v_max_accel = np.sqrt(prev_point.velocity ** 2 + 2 * max_acceleration * ds)

            curr_point.velocity = min(max_velocity, v_max_curvature, v_max_accel)

        # Backward pass - limit by deceleration
        for i in range(len(trajectory.points) - 2, -1, -1):
            curr_point = trajectory.points[i]
            next_point = trajectory.points[i + 1]

            dx = next_point.x - curr_point.x
            dy = next_point.y - curr_point.y
            ds = np.sqrt(dx ** 2 + dy ** 2)

            v_max_decel = np.sqrt(next_point.velocity ** 2 + 2 * max_acceleration * ds)
            curr_point.velocity = min(curr_point.velocity, v_max_decel)

        return trajectory
