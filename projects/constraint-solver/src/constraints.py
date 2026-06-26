"""Constraints for 2D geometric constraint solving.

Each constraint type computes a residual that must be zero when satisfied.
Constraints work with a global variable vector containing only FREE (non-fixed)
point coordinates. Fixed points use their actual coordinates.
"""

import numpy as np
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import List, Optional, Tuple, Union
from .entities import Point, Line, Circle


class ConstraintType(Enum):
    DISTANCE = auto()
    ANGLE = auto()
    PARALLEL = auto()
    PERPENDICULAR = auto()
    COLLINAR = auto()
    CONCENTRIC = auto()
    TANGENT = auto()
    EQUAL_RADIUS = auto()
    MIDPOINT = auto()
    HORIZONTAL = auto()
    VERTICAL = auto()
    POINT_ON_CURVE = auto()
    SYMMETRY = auto()


class Constraint(ABC):
    """Abstract base class for all geometric constraints."""

    _next_id = 0

    def __init__(
        self,
        constraint_type: ConstraintType,
        entities: List[Point],
        value: float = 0.0,
        weight: float = 1.0,
    ):
        Constraint._next_id += 1
        self.id = Constraint._next_id
        self.constraint_type = constraint_type
        self.entities = entities
        self.value = value
        self.active = True
        self.weight = weight
        # Will be set by ConstraintSystem.build()
        self._global_var_map: Optional[List[Optional[int]]] = None

    def residual(self, values: np.ndarray) -> float:
        return self._residual_impl(values)

    @abstractmethod
    def _residual_impl(self, values: np.ndarray) -> float:
        pass

    def jacobian_indices(self) -> List[int]:
        """Get indices into the global variable vector for this constraint."""
        if self._global_var_map is not None:
            return [
                idx for idx in self._global_var_map if idx is not None
            ]
        # Fallback: check fixed_idx attribute on entities
        indices = []
        seen = set()
        for entity in self.entities:
            if hasattr(entity, 'fixed_idx') and entity.fixed_idx >= 0:
                for offset in range(self.num_equations()):
                    idx = entity.fixed_idx + offset
                    if idx not in seen:
                        indices.append(idx)
                        seen.add(idx)
        return indices

    def num_equations(self) -> int:
        return 1

    def check_satisfied(self, values: np.ndarray, tolerance: float = 1e-6) -> bool:
        return abs(self.residual(values)) < tolerance

    def __repr__(self) -> str:
        return f"Constraint({self.constraint_type.name}: {[e.name for e in self.entities]})"


class DistanceConstraint(Constraint):
    """Distance constraint between two points: ||P1 - P2|| - d = 0."""

    def __init__(self, p1: Point, p2: Point, distance: float, weight: float = 1.0):
        super().__init__(ConstraintType.DISTANCE, [p1, p2], distance, weight)
        self.p1 = p1
        self.p2 = p2

    def _residual_impl(self, values: np.ndarray) -> float:
        x1 = self.p1.x if self.p1.fixed else values[self.p1.fixed_idx]
        y1 = self.p1.y if self.p1.fixed else values[self.p1.fixed_idx + 1]
        x2 = self.p2.x if self.p2.fixed else values[self.p2.fixed_idx]
        y2 = self.p2.y if self.p2.fixed else values[self.p2.fixed_idx + 1]
        dx, dy = x2 - x1, y2 - y1
        return np.sqrt(dx * dx + dy * dy) - self.value


class AngleConstraint(Constraint):
    """Angle between two rays: angle(P1->P2, P3->P4) - theta = 0."""

    def __init__(self, p1: Point, p2: Point, p3: Point, p4: Point, angle: float, weight: float = 1.0):
        super().__init__(ConstraintType.ANGLE, [p1, p2, p3, p4], angle, weight)
        self.p1, self.p2, self.p3, self.p4 = p1, p2, p3, p4

    def _residual_impl(self, values: np.ndarray) -> float:
        def coord(p, c):
            if p.fixed:
                return p.x if c == 'x' else p.y
            base = p.fixed_idx
            return values[base + (0 if c == 'x' else 1)]

        x1, y1 = coord(self.p1, 'x'), coord(self.p1, 'y')
        x2, y2 = coord(self.p2, 'x'), coord(self.p2, 'y')
        x3, y3 = coord(self.p3, 'x'), coord(self.p3, 'y')
        x4, y4 = coord(self.p4, 'x'), coord(self.p4, 'y')

        v1 = np.array([x2 - x1, y2 - y1])
        v2 = np.array([x4 - x3, y4 - y3])
        n1, n2 = np.linalg.norm(v1), np.linalg.norm(v2)
        if n1 < 1e-12 or n2 < 1e-12:
            return 0.0
        cos_a = np.clip(np.dot(v1, v2) / (n1 * n2), -1.0, 1.0)
        return np.arccos(cos_a) - self.value


