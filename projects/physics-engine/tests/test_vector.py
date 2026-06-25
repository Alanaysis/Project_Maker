"""Tests for Vector2D class."""

import pytest
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.vector import Vector2D


class TestVector2D:
    """Test Vector2D operations."""

    def test_creation(self):
        v = Vector2D(3, 4)
        assert v.x == 3
        assert v.y == 4

    def test_default_creation(self):
        v = Vector2D()
        assert v.x == 0
        assert v.y == 0

    def test_addition(self):
        v1 = Vector2D(1, 2)
        v2 = Vector2D(3, 4)
        result = v1 + v2
        assert result.x == 4
        assert result.y == 6

    def test_subtraction(self):
        v1 = Vector2D(5, 7)
        v2 = Vector2D(2, 3)
        result = v1 - v2
        assert result.x == 3
        assert result.y == 4

    def test_scalar_multiplication(self):
        v = Vector2D(2, 3)
        result = v * 2
        assert result.x == 4
        assert result.y == 6

    def test_rmul(self):
        v = Vector2D(2, 3)
        result = 2 * v
        assert result.x == 4
        assert result.y == 6

    def test_division(self):
        v = Vector2D(6, 8)
        result = v / 2
        assert result.x == 3
        assert result.y == 4

    def test_division_by_zero(self):
        v = Vector2D(1, 1)
        with pytest.raises(ValueError):
            v / 0

    def test_negation(self):
        v = Vector2D(3, -4)
        result = -v
        assert result.x == -3
        assert result.y == 4

    def test_dot_product(self):
        v1 = Vector2D(1, 2)
        v2 = Vector2D(3, 4)
        assert v1.dot(v2) == 11

    def test_cross_product(self):
        v1 = Vector2D(1, 0)
        v2 = Vector2D(0, 1)
        assert v1.cross(v2) == 1

    def test_length(self):
        v = Vector2D(3, 4)
        assert v.length() == 5.0

    def test_length_squared(self):
        v = Vector2D(3, 4)
        assert v.length_squared() == 25.0

    def test_normalized(self):
        v = Vector2D(3, 4)
        n = v.normalized()
        assert abs(n.length() - 1.0) < 1e-10
        assert abs(n.x - 0.6) < 1e-10
        assert abs(n.y - 0.8) < 1e-10

    def test_normalize_zero_vector(self):
        v = Vector2D(0, 0)
        n = v.normalized()
        assert n.x == 0
        assert n.y == 0

    def test_perpendicular(self):
        v = Vector2D(1, 0)
        p = v.perpendicular()
        # perpendicular() returns (-y, x) which is counterclockwise rotation
        assert p.x == 0
        assert p.y == 1

    def test_reflect(self):
        v = Vector2D(1, -1)
        normal = Vector2D(0, 1)
        r = v.reflect(normal)
        assert r.x == 1
        assert r.y == 1

    def test_distance_to(self):
        v1 = Vector2D(0, 0)
        v2 = Vector2D(3, 4)
        assert v1.distance_to(v2) == 5.0

    def test_angle(self):
        v = Vector2D(1, 0)
        assert v.angle() == 0.0

        v = Vector2D(0, 1)
        assert abs(v.angle() - math.pi / 2) < 1e-10

    def test_from_angle(self):
        v = Vector2D.from_angle(0)
        assert abs(v.x - 1.0) < 1e-10
        assert abs(v.y - 0.0) < 1e-10

    def test_zero(self):
        v = Vector2D.zero()
        assert v.x == 0
        assert v.y == 0

    def test_one(self):
        v = Vector2D.one()
        assert v.x == 1
        assert v.y == 1

    def test_iadd(self):
        v = Vector2D(1, 2)
        v += Vector2D(3, 4)
        assert v.x == 4
        assert v.y == 6

    def test_isub(self):
        v = Vector2D(5, 7)
        v -= Vector2D(2, 3)
        assert v.x == 3
        assert v.y == 4

    def test_imul(self):
        v = Vector2D(2, 3)
        v *= 2
        assert v.x == 4
        assert v.y == 6


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
