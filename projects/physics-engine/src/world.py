"""Physics world simulation."""

from .vector import Vector2D
from .rigidbody import RigidBody
from .collider import Collider
from .collision import CollisionDetector, CollisionInfo
from .resolver import CollisionResolver
from .constraint import Constraint
from .integrator import Integrator, EulerIntegrator


class PhysicsWorld:
    """Main physics simulation world."""

    def __init__(self, integrator: Integrator = None):
        self.bodies: list[RigidBody] = []
        self.colliders: dict[int, Collider] = {}  # body_id -> collider
        self.constraints: list[Constraint] = []
        self.gravity = Vector2D(0, 9.81)  # Default gravity
        self.integrator = integrator or EulerIntegrator()
        self.iterations = 10  # Constraint solver iterations

    def add_body(self, body: RigidBody, collider: Collider = None) -> None:
        """Add a rigid body to the world."""
        self.bodies.append(body)
        if collider:
            self.colliders[id(body)] = collider

    def remove_body(self, body: RigidBody) -> None:
        """Remove a rigid body from the world."""
        self.bodies.remove(body)
        body_id = id(body)
        if body_id in self.colliders:
            del self.colliders[body_id]

    def add_constraint(self, constraint: Constraint) -> None:
        """Add a constraint to the world."""
        self.constraints.append(constraint)

    def remove_constraint(self, constraint: Constraint) -> None:
        """Remove a constraint from the world."""
        self.constraints.remove(constraint)

    def step(self, dt: float) -> None:
        """Advance simulation by one time step."""
        # Apply gravity
        self._apply_gravity()

        # Detect collisions
        collisions = self._detect_collisions()

        # Resolve collisions
        self._resolve_collisions(collisions)

        # Solve constraints
        self._solve_constraints(dt)

        # Integrate
        self._integrate(dt)

    def _apply_gravity(self) -> None:
        """Apply gravity to all non-static bodies."""
        for body in self.bodies:
            if not body.is_static:
                body.apply_force(self.gravity * body.mass)

    def _detect_collisions(self) -> list[CollisionInfo]:
        """Detect all collisions between bodies."""
        collisions = []
        n = len(self.bodies)

        for i in range(n):
            for j in range(i + 1, n):
                body_a = self.bodies[i]
                body_b = self.bodies[j]

                # Skip if both are static
                if body_a.is_static and body_b.is_static:
                    continue

                # Get colliders
                collider_a = self.colliders.get(id(body_a))
                collider_b = self.colliders.get(id(body_b))

                if collider_a and collider_b:
                    collision = CollisionDetector.check_collision(collider_a, collider_b)
                    if collision:
                        collisions.append(collision)

        return collisions

    def _resolve_collisions(self, collisions: list[CollisionInfo]) -> None:
        """Resolve all detected collisions."""
        for collision in collisions:
            CollisionResolver.resolve(collision)

    def _solve_constraints(self, dt: float) -> None:
        """Solve all constraints."""
        for _ in range(self.iterations):
            for constraint in self.constraints:
                constraint.solve(dt)

    def _integrate(self, dt: float) -> None:
        """Integrate all bodies forward in time."""
        for body in self.bodies:
            self.integrator.integrate(body, dt)

    def get_body_at(self, point: Vector2D) -> RigidBody | None:
        """Find body at given point."""
        for body in self.bodies:
            collider = self.colliders.get(id(body))
            if collider and collider.contains_point(point):
                return body
        return None

    def clear(self) -> None:
        """Remove all bodies and constraints."""
        self.bodies.clear()
        self.colliders.clear()
        self.constraints.clear()

    def __repr__(self) -> str:
        return f"PhysicsWorld(bodies={len(self.bodies)}, constraints={len(self.constraints)})"