class ParallelConstraint(Constraint):
    """Parallel: cross product of direction vectors = 0."""

    def __init__(self, p1: Point, p2: Point, p3: Point, p4: Point, weight: float = 1.0):
        super().__init__(ConstraintType.PARALLEL, [p1, p2, p3, p4], 0.0, weight)
        self.p1, self.p2, self.p3, self.p4 = p1, p2, p3, p4

    def _residual_impl(self, values: np.ndarray) -> float:
        def coord(p, c):
            if p.fixed:
                return p.x if c == 'x' else p.y
            base = p.fixed_idx
            return values[base + (0 if c == 'x' else 1)]

        x1, y1 = coord(self.p1, 'x'), coord(self.p1, 'y')
        x2, y2 = coord(self.p2, 'x'), coord(self.p2, 'y')
        x3, y3 = coord(self.p3, 'x'), coord(self.p3, 'y')
        x4, y4 = coord(self.p4, 'x'), coord(self.p4, 'y')

        v1 = np.array([x2 - x1, y2 - y1])
        v2 = np.array([x4 - x3, y4 - y3])
        n1, n2 = np.linalg.norm(v1), np.linalg.norm(v2)
        if n1 < 1e-12 or n2 < 1e-12:
            return 0.0
        v1, v2 = v1 / n1, v2 / n2
        return v1[0] * v2[1] - v1[1] * v2[0]


class PerpendicularConstraint(Constraint):
    """Perpendicular: dot product of direction vectors = 0."""

    def __init__(self, p1: Point, p2: Point, p3: Point, p4: Point, weight: float = 1.0):
        super().__init__(ConstraintType.PERPENDICULAR, [p1, p2, p3, p4], 0.0, weight)
        self.p1, self.p2, self.p3, self.p4 = p1, p2, p3, p4

    def _residual_impl(self, values: np.ndarray) -> float:
        def coord(p, c):
            if p.fixed:
                return p.x if c == 'x' else p.y
            base = p.fixed_idx
            return values[base + (0 if c == 'x' else 1)]

        x1, y1 = coord(self.p1, 'x'), coord(self.p1, 'y')
        x2, y2 = coord(self.p2, 'x'), coord(self.p2, 'y')
        x3, y3 = coord(self.p3, 'x'), coord(self.p3, 'y')
        x4, y4 = coord(self.p4, 'x'), coord(self.p4, 'y')

        v1 = np.array([x2 - x1, y2 - y1])
        v2 = np.array([x4 - x3, y4 - y3])
        return float(np.dot(v1, v2))


class CollinearConstraint(Constraint):
    """Collinear: all points lie on the same line."""

    def __init__(self, points: List[Point], weight: float = 1.0):
        if len(points) < 3:
            raise ValueError("Collinear constraint requires at least 3 points")
        super().__init__(ConstraintType.COLLINAR, points, 0.0, weight)

    def _residual_impl(self, values: np.ndarray) -> float:
        def coord(p, c):
            if p.fixed:
                return p.x if c == 'x' else p.y
            base = p.fixed_idx
            return values[base + (0 if c == 'x' else 1)]

        x0, y0 = coord(self.entities[0], 'x'), coord(self.entities[0], 'y')
        vectors = []
        for pi in self.entities[1:]:
            xi, yi = coord(pi, 'x'), coord(pi, 'y')
            vectors.append([xi - x0, yi - y0])

        if len(vectors) < 2:
            return 0.0

        n0 = np.linalg.norm(vectors[0])
        if n0 < 1e-12:
            return 0.0
        v0 = vectors[0] / n0
        total = sum(v0[0] * v[1] - v0[1] * v[0] for v in vectors[1:])
        return np.sqrt(sum(c * c for c in total)) if isinstance(total, list) else abs(total)


class ConcentricConstraint(Constraint):
    """Concentric: two circles share the same center."""

    def __init__(self, c1: Circle, c2: Circle, weight: float = 1.0):
        super().__init__(ConstraintType.CONCENTRIC, [c1.center, c2.center], 0.0, weight)
        self.circles = [c1, c2]

    def _residual_impl(self, values: np.ndarray) -> float:
        def center(c):
            p = c.center
            if p.fixed:
                return p.x, p.y
            base = p.fixed_idx
            return values[base], values[base + 1]

        x1, y1 = center(self.circles[0])
        x2, y2 = center(self.circles[1])
        return np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

    def num_equations(self) -> int:
        return 2


