"""Physics constraints for connecting bodies."""

from abc import ABC, abstractmethod
from .vector import Vector2D
from .rigidbody import RigidBody


class Constraint(ABC):
    """Base constraint class."""

    @abstractmethod
    def solve(self, dt: float) -> None:
        """Solve the constraint."""
        pass


class DistanceConstraint(Constraint):
    """Maintains a fixed distance between two bodies."""

    def __init__(
        self,
        body_a: RigidBody,
        body_b: RigidBody,
        distance: float = None,
        stiffness: float = 1.0,
    ):
        self.body_a = body_a
        self.body_b = body_b
        self.stiffness = stiffness

        # If distance not specified, use current distance
        if distance is None:
            self.distance = body_a.position.distance_to(body_b.position)
        else:
            self.distance = distance

    def solve(self, dt: float) -> None:
        """Solve distance constraint."""
        diff = self.body_b.position - self.body_a.position
        current_distance = diff.length()

        if current_distance == 0:
            return

        # Calculate correction
        error = current_distance - self.distance
        correction = diff.normalized() * error * self.stiffness

        total_inverse_mass = self.body_a.inverse_mass + self.body_b.inverse_mass
        if total_inverse_mass == 0:
            return

        # Apply positional correction
        correction_a = correction * (self.body_a.inverse_mass / total_inverse_mass)
        correction_b = correction * (self.body_b.inverse_mass / total_inverse_mass)

        self.body_a.position += correction_a
        self.body_b.position -= correction_b

        # Also correct velocities to prevent drift
        relative_velocity = self.body_b.velocity - self.body_a.velocity
        velocity_along_constraint = relative_velocity.dot(diff.normalized())

        if abs(velocity_along_constraint) > 0:
            velocity_correction = diff.normalized() * velocity_along_constraint * self.stiffness
            self.body_a.velocity += velocity_correction * (self.body_a.inverse_mass / total_inverse_mass)
            self.body_b.velocity -= velocity_correction * (self.body_b.inverse_mass / total_inverse_mass)


class SpringConstraint(Constraint):
    """Spring force between two bodies."""

    def __init__(
        self,
        body_a: RigidBody,
        body_b: RigidBody,
        rest_length: float = None,
        stiffness: float = 50.0,
        damping: float = 5.0,
    ):
        self.body_a = body_a
        self.body_b = body_b
        self.stiffness = stiffness
        self.damping = damping

        # If rest length not specified, use current distance
        if rest_length is None:
            self.rest_length = body_a.position.distance_to(body_b.position)
        else:
            self.rest_length = rest_length

    def solve(self, dt: float) -> None:
        """Apply spring force between bodies."""
        diff = self.body_b.position - self.body_a.position
        current_length = diff.length()

        if current_length == 0:
            return

        direction = diff.normalized()

        # Spring force (Hooke's law)
        displacement = current_length - self.rest_length
        spring_force = direction * (displacement * self.stiffness)

        # Damping force
        relative_velocity = self.body_b.velocity - self.body_a.velocity
        damping_force = direction * (relative_velocity.dot(direction) * self.damping)

        # Total force
        total_force = spring_force + damping_force

        # Apply forces
        self.body_a.apply_force(total_force)
        self.body_b.apply_force(-total_force)


class PinConstraint(Constraint):
    """Pins a body to a fixed world position."""

    def __init__(self, body: RigidBody, anchor: Vector2D, stiffness: float = 1.0):
        self.body = body
        self.anchor = anchor
        self.stiffness = stiffness

    def solve(self, dt: float) -> None:
        """Pin body to anchor position."""
        if self.body.is_static:
            return

        # Move body towards anchor
        correction = (self.anchor - self.body.position) * self.stiffness
        self.body.position += correction

        # Dampen velocity
        self.body.velocity *= 0.9


class AngleConstraint(Constraint):
    """Maintains angle between three bodies."""

    def __init__(
        self,
        body_a: RigidBody,
        pivot: RigidBody,
        body_b: RigidBody,
        angle: float = None,
        stiffness: float = 1.0,
    ):
        self.body_a = body_a
        self.pivot = pivot
        self.body_b = body_b
        self.stiffness = stiffness

        # If angle not specified, use current angle
        if angle is None:
            self.angle = self._calculate_angle()
        else:
            self.angle = angle

    def _calculate_angle(self) -> float:
        """Calculate current angle between bodies."""
        import math
        a = self.body_a.position - self.pivot.position
        b = self.body_b.position - self.pivot.position
        return math.atan2(a.cross(b), a.dot(b))

    def solve(self, dt: float) -> None:
        """Solve angle constraint."""
        import math
        current_angle = self._calculate_angle()
        error = current_angle - self.angle

        if abs(error) < 1e-6:
            return

        # Simple angular correction
        correction = error * self.stiffness * 0.5

        # Apply rotation correction to both bodies
        if not self.body_a.is_static:
            self.body_a.angular_velocity -= correction
        if not self.body_b.is_static:
            self.body_b.angular_velocity += correction
