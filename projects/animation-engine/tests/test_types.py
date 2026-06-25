"""Tests for type definitions."""

import math
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from animation_engine.types import Vector3, Color, Keyframe, AnimationConfig, TweenConfig, lerp_value


class TestVector3:
    def test_default(self):
        v = Vector3()
        assert v.x == 0.0
        assert v.y == 0.0
        assert v.z == 0.0

    def test_init(self):
        v = Vector3(1, 2, 3)
        assert v.x == 1
        assert v.y == 2
        assert v.z == 3

    def test_add(self):
        a = Vector3(1, 2, 3)
        b = Vector3(4, 5, 6)
        c = a + b
        assert c.x == 5
        assert c.y == 7
        assert c.z == 9

    def test_sub(self):
        a = Vector3(5, 7, 9)
        b = Vector3(1, 2, 3)
        c = a - b
        assert c.x == 4
        assert c.y == 5
        assert c.z == 6

    def test_mul(self):
        v = Vector3(1, 2, 3)
        r = v * 2
        assert r.x == 2
        assert r.y == 4
        assert r.z == 6

    def test_rmul(self):
        v = Vector3(1, 2, 3)
        r = 2 * v
        assert r.x == 2
        assert r.y == 4
        assert r.z == 6

    def test_length(self):
        v = Vector3(3, 4, 0)
        assert v.length() == pytest.approx(5.0)

    def test_normalized(self):
        v = Vector3(3, 4, 0)
        n = v.normalized()
        assert n.length() == pytest.approx(1.0)
        assert n.x == pytest.approx(0.6)
        assert n.y == pytest.approx(0.8)

    def test_normalized_zero(self):
        v = Vector3(0, 0, 0)
        n = v.normalized()
        assert n.x == 0
        assert n.y == 0
        assert n.z == 0

    def test_dot(self):
        a = Vector3(1, 0, 0)
        b = Vector3(0, 1, 0)
        assert a.dot(b) == 0.0

    def test_cross(self):
        a = Vector3(1, 0, 0)
        b = Vector3(0, 1, 0)
        c = a.cross(b)
        assert c.x == pytest.approx(0)
        assert c.y == pytest.approx(0)
        assert c.z == pytest.approx(1)

    def test_lerp(self):
        a = Vector3(0, 0, 0)
        b = Vector3(10, 20, 30)
        mid = Vector3.lerp(a, b, 0.5)
        assert mid.x == pytest.approx(5)
        assert mid.y == pytest.approx(10)
        assert mid.z == pytest.approx(15)

    def test_copy(self):
        v = Vector3(1, 2, 3)
        c = v.copy()
        c.x = 99
        assert v.x == 1  # Original unchanged

    def test_to_tuple(self):
        v = Vector3(1, 2, 3)
        assert v.to_tuple() == (1, 2, 3)


class TestColor:
    def test_default(self):
        c = Color()
        assert c.r == 1.0
        assert c.g == 1.0
        assert c.b == 1.0
        assert c.a == 1.0

    def test_init(self):
        c = Color(0.5, 0.3, 0.8, 0.9)
        assert c.r == 0.5
        assert c.g == 0.3
        assert c.b == 0.8
        assert c.a == 0.9

    def test_to_tuple(self):
        c = Color(0.1, 0.2, 0.3, 0.4)
        assert c.to_tuple() == (0.1, 0.2, 0.3, 0.4)

    def test_to_hex(self):
        c = Color(1, 0, 0, 1)
        assert c.to_hex() == "#ff0000"

    def test_to_hex_green(self):
        c = Color(0, 1, 0, 1)
        assert c.to_hex() == "#00ff00"

    def test_from_hex(self):
        c = Color.from_hex("#ff8000")
        assert c.r == pytest.approx(1.0)
        assert c.g == pytest.approx(128 / 255, abs=0.01)
        assert c.b == pytest.approx(0.0)
        assert c.a == 1.0

    def test_lerp(self):
        a = Color(1, 0, 0, 1)
        b = Color(0, 0, 1, 1)
        mid = Color.lerp(a, b, 0.5)
        assert mid.r == pytest.approx(0.5)
        assert mid.g == pytest.approx(0.0)
        assert mid.b == pytest.approx(0.5)

    def test_copy(self):
        c = Color(0.5, 0.5, 0.5, 1.0)
        cc = c.copy()
        cc.r = 0.0
        assert c.r == 0.5


class TestKeyframe:
    def test_valid(self):
        kf = Keyframe(time=0.5, values={"x": 10})
        assert kf.time == 0.5
        assert kf.values == {"x": 10}

    def test_invalid_time_low(self):
        with pytest.raises(ValueError):
            Keyframe(time=-0.1, values={})

    def test_invalid_time_high(self):
        with pytest.raises(ValueError):
            Keyframe(time=1.1, values={})

    def test_boundary_times(self):
        kf0 = Keyframe(time=0.0, values={})
        kf1 = Keyframe(time=1.0, values={})
        assert kf0.time == 0.0
        assert kf1.time == 1.0


class TestAnimationConfig:
    def test_defaults(self):
        kfs = [Keyframe(time=0, values={}), Keyframe(time=1, values={})]
        config = AnimationConfig(keyframes=kfs)
        assert config.duration == 1.0
        assert config.delay == 0.0
        assert config.iterations == 1
        assert config.direction == "normal"

    def test_custom(self):
        kfs = [Keyframe(time=0, values={"x": 0})]
        config = AnimationConfig(
            keyframes=kfs, duration=2.0, iterations=3, direction="alternate"
        )
        assert config.duration == 2.0
        assert config.iterations == 3
        assert config.direction == "alternate"


class TestTweenConfig:
    def test_defaults(self):
        config = TweenConfig(from_values={"x": 0}, to_values={"x": 1})
        assert config.duration == 1.0
        assert config.easing == "linear"


class TestLerpValue:
    def test_numeric(self):
        assert lerp_value(0, 10, 0.5) == pytest.approx(5.0)

    def test_float(self):
        assert lerp_value(0.0, 1.0, 0.25) == pytest.approx(0.25)

    def test_vector3(self):
        a = Vector3(0, 0, 0)
        b = Vector3(10, 20, 30)
        r = lerp_value(a, b, 0.5)
        assert r.x == pytest.approx(5)

    def test_color(self):
        a = Color(1, 0, 0, 1)
        b = Color(0, 1, 0, 1)
        r = lerp_value(a, b, 0.5)
        assert r.r == pytest.approx(0.5)

    def test_list(self):
        a = [0, 10, 20]
        b = [10, 20, 30]
        r = lerp_value(a, b, 0.5)
        assert r == [5, 15, 25]

    def test_discrete(self):
        assert lerp_value("a", "b", 0.3) == "a"
        assert lerp_value("a", "b", 0.7) == "b"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