class TangentConstraint(Constraint):
    """Tangent: circle tangent to line or another circle."""

    def __init__(self, circle: Circle, entity: Union['Circle', 'Line', Tuple[Point, Point]], weight: float = 1.0):
        super().__init__(ConstraintType.TANGENT, [], 0.0, weight)
        self.circle = circle
        self.entity = entity

        if isinstance(entity, Circle):
            self.entities = [circle.center, entity.center]
            self.mode = 'circle-circle'
        elif isinstance(entity, Line):
            self.entities = [circle.center, entity.start, entity.end]
            self.mode = 'circle-line'
        else:
            self.entities = [circle.center] + list(entity)
            self.mode = 'line'

    def _residual_impl(self, values: np.ndarray) -> float:
        def coord(p):
            if p.fixed:
                return p.x, p.y
            base = p.fixed_idx
            return values[base], values[base + 1]

        if self.mode == 'circle-circle':
            cx1, cy1 = coord(self.circle.center)
            cx2, cy2 = coord(self.entity.center)
            return np.sqrt((cx1 - cx2) ** 2 + (cy1 - cy2) ** 2) - (self.circle.radius + self.entity.radius)

        cx, cy = coord(self.circle.center)
        x1, y1 = coord(self.entities[1])
        x2, y2 = coord(self.entities[2])
        dx, dy = x2 - x1, y2 - y1
        len_sq = dx * dx + dy * dy
        if len_sq < 1e-12:
            return 0.0
        return abs(dy * cx - dx * cy + x2 * y1 - y2 * x1) / np.sqrt(len_sq) - self.circle.radius


class EqualRadiusConstraint(Constraint):
    """Equal radius: two circles have the same radius."""

    def __init__(self, c1: Circle, c2: Circle, weight: float = 1.0):
        super().__init__(ConstraintType.EQUAL_RADIUS, [c1.center, c2.center], 0.0, weight)
        self.circles = [c1, c2]

    def _residual_impl(self, values: np.ndarray) -> float:
        return self.circles[0].radius - self.circles[1].radius


class MidpointConstraint(Constraint):
    """Midpoint: point is midpoint of line segment."""

    def __init__(self, mid_point: Point, p1: Point, p2: Point, weight: float = 1.0):
        super().__init__(ConstraintType.MIDPOINT, [mid_point, p1, p2], 0.0, weight)
        self.mid_point = mid_point
        self.p1 = p1
        self.p2 = p2

    def _residual_impl(self, values: np.ndarray) -> float:
        def coord(p):
            if p.fixed:
                return p.x, p.y
            base = p.fixed_idx
            return values[base], values[base + 1]

        mx, my = coord(self.mid_point)
        x1, y1 = coord(self.p1)
        x2, y2 = coord(self.p2)
        dx = mx - (x1 + x2) / 2.0
        dy = my - (y1 + y2) / 2.0
        return np.sqrt(dx * dx + dy * dy)


class HorizontalConstraint(Constraint):
    """Horizontal: two points have the same y coordinate."""

    def __init__(self, p1: Point, p2: Point, weight: float = 1.0):
        super().__init__(ConstraintType.HORIZONTAL, [p1, p2], 0.0, weight)
        self.p1, self.p2 = p1, p2

    def _residual_impl(self, values: np.ndarray) -> float:
        y1 = self.p1.y if self.p1.fixed else values[self.p1.fixed_idx + 1]
        y2 = self.p2.y if self.p2.fixed else values[self.p2.fixed_idx + 1]
        return y1 - y2


class VerticalConstraint(Constraint):
    """Vertical: two points have the same x coordinate."""

    def __init__(self, p1: Point, p2: Point, weight: float = 1.0):
        super().__init__(ConstraintType.VERTICAL, [p1, p2], 0.0, weight)
        self.p1, self.p2 = p1, p2

    def _residual_impl(self, values: np.ndarray) -> float:
        x1 = self.p1.x if self.p1.fixed else values[self.p1.fixed_idx]
        x2 = self.p2.x if self.p2.fixed else values[self.p2.fixed_idx]
        return x1 - x2


def create_constraint(constraint_type: ConstraintType, *args, **kwargs) -> Constraint:
    """Factory function to create constraint instances."""
    constraint_map = {
        ConstraintType.DISTANCE: DistanceConstraint,
        ConstraintType.ANGLE: AngleConstraint,
        ConstraintType.PARALLEL: ParallelConstraint,
        ConstraintType.PERPENDICULAR: PerpendicularConstraint,
        ConstraintType.COLLINAR: CollinearConstraint,
        ConstraintType.CONCENTRIC: ConcentricConstraint,
        ConstraintType.EQUAL_RADIUS: EqualRadiusConstraint,
        ConstraintType.MIDPOINT: MidpointConstraint,
        ConstraintType.HORIZONTAL: HorizontalConstraint,
        ConstraintType.VERTICAL: VerticalConstraint,
    }
    if constraint_type not in constraint_map:
        raise ValueError(f"Unsupported constraint type: {constraint_type}")
    return constraint_map[constraint_type](*args, **kwargs)
