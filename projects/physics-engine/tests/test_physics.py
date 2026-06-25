"""Tests for physics engine components."""

import pytest
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src import (
    Vector2D, RigidBody, CircleCollider, AABBCollider,
    CollisionDetector, CollisionResolver, PhysicsWorld,
    EulerIntegrator, VerletIntegrator, SpringConstraint, DistanceConstraint
)


class TestRigidBody:
    """Test RigidBody functionality."""

    def test_creation(self):
        body = RigidBody(Vector2D(10, 20), mass=2.0)
        assert body.position.x == 10
        assert body.position.y == 20
        assert body.mass == 2.0
        assert body.inverse_mass == 0.5

    def test_static_body(self):
        body = RigidBody(Vector2D(0, 0), is_static=True)
        assert body.is_static
        assert body.inverse_mass == 0

    def test_apply_force(self):
        body = RigidBody(Vector2D(0, 0), mass=2.0)
        body.apply_force(Vector2D(10, 0))
        assert body.force.x == 10
        assert body.force.y == 0

    def test_apply_impulse(self):
        body = RigidBody(Vector2D(0, 0), mass=2.0)
        body.apply_impulse(Vector2D(10, 0))
        assert body.velocity.x == 5.0  # impulse / mass

    def test_clear_forces(self):
        body = RigidBody(Vector2D(0, 0))
        body.apply_force(Vector2D(10, 10))
        body.clear_forces()
        assert body.force.x == 0
        assert body.force.y == 0

    def test_kinetic_energy(self):
        body = RigidBody(Vector2D(0, 0), mass=2.0)
        body.velocity = Vector2D(3, 4)
        assert body.kinetic_energy == 25.0  # 0.5 * m * v^2 = 0.5 * 2 * 25

    def test_momentum(self):
        body = RigidBody(Vector2D(0, 0), mass=3.0)
        body.velocity = Vector2D(2, 4)
        p = body.momentum
        assert p.x == 6.0
        assert p.y == 12.0


class TestColliders:
    """Test collider functionality."""

    def test_circle_collider(self):
        body = RigidBody(Vector2D(10, 20))
        collider = CircleCollider(body, radius=5.0)

        assert collider.radius == 5.0

        # Test AABB
        min_point, max_point = collider.get_aabb()
        assert min_point.x == 5
        assert min_point.y == 15
        assert max_point.x == 15
        assert max_point.y == 25

    def test_circle_contains_point(self):
        body = RigidBody(Vector2D(0, 0))
        collider = CircleCollider(body, radius=5.0)

        assert collider.contains_point(Vector2D(3, 0))
        assert not collider.contains_point(Vector2D(6, 0))

    def test_aabb_collider(self):
        body = RigidBody(Vector2D(10, 20))
        collider = AABBCollider(body, width=6, height=4)

        assert collider.width == 6
        assert collider.height == 4

        # Test AABB
        min_point, max_point = collider.get_aabb()
        assert min_point.x == 7
        assert min_point.y == 18
        assert max_point.x == 13
        assert max_point.y == 22

    def test_aabb_contains_point(self):
        body = RigidBody(Vector2D(0, 0))
        collider = AABBCollider(body, width=4, height=4)

        assert collider.contains_point(Vector2D(1, 1))
        assert not collider.contains_point(Vector2D(3, 3))


class TestCollisionDetection:
    """Test collision detection."""

    def test_circle_vs_circle_collision(self):
        body_a = RigidBody(Vector2D(0, 0))
        body_b = RigidBody(Vector2D(3, 0))
        collider_a = CircleCollider(body_a, radius=2.0)
        collider_b = CircleCollider(body_b, radius=2.0)

        result = CollisionDetector.circle_vs_circle(collider_a, collider_b)
        assert result is not None
        assert result.penetration == 1.0

    def test_circle_vs_circle_no_collision(self):
        body_a = RigidBody(Vector2D(0, 0))
        body_b = RigidBody(Vector2D(10, 0))
        collider_a = CircleCollider(body_a, radius=2.0)
        collider_b = CircleCollider(body_b, radius=2.0)

        result = CollisionDetector.circle_vs_circle(collider_a, collider_b)
        assert result is None

    def test_aabb_vs_aabb_collision(self):
        body_a = RigidBody(Vector2D(0, 0))
        body_b = RigidBody(Vector2D(3, 0))
        collider_a = AABBCollider(body_a, width=4, height=4)
        collider_b = AABBCollider(body_b, width=4, height=4)

        result = CollisionDetector.aabb_vs_aabb(collider_a, collider_b)
        assert result is not None
        assert result.penetration == 1.0

    def test_aabb_vs_aabb_no_collision(self):
        body_a = RigidBody(Vector2D(0, 0))
        body_b = RigidBody(Vector2D(10, 0))
        collider_a = AABBCollider(body_a, width=4, height=4)
        collider_b = AABBCollider(body_b, width=4, height=4)

        result = CollisionDetector.aabb_vs_aabb(collider_a, collider_b)
        assert result is None

    def test_circle_vs_aabb_collision(self):
        body_circle = RigidBody(Vector2D(0, 0))
        body_aabb = RigidBody(Vector2D(3, 0))
        circle = CircleCollider(body_circle, radius=2.0)
        aabb = AABBCollider(body_aabb, width=4, height=4)

        result = CollisionDetector.circle_vs_aabb(circle, aabb)
        assert result is not None

    def test_circle_vs_aabb_no_collision(self):
        body_circle = RigidBody(Vector2D(0, 0))
        body_aabb = RigidBody(Vector2D(10, 0))
        circle = CircleCollider(body_circle, radius=2.0)
        aabb = AABBCollider(body_aabb, width=4, height=4)

        result = CollisionDetector.circle_vs_aabb(circle, aabb)
        assert result is None


