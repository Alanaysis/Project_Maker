"""Collider shapes for collision detection."""

from abc import ABC, abstractmethod
from .vector import Vector2D
from .rigidbody import RigidBody


class Collider(ABC):
    """Base collider class."""

    def __init__(self, body: RigidBody):
        self.body = body

    @abstractmethod
    def get_aabb(self) -> tuple[Vector2D, Vector2D]:
        """Get axis-aligned bounding box (min, max)."""
        pass

    @abstractmethod
    def contains_point(self, point: Vector2D) -> bool:
        """Check if point is inside collider."""
        pass


class CircleCollider(Collider):
    """Circle collider shape."""

    def __init__(self, body: RigidBody, radius: float = 1.0):
        super().__init__(body)
        self.radius = radius

    def get_aabb(self) -> tuple[Vector2D, Vector2D]:
        """Get AABB for circle."""
        min_point = self.body.position - Vector2D(self.radius, self.radius)
        max_point = self.body.position + Vector2D(self.radius, self.radius)
        return min_point, max_point

    def contains_point(self, point: Vector2D) -> bool:
        """Check if point is inside circle."""
        distance = self.body.position.distance_to(point)
        return distance <= self.radius

    def __repr__(self) -> str:
        return f"CircleCollider(radius={self.radius}, pos={self.body.position})"


class AABBCollider(Collider):
    """Axis-Aligned Bounding Box collider."""

    def __init__(self, body: RigidBody, width: float = 1.0, height: float = 1.0):
        super().__init__(body)
        self.width = width
        self.height = height
        self.half_width = width / 2
        self.half_height = height / 2

    def get_aabb(self) -> tuple[Vector2D, Vector2D]:
        """Get AABB."""
        min_point = self.body.position - Vector2D(self.half_width, self.half_height)
        max_point = self.body.position + Vector2D(self.half_width, self.half_height)
        return min_point, max_point

    def contains_point(self, point: Vector2D) -> bool:
        """Check if point is inside AABB."""
        min_point, max_point = self.get_aabb()
        return (
            min_point.x <= point.x <= max_point.x and
            min_point.y <= point.y <= max_point.y
        )

    def get_corners(self) -> list[Vector2D]:
        """Get the four corners of the AABB."""
        min_point, max_point = self.get_aabb()
        return [
            Vector2D(min_point.x, min_point.y),
            Vector2D(max_point.x, min_point.y),
            Vector2D(max_point.x, max_point.y),
            Vector2D(min_point.x, max_point.y),
        ]

    def __repr__(self) -> str:
        return f"AABBCollider(width={self.width}, height={self.height})"


class PolygonCollider(Collider):
    """Convex polygon collider for SAT collision detection."""

    def __init__(self, body: RigidBody, vertices: list[Vector2D]):
        super().__init__(body)
        self.vertices = vertices
        self._normals = self._calculate_normals()

    def _calculate_normals(self) -> list[Vector2D]:
        """Calculate edge normals for SAT."""
        normals = []
        n = len(self.vertices)
        for i in range(n):
            edge = self.vertices[(i + 1) % n] - self.vertices[i]
            normal = edge.perpendicular().normalized()
            normals.append(normal)
        return normals

    def get_world_vertices(self) -> list[Vector2D]:
        """Get vertices in world space."""
        return [v + self.body.position for v in self.vertices]

    def get_world_normals(self) -> list[Vector2D]:
        """Get normals in world space (rotation not implemented for simplicity)."""
        return self._normals.copy()

    def get_aabb(self) -> tuple[Vector2D, Vector2D]:
        """Get AABB for polygon."""
        world_vertices = self.get_world_vertices()
        min_x = min(v.x for v in world_vertices)
        min_y = min(v.y for v in world_vertices)
        max_x = max(v.x for v in world_vertices)
        max_y = max(v.y for v in world_vertices)
        return Vector2D(min_x, min_y), Vector2D(max_x, max_y)

    def contains_point(self, point: Vector2D) -> bool:
        """Check if point is inside polygon using cross product method."""
        world_vertices = self.get_world_vertices()
        n = len(world_vertices)
        for i in range(n):
            v1 = world_vertices[i]
            v2 = world_vertices[(i + 1) % n]
            edge = v2 - v1
            to_point = point - v1
            if edge.cross(to_point) < 0:
                return False
        return True

    @staticmethod
    def create_box(body: RigidBody, width: float, height: float) -> 'PolygonCollider':
        """Create a box polygon collider."""
        half_w = width / 2
        half_h = height / 2
        vertices = [
            Vector2D(-half_w, -half_h),
            Vector2D(half_w, -half_h),
            Vector2D(half_w, half_h),
            Vector2D(-half_w, half_h),
        ]
        return PolygonCollider(body, vertices)

    def __repr__(self) -> str:
        return f"PolygonCollider(vertices={len(self.vertices)})"
