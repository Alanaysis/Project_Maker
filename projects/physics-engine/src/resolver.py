"""Collision response and resolution."""

from .vector import Vector2D
from .collision import CollisionInfo


class CollisionResolver:
    """Handles collision response between bodies."""

    @staticmethod
    def resolve(collision: CollisionInfo) -> None:
        """Resolve a collision between two bodies."""
        body_a = collision.body_a
        body_b = collision.body_b
        normal = collision.normal

        # Calculate relative velocity
        relative_velocity = body_b.velocity - body_a.velocity
        velocity_along_normal = relative_velocity.dot(normal)

        # Don't resolve if bodies are separating
        if velocity_along_normal > 0:
            return

        # Calculate restitution (bounciness)
        restitution = min(body_a.restitution, body_b.restitution)

        # Calculate impulse scalar
        impulse_scalar = -(1 + restitution) * velocity_along_normal
        impulse_scalar /= body_a.inverse_mass + body_b.inverse_mass

        # Apply impulse
        impulse = normal * impulse_scalar
        body_a.velocity -= impulse * body_a.inverse_mass
        body_b.velocity += impulse * body_b.inverse_mass

        # Apply friction
        CollisionResolver._apply_friction(collision, impulse_scalar)

        # Separate overlapping bodies
        CollisionResolver._positional_correction(collision)

    @staticmethod
    def _apply_friction(collision: CollisionInfo, impulse_scalar: float) -> None:
        """Apply friction impulse."""
        body_a = collision.body_a
        body_b = collision.body_b
        normal = collision.normal

        # Calculate relative velocity
        relative_velocity = body_b.velocity - body_a.velocity

        # Calculate tangent vector
        tangent = relative_velocity - normal * relative_velocity.dot(normal)
        tangent_length = tangent.length()
        if tangent_length < 1e-6:
            return
        tangent = tangent / tangent_length

        # Calculate friction impulse magnitude
        friction = (body_a.friction + body_b.friction) / 2
        friction_impulse = -relative_velocity.dot(tangent)
        friction_impulse /= body_a.inverse_mass + body_b.inverse_mass

        # Coulomb's law: friction cannot exceed normal impulse
        if abs(friction_impulse) < impulse_scalar * friction:
            friction_vector = tangent * friction_impulse
        else:
            friction_vector = tangent * (-impulse_scalar * friction)

        # Apply friction impulse
        body_a.velocity -= friction_vector * body_a.inverse_mass
        body_b.velocity += friction_vector * body_b.inverse_mass

    @staticmethod
    def _positional_correction(collision: CollisionInfo) -> None:
        """Separate overlapping bodies."""
        body_a = collision.body_a
        body_b = collision.body_b

        total_inverse_mass = body_a.inverse_mass + body_b.inverse_mass
        if total_inverse_mass == 0:
            return

        # Correction percentage (higher = more aggressive)
        correction_percentage = 0.8
        # Slop allowance to prevent jittering
        slop = 0.01

        correction = collision.normal * (
            max(collision.penetration - slop, 0) /
            total_inverse_mass *
            correction_percentage
        )

        body_a.position -= correction * body_a.inverse_mass
        body_b.position += correction * body_b.inverse_mass
