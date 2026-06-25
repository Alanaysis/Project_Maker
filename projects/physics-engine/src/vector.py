"""2D Vector implementation for physics calculations."""

import math
from dataclasses import dataclass


@dataclass
class Vector2D:
    """2D vector class with common vector operations."""
    x: float = 0.0
    y: float = 0.0

    def __add__(self, other: 'Vector2D') -> 'Vector2D':
        return Vector2D(self.x + other.x, self.y + other.y)

    def __sub__(self, other: 'Vector2D') -> 'Vector2D':
        return Vector2D(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> 'Vector2D':
        return Vector2D(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar: float) -> 'Vector2D':
        return self.__mul__(scalar)

    def __truediv__(self, scalar: float) -> 'Vector2D':
        if scalar == 0:
            raise ValueError("Cannot divide by zero")
        return Vector2D(self.x / scalar, self.y / scalar)

    def __neg__(self) -> 'Vector2D':
        return Vector2D(-self.x, -self.y)

    def __iadd__(self, other: 'Vector2D') -> 'Vector2D':
        self.x += other.x
        self.y += other.y
        return self

    def __isub__(self, other: 'Vector2D') -> 'Vector2D':
        self.x -= other.x
        self.y -= other.y
        return self

    def __imul__(self, scalar: float) -> 'Vector2D':
        self.x *= scalar
        self.y *= scalar
        return self

    def __itruediv__(self, scalar: float) -> 'Vector2D':
        if scalar == 0:
            raise ValueError("Cannot divide by zero")
        self.x /= scalar
        self.y /= scalar
        return self

    def dot(self, other: 'Vector2D') -> float:
        """Calculate dot product."""
        return self.x * other.x + self.y * other.y

    def cross(self, other: 'Vector2D') -> float:
        """Calculate cross product (returns scalar in 2D)."""
        return self.x * other.y - self.y * other.x

    def length(self) -> float:
        """Calculate vector length."""
        return math.sqrt(self.x * self.x + self.y * self.y)

    def length_squared(self) -> float:
        """Calculate vector length squared (faster than length)."""
        return self.x * self.x + self.y * self.y

    def normalized(self) -> 'Vector2D':
        """Return normalized vector."""
        length = self.length()
        if length == 0:
            return Vector2D(0, 0)
        return Vector2D(self.x / length, self.y / length)

    def normalize(self) -> None:
        """Normalize this vector in place."""
        length = self.length()
        if length > 0:
            self.x /= length
            self.y /= length

    def perpendicular(self) -> 'Vector2D':
        """Return perpendicular vector (rotated 90 degrees counterclockwise)."""
        return Vector2D(-self.y, self.x)

    def reflect(self, normal: 'Vector2D') -> 'Vector2D':
        """Reflect vector around normal."""
        return self - 2 * self.dot(normal) * normal

    def distance_to(self, other: 'Vector2D') -> float:
        """Calculate distance to another vector."""
        return (self - other).length()

    def angle(self) -> float:
        """Calculate angle in radians."""
        return math.atan2(self.y, self.x)

    @staticmethod
    def from_angle(angle: float, length: float = 1.0) -> 'Vector2D':
        """Create vector from angle and length."""
        return Vector2D(math.cos(angle) * length, math.sin(angle) * length)

    @staticmethod
    def zero() -> 'Vector2D':
        """Return zero vector."""
        return Vector2D(0, 0)

    @staticmethod
    def one() -> 'Vector2D':
        """Return one vector."""
        return Vector2D(1, 1)

    def __repr__(self) -> str:
        return f"Vector2D({self.x:.2f}, {self.y:.2f})"
