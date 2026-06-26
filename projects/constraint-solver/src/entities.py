"""Geometric entities: Point, Line, Circle, and other basic shapes."""

import numpy as np
from enum import Enum, auto
from typing import List, Optional, Tuple


class EntityType(Enum):
    """Enumeration of supported geometric entity types."""
    POINT = auto()
    LINE = auto()
    CIRCLE = auto()
    ARC = auto()
    POLYGON = auto()


class Point:
    """A 2D point with x and y coordinates.

    Points are the fundamental building blocks of geometric constraints.
    Each point has free (unknown) or fixed (known) coordinates.

    Attributes:
        id: Unique identifier for this point
        x: X coordinate (numpy array for numerical solver compatibility)
        y: Y coordinate
        fixed: Whether this point's position is fixed (driven by dimensions)
        name: Optional human-readable name
        constraints: List of constraints involving this point
    """

    _next_id = 0

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        fixed: bool = False,
        name: Optional[str] = None,
    ):
        """Initialize a 2D point.

        Args:
            x: Initial X coordinate
            y: Initial Y coordinate
            fixed: If True, this point acts as an anchor (does not move)
            name: Optional display name
        """
        Point._next_id += 1
        self.id = Point._next_id
        self.x = x
        self.y = y
        self.fixed = fixed
        self.name = name or f"P{self.id}"
        self.constraints: List['Constraint'] = []
        self.fixed_idx: int = -1  # Global variable index in solver (set during build)

    def to_array(self) -> np.ndarray:
        """Convert point to numpy array [x, y]."""
        return np.array([self.x, self.y])

    def from_array(self, arr: np.ndarray) -> None:
        """Update point coordinates from numpy array.

        Args:
            arr: Array with shape (2,) containing [x, y]
        """
        self.x = arr[0]
        self.y = arr[1]

    def distance_to(self, other: 'Point') -> float:
        """Calculate Euclidean distance to another point.

        Args:
            other: Another Point instance

        Returns:
            Euclidean distance between the two points
        """
        dx = self.x - other.x
        dy = self.y - other.y
        return np.sqrt(dx * dx + dy * dy)

    def angle_to(self, other: 'Point') -> float:
        """Calculate angle from this point to another.

        Args:
            other: Another Point instance

        Returns:
            Angle in radians measured from positive X axis
        """
        return np.arctan2(other.y - self.y, other.x - self.x)

    def __repr__(self) -> str:
        return f"Point({self.name}: ({self.x:.3f}, {self.y:.3f})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Point):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


class Line:
    """A line segment defined by two endpoints.

    Attributes:
        id: Unique identifier
        start: Start Point
        end: End Point
        name: Optional display name
        constraints: List of constraints involving this line
    """

    _next_id = 0

    def __init__(
        self,
        start: Point,
        end: Point,
        name: Optional[str] = None,
    ):
        Line._next_id += 1
        self.id = Line._next_id
        self.start = start
        self.end = end
        self.name = name or f"L{self.id}"
        self.constraints: List['Constraint'] = []

    @property
    def direction(self) -> np.ndarray:
        """Get the direction vector of the line."""
        return np.array([self.end.x - self.start.x, self.end.y - self.start.y])

    @property
    def length(self) -> float:
        """Get the length of the line segment."""
        return self.start.distance_to(self.end)

    @property
    def midpoint(self) -> Point:
        """Get the midpoint of the line segment."""
        return Point(
            (self.start.x + self.end.x) / 2.0,
            (self.start.y + self.end.y) / 2.0,
        )

    def __repr__(self) -> str:
        return f"Line({self.name}: {self.start.name}->{self.end.name})"


class Circle:
    """A circle defined by center point and radius.

    Attributes:
        id: Unique identifier
        center: Center Point
        radius: Radius value
        name: Optional display name
        constraints: List of constraints involving this circle
    """

    _next_id = 0

    def __init__(
        self,
        center: Point,
        radius: float = 1.0,
        name: Optional[str] = None,
    ):
        Circle._next_id += 1
        self.id = Circle._next_id
        self.center = center
        self.radius = radius
        self.name = name or f"C{self.id}"
        self.constraints: List['Constraint'] = []

    def __repr__(self) -> str:
        return f"Circle({self.name}: center={self.center.name}, r={self.radius:.3f})"


class GeometricEntity:
    """Base class for all geometric entities with common interface."""

    def __init__(self, entity_type: EntityType, name: str = ""):
        self.entity_type = entity_type
        self.name = name
        self.constraints: List['Constraint'] = []

    def get_variables(self) -> List[Point]:
        """Get all points that define this entity."""
        raise NotImplementedError

    def update_from_solution(self, values: np.ndarray) -> None:
        """Update entity geometry from solver output values."""
        raise NotImplementedError

    def residual(self) -> float:
        """Calculate constraint violation for this entity."""
        raise NotImplementedError
