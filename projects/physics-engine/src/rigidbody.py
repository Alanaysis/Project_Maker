"""Rigid body implementation for physics simulation."""

from .vector import Vector2D


class RigidBody:
    """Rigid body with mass, velocity, and acceleration."""

    def __init__(
        self,
        position: Vector2D = None,
        mass: float = 1.0,
        is_static: bool = False,
    ):
        self.position = position or Vector2D.zero()
        self.velocity = Vector2D.zero()
        self.acceleration = Vector2D.zero()
        self.force = Vector2D.zero()

        self.mass = mass
        self.inverse_mass = 0.0 if is_static or mass == 0 else 1.0 / mass
        self.is_static = is_static

        self.restitution = 0.5  # Bounciness (0 = inelastic, 1 = elastic)
        self.friction = 0.2     # Friction coefficient

        self.rotation = 0.0     # Angle in radians
        self.angular_velocity = 0.0
        self.torque = 0.0

        # Moment of inertia (simplified as scalar for 2D)
        self.inertia = self._calculate_inertia()
        self.inverse_inertia = 0.0 if is_static else 1.0 / self.inertia

    def _calculate_inertia(self) -> float:
        """Calculate moment of inertia (default: solid circle approximation)."""
        # For a circle: I = 0.5 * m * r^2
        # Using radius = 1.0 as default
        return 0.5 * self.mass * 1.0 * 1.0

    def apply_force(self, force: Vector2D) -> None:
        """Apply a force to the body."""
        if not self.is_static:
            self.force += force

    def apply_impulse(self, impulse: Vector2D) -> None:
        """Apply an impulse to the body."""
        if not self.is_static:
            self.velocity += impulse * self.inverse_mass

    def clear_forces(self) -> None:
        """Clear accumulated forces."""
        self.force = Vector2D.zero()
        self.torque = 0.0

    def update(self, dt: float) -> None:
        """Update body state using current forces."""
        if self.is_static:
            return

        # Calculate acceleration from forces
        self.acceleration = self.force * self.inverse_mass

        # Update velocity
        self.velocity += self.acceleration * dt

        # Update position
        self.position += self.velocity * dt

        # Update rotation
        self.rotation += self.angular_velocity * dt

        # Clear forces after update
        self.clear_forces()

    @property
    def kinetic_energy(self) -> float:
        """Calculate kinetic energy."""
        return 0.5 * self.mass * self.velocity.length_squared()

    @property
    def momentum(self) -> Vector2D:
        """Calculate momentum."""
        return self.velocity * self.mass

    def __repr__(self) -> str:
        return (
            f"RigidBody(pos={self.position}, vel={self.velocity}, "
            f"mass={self.mass}, static={self.is_static})"
        )
