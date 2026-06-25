"""Collision detection algorithms."""

from dataclasses import dataclass
from .vector import Vector2D
from .collider import Collider, CircleCollider, AABBCollider, PolygonCollider


@dataclass
class CollisionInfo:
    """Information about a collision."""
    body_a: 'RigidBody'
    body_b: 'RigidBody'
    normal: Vector2D
    penetration: float
    contact_point: Vector2D


class CollisionDetector:
    """Handles collision detection between different shapes."""

    @staticmethod
    def check_collision(a: Collider, b: Collider) -> CollisionInfo | None:
        """Check collision between two colliders."""
        if isinstance(a, CircleCollider) and isinstance(b, CircleCollider):
            return CollisionDetector.circle_vs_circle(a, b)
        elif isinstance(a, AABBCollider) and isinstance(b, AABBCollider):
            return CollisionDetector.aabb_vs_aabb(a, b)
        elif isinstance(a, CircleCollider) and isinstance(b, AABBCollider):
            return CollisionDetector.circle_vs_aabb(a, b)
        elif isinstance(a, AABBCollider) and isinstance(b, CircleCollider):
            result = CollisionDetector.circle_vs_aabb(b, a)
            if result:
                result.normal = -result.normal
                result.body_a, result.body_b = result.body_b, result.body_a
            return result
        elif isinstance(a, PolygonCollider) and isinstance(b, PolygonCollider):
            return CollisionDetector.sat_polygon_vs_polygon(a, b)
        return None

    @staticmethod
    def circle_vs_circle(a: CircleCollider, b: CircleCollider) -> CollisionInfo | None:
        """Detect collision between two circles."""
        diff = b.body.position - a.body.position
        distance = diff.length()
        sum_radius = a.radius + b.radius

        if distance >= sum_radius:
            return None

        # Collision detected
        if distance == 0:
            # Circles are at same position
            normal = Vector2D(1, 0)
            penetration = a.radius
        else:
            normal = diff.normalized()
            penetration = sum_radius - distance

        contact_point = a.body.position + normal * a.radius

        return CollisionInfo(
            body_a=a.body,
            body_b=b.body,
            normal=normal,
            penetration=penetration,
            contact_point=contact_point,
        )

    @staticmethod
    def aabb_vs_aabb(a: AABBCollider, b: AABBCollider) -> CollisionInfo | None:
        """Detect collision between two AABBs."""
        a_min, a_max = a.get_aabb()
        b_min, b_max = b.get_aabb()

        # Check overlap on each axis
        overlap_x = min(a_max.x, b_max.x) - max(a_min.x, b_min.x)
        overlap_y = min(a_max.y, b_max.y) - max(a_min.y, b_min.y)

        if overlap_x <= 0 or overlap_y <= 0:
            return None

        # Find minimum penetration axis
        if overlap_x < overlap_y:
            # Collision on X axis
            if a.body.position.x < b.body.position.x:
                normal = Vector2D(1, 0)
            else:
                normal = Vector2D(-1, 0)
            penetration = overlap_x
        else:
            # Collision on Y axis
            if a.body.position.y < b.body.position.y:
                normal = Vector2D(0, 1)
            else:
                normal = Vector2D(0, -1)
            penetration = overlap_y

        contact_point = (a.body.position + b.body.position) * 0.5

        return CollisionInfo(
            body_a=a.body,
            body_b=b.body,
            normal=normal,
            penetration=penetration,
            contact_point=contact_point,
        )

    @staticmethod
    def circle_vs_aabb(circle: CircleCollider, aabb: AABBCollider) -> CollisionInfo | None:
        """Detect collision between circle and AABB."""
        # Find closest point on AABB to circle center
        aabb_min, aabb_max = aabb.get_aabb()

        closest_x = max(aabb_min.x, min(circle.body.position.x, aabb_max.x))
        closest_y = max(aabb_min.y, min(circle.body.position.y, aabb_max.y))
        closest = Vector2D(closest_x, closest_y)

        # Check if closest point is inside circle
        diff = closest - circle.body.position
        distance = diff.length()

        if distance >= circle.radius:
            return None

        if distance == 0:
            # Circle center is inside AABB
            # Find shortest exit direction
            dx = min(circle.body.position.x - aabb_min.x, aabb_max.x - circle.body.position.x)
            dy = min(circle.body.position.y - aabb_min.y, aabb_max.y - circle.body.position.y)

            if dx < dy:
                if circle.body.position.x < aabb.body.position.x:
                    normal = Vector2D(-1, 0)
                else:
                    normal = Vector2D(1, 0)
                penetration = dx + circle.radius
            else:
                if circle.body.position.y < aabb.body.position.y:
                    normal = Vector2D(0, -1)
                else:
                    normal = Vector2D(0, 1)
                penetration = dy + circle.radius
        else:
            normal = diff.normalized()
            penetration = circle.radius - distance

        contact_point = closest

        return CollisionInfo(
            body_a=circle.body,
            body_b=aabb.body,
            normal=normal,
            penetration=penetration,
            contact_point=contact_point,
        )

    @staticmethod
    def sat_polygon_vs_polygon(a: PolygonCollider, b: PolygonCollider) -> CollisionInfo | None:
        """Detect collision between two polygons using Separating Axis Theorem."""
        a_vertices = a.get_world_vertices()
        b_vertices = b.get_world_vertices()

        # Get all potential separating axes
        axes = []
        for vertices in [a_vertices, b_vertices]:
            n = len(vertices)
            for i in range(n):
                edge = vertices[(i + 1) % n] - vertices[i]
                axis = edge.perpendicular().normalized()
                axes.append(axis)

        min_overlap = float('inf')
        min_axis = None

        for axis in axes:
            # Project both polygons onto axis
            a_min, a_max = CollisionDetector._project_polygon(a_vertices, axis)
            b_min, b_max = CollisionDetector._project_polygon(b_vertices, axis)

            # Check for gap
            if a_max < b_min or b_max < a_min:
                return None  # Separating axis found

            # Calculate overlap
            overlap = min(a_max - b_min, b_max - a_min)
            if overlap < min_overlap:
                min_overlap = overlap
                min_axis = axis

        # Ensure normal points from A to B
        direction = b.body.position - a.body.position
        if direction.dot(min_axis) < 0:
            min_axis = -min_axis

        contact_point = CollisionDetector._find_contact_point(
            a_vertices, b_vertices, min_axis
        )

        return CollisionInfo(
            body_a=a.body,
            body_b=b.body,
            normal=min_axis,
            penetration=min_overlap,
            contact_point=contact_point,
        )

    @staticmethod
    def _project_polygon(vertices: list[Vector2D], axis: Vector2D) -> tuple[float, float]:
        """Project polygon onto axis and return min/max."""
        projections = [v.dot(axis) for v in vertices]
        return min(projections), max(projections)

    @staticmethod
    def _find_contact_point(
        a_vertices: list[Vector2D],
        b_vertices: list[Vector2D],
        normal: Vector2D,
    ) -> Vector2D:
        """Find approximate contact point between two polygons."""
        # Simple approximation: average of closest vertices
        a_closest = min(a_vertices, key=lambda v: v.dot(normal))
        b_closest = min(b_vertices, key=lambda v: v.dot(-normal))
        return (a_closest + b_closest) * 0.5