class TestCollisionResolution:
    """Test collision resolution."""

    def test_elastic_collision(self):
        body_a = RigidBody(Vector2D(0, 0), mass=1.0)
        body_b = RigidBody(Vector2D(2, 0), mass=1.0)
        body_a.velocity = Vector2D(5, 0)
        body_b.velocity = Vector2D(-3, 0)

        body_a.restitution = 1.0
        body_b.restitution = 1.0

        collision = CollisionDetector.circle_vs_circle(
            CircleCollider(body_a, 1.5),
            CircleCollider(body_b, 1.5)
        )

        if collision:
            CollisionResolver.resolve(collision)

        # Velocities should be approximately swapped in elastic collision
        assert body_a.velocity.x < 0
        assert body_b.velocity.x > 0

    def test_inelastic_collision(self):
        body_a = RigidBody(Vector2D(0, 0), mass=1.0)
        body_b = RigidBody(Vector2D(2, 0), mass=1.0)
        body_a.velocity = Vector2D(5, 0)
        body_b.velocity = Vector2D(0, 0)

        body_a.restitution = 0.0
        body_b.restitution = 0.0

        collision = CollisionDetector.circle_vs_circle(
            CircleCollider(body_a, 1.5),
            CircleCollider(body_b, 1.5)
        )

        if collision:
            CollisionResolver.resolve(collision)

        # Both should move in same direction with similar velocities
        assert body_a.velocity.x > 0
        assert body_b.velocity.x > 0


class TestConstraints:
    """Test constraint functionality."""

    def test_distance_constraint(self):
        body_a = RigidBody(Vector2D(0, 0))
        body_b = RigidBody(Vector2D(10, 0))
        constraint = DistanceConstraint(body_a, body_b, distance=5.0)

        # Move bodies closer
        body_b.position = Vector2D(3, 0)
        constraint.solve(1 / 60)

        # Should push them apart
        distance = body_a.position.distance_to(body_b.position)
        assert distance > 3.0

    def test_spring_constraint(self):
        body_a = RigidBody(Vector2D(0, 0), mass=1.0)
        body_b = RigidBody(Vector2D(10, 0), mass=1.0)
        constraint = SpringConstraint(body_a, body_b, rest_length=5.0, stiffness=10.0)

        # Apply spring force
        constraint.solve(1 / 60)

        # Should attract towards rest length
        assert body_a.force.x > 0
        assert body_b.force.x < 0


class TestPhysicsWorld:
    """Test PhysicsWorld functionality."""

    def test_world_creation(self):
        world = PhysicsWorld()
        assert len(world.bodies) == 0
        assert len(world.constraints) == 0

    def test_add_remove_body(self):
        world = PhysicsWorld()
        body = RigidBody(Vector2D(0, 0))
        collider = CircleCollider(body, 5.0)

        world.add_body(body, collider)
        assert len(world.bodies) == 1

        world.remove_body(body)
        assert len(world.bodies) == 0

    def test_gravity(self):
        world = PhysicsWorld()
        world.gravity = Vector2D(0, 10)

        body = RigidBody(Vector2D(0, 0), mass=1.0)
        world.add_body(body)

        world.step(1.0)

        # Body should have moved down
        assert body.position.y > 0

    def test_collision_in_world(self):
        world = PhysicsWorld()
        world.gravity = Vector2D(0, 0)

        body_a = RigidBody(Vector2D(0, 0), mass=1.0)
        body_b = RigidBody(Vector2D(2, 0), mass=1.0)

        collider_a = CircleCollider(body_a, 1.5)
        collider_b = CircleCollider(body_b, 1.5)

        world.add_body(body_a, collider_a)
        world.add_body(body_b, collider_b)

        # Move towards each other
        body_a.velocity = Vector2D(5, 0)
        body_b.velocity = Vector2D(-5, 0)

        world.step(1 / 60)

        # Should have collided and separated
        assert body_a.position.x < body_b.position.x


class TestIntegrators:
    """Test integrator functionality."""

    def test_euler_integration(self):
        integrator = EulerIntegrator()
        body = RigidBody(Vector2D(0, 0), mass=1.0)
        body.velocity = Vector2D(10, 0)

        integrator.integrate(body, 1.0)

        assert abs(body.position.x - 10.0) < 0.1

    def test_verlet_integration(self):
        integrator = VerletIntegrator()
        body = RigidBody(Vector2D(0, 0), mass=1.0)
        body.velocity = Vector2D(10, 0)

        integrator.integrate(body, 1.0)

        # Verlet should give similar results to Euler for constant velocity
        assert body.position.x > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
