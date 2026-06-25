"""Numerical integrators for physics simulation."""

from abc import ABC, abstractmethod
from .vector import Vector2D
from .rigidbody import RigidBody


class Integrator(ABC):
    """Base integrator class."""

    @abstractmethod
    def integrate(self, body: RigidBody, dt: float) -> None:
        """Integrate body state forward by dt."""
        pass


class EulerIntegrator(Integrator):
    """Semi-implicit Euler integration."""

    def integrate(self, body: RigidBody, dt: float) -> None:
        """Integrate using semi-implicit Euler method.

        This method updates velocity first, then position,
        which provides better stability than explicit Euler.
        """
        if body.is_static:
            return

        # Calculate acceleration from forces
        acceleration = body.force * body.inverse_mass

        # Update velocity from acceleration
        body.velocity += acceleration * dt

        # Apply damping
        body.velocity *= 0.999

        # Update position from velocity
        body.position += body.velocity * dt

        # Update angular velocity
        body.angular_velocity += body.torque * body.inverse_inertia * dt
        body.angular_velocity *= 0.999

        # Update rotation
        body.rotation += body.angular_velocity * dt

        # Clear forces
        body.clear_forces()


class VerletIntegrator(Integrator):
    """Verlet integration for improved stability."""

    def __init__(self):
        self._positions: dict[int, Vector2D] = {}

    def integrate(self, body: RigidBody, dt: float) -> None:
        """Integrate using Verlet method.

        Verlet integration is more stable for constraints
        and provides better energy conservation.
        """
        if body.is_static:
            return

        body_id = id(body)

        # Store previous position if not exists
        if body_id not in self._positions:
            self._positions[body_id] = body.position - body.velocity * dt

        # Calculate acceleration
        acceleration = body.force * body.inverse_mass

        # Verlet integration
        new_position = (
            2 * body.position
            - self._positions[body_id]
            + acceleration * dt * dt
        )

        # Update velocity (approximate)
        body.velocity = (new_position - self._positions[body_id]) / (2 * dt)

        # Apply damping
        body.velocity *= 0.999

        # Store current position and update
        self._positions[body_id] = body.position
        body.position = new_position

        # Update rotation
        body.angular_velocity += body.torque * body.inverse_inertia * dt
        body.angular_velocity *= 0.999
        body.rotation += body.angular_velocity * dt

        # Clear forces
        body.clear_forces()


class RK4Integrator(Integrator):
    """Runge-Kutta 4th order integration for high accuracy."""

    def integrate(self, body: RigidBody, dt: float) -> None:
        """Integrate using RK4 method.

        RK4 provides 4th order accuracy for smooth simulations.
        """
        if body.is_static:
            return

        # Store initial state
        pos0 = body.position
        vel0 = body.velocity

        # k1
        k1_vel = body.force * body.inverse_mass * dt
        k1_pos = vel0 * dt

        # k2
        body.position = pos0 + k1_pos * 0.5
        body.velocity = vel0 + k1_vel * 0.5
        k2_vel = body.force * body.inverse_mass * dt
        k2_pos = body.velocity * dt

        # k3
        body.position = pos0 + k2_pos * 0.5
        body.velocity = vel0 + k2_vel * 0.5
        k3_vel = body.force * body.inverse_mass * dt
        k3_pos = body.velocity * dt

        # k4
        body.position = pos0 + k3_pos
        body.velocity = vel0 + k3_vel
        k4_vel = body.force * body.inverse_mass * dt
        k4_pos = body.velocity * dt

        # Combine results
        body.position = pos0 + (k1_pos + 2 * k2_pos + 2 * k3_pos + k4_pos) / 6
        body.velocity = vel0 + (k1_vel + 2 * k2_vel + 2 * k3_vel + k4_vel) / 6

        # Apply damping
        body.velocity *= 0.999

        # Update rotation
        body.angular_velocity += body.torque * body.inverse_inertia * dt
        body.angular_velocity *= 0.999
        body.rotation += body.angular_velocity * dt

        # Clear forces
        body.clear_forces()
