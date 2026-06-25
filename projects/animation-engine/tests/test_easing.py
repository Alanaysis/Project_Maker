"""Tests for easing functions."""

import math
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from animation_engine.easing import (
    linear,
    ease_in_quad, ease_out_quad, ease_in_out_quad,
    ease_in_cubic, ease_out_cubic, ease_in_out_cubic,
    ease_in_sine, ease_out_sine, ease_in_out_sine,
    ease_in_expo, ease_out_expo, ease_in_out_expo,
    ease_in_circ, ease_out_circ, ease_in_out_circ,
    ease_in_elastic, ease_out_elastic, ease_in_out_elastic,
    ease_in_back, ease_out_back, ease_in_out_back,
    ease_in_bounce, ease_out_bounce, ease_in_out_bounce,
    get_easing_function, list_easing_functions,
    EASING_FUNCTIONS,
)


class TestLinearEasing:
    def test_start(self):
        assert linear(0.0) == 0.0

    def test_end(self):
        assert linear(1.0) == 1.0

    def test_mid(self):
        assert linear(0.5) == 0.5

    def test_quarter(self):
        assert linear(0.25) == 0.25


class TestQuadraticEasing:
    def test_ease_in_quad_boundaries(self):
        assert ease_in_quad(0.0) == 0.0
        assert ease_in_quad(1.0) == 1.0

    def test_ease_in_quad_mid(self):
        assert ease_in_quad(0.5) == pytest.approx(0.25)

    def test_ease_out_quad_boundaries(self):
        assert ease_out_quad(0.0) == 0.0
        assert ease_out_quad(1.0) == pytest.approx(1.0)

    def test_ease_out_quad_mid(self):
        assert ease_out_quad(0.5) == pytest.approx(0.75)

    def test_ease_in_out_quad_boundaries(self):
        assert ease_in_out_quad(0.0) == 0.0
        assert ease_in_out_quad(1.0) == pytest.approx(1.0)

    def test_ease_in_out_quad_mid(self):
        assert ease_in_out_quad(0.5) == pytest.approx(0.5)


class TestCubicEasing:
    def test_ease_in_cubic_boundaries(self):
        assert ease_in_cubic(0.0) == 0.0
        assert ease_in_cubic(1.0) == 1.0

    def test_ease_in_cubic_mid(self):
        assert ease_in_cubic(0.5) == pytest.approx(0.125)

    def test_ease_out_cubic_boundaries(self):
        assert ease_out_cubic(0.0) == pytest.approx(0.0)
        assert ease_out_cubic(1.0) == pytest.approx(1.0)

    def test_ease_in_out_cubic_boundaries(self):
        assert ease_in_out_cubic(0.0) == 0.0
        assert ease_in_out_cubic(1.0) == pytest.approx(1.0)


class TestSineEasing:
    def test_ease_in_sine_boundaries(self):
        assert ease_in_sine(0.0) == 0.0
        assert ease_in_sine(1.0) == pytest.approx(1.0)

    def test_ease_out_sine_boundaries(self):
        assert ease_out_sine(0.0) == 0.0
        assert ease_out_sine(1.0) == pytest.approx(1.0)

    def test_ease_in_out_sine_boundaries(self):
        assert ease_in_out_sine(0.0) == 0.0
        assert ease_in_out_sine(1.0) == pytest.approx(1.0)

    def test_ease_in_out_sine_mid(self):
        assert ease_in_out_sine(0.5) == pytest.approx(0.5)


class TestExponentialEasing:
    def test_ease_in_expo_boundaries(self):
        assert ease_in_expo(0.0) == 0.0
        assert ease_in_expo(1.0) == pytest.approx(1.0)

    def test_ease_out_expo_boundaries(self):
        assert ease_out_expo(0.0) == 0.0
        assert ease_out_expo(1.0) == pytest.approx(1.0)

    def test_ease_in_out_expo_boundaries(self):
        assert ease_in_out_expo(0.0) == 0.0
        assert ease_in_out_expo(1.0) == pytest.approx(1.0)


class TestCircularEasing:
    def test_ease_in_circ_boundaries(self):
        assert ease_in_circ(0.0) == 0.0
        assert ease_in_circ(1.0) == pytest.approx(1.0)

    def test_ease_out_circ_boundaries(self):
        assert ease_out_circ(0.0) == 0.0
        assert ease_out_circ(1.0) == pytest.approx(1.0)

    def test_ease_in_out_circ_boundaries(self):
        assert ease_in_out_circ(0.0) == 0.0
        assert ease_in_out_circ(1.0) == pytest.approx(1.0)


class TestElasticEasing:
    def test_ease_in_elastic_boundaries(self):
        assert ease_in_elastic(0.0) == 0.0
        assert ease_in_elastic(1.0) == pytest.approx(1.0)

    def test_ease_out_elastic_boundaries(self):
        assert ease_out_elastic(0.0) == 0.0
        assert ease_out_elastic(1.0) == pytest.approx(1.0)

    def test_ease_in_out_elastic_boundaries(self):
        assert ease_in_out_elastic(0.0) == 0.0
        assert ease_in_out_elastic(1.0) == pytest.approx(1.0)

    def test_elastic_overshoot(self):
        # Elastic functions should overshoot at certain points
        v = ease_out_elastic(0.2)
        assert v > 1.0  # Overshoots


class TestBackEasing:
    def test_ease_in_back_boundaries(self):
        assert ease_in_back(0.0) == 0.0
        assert ease_in_back(1.0) == pytest.approx(1.0)

    def test_ease_out_back_boundaries(self):
        assert ease_out_back(0.0) == pytest.approx(0.0)
        assert ease_out_back(1.0) == pytest.approx(1.0)

    def test_ease_in_out_back_boundaries(self):
        assert ease_in_out_back(0.0) == 0.0
        assert ease_in_out_back(1.0) == pytest.approx(1.0)

    def test_back_undershoot(self):
        # Back functions should undershoot at start
        v = ease_in_back(0.2)
        assert v < 0.0


class TestBounceEasing:
    def test_ease_in_bounce_boundaries(self):
        assert ease_in_bounce(0.0) == 0.0
        assert ease_in_bounce(1.0) == pytest.approx(1.0)

    def test_ease_out_bounce_boundaries(self):
        assert ease_out_bounce(0.0) == 0.0
        assert ease_out_bounce(1.0) == pytest.approx(1.0)

    def test_ease_in_out_bounce_boundaries(self):
        assert ease_in_out_bounce(0.0) == 0.0
        assert ease_in_out_bounce(1.0) == pytest.approx(1.0)

    def test_bounce_non_negative(self):
        # Bounce values should always be non-negative
        for i in range(101):
            t = i / 100.0
            assert ease_out_bounce(t) >= 0.0


class TestEasingRegistry:
    def test_get_easing_function_valid(self):
        fn = get_easing_function("linear")
        assert fn(0.5) == 0.5

    def test_get_easing_function_css_format(self):
        fn = get_easing_function("ease-in-quad")
        assert fn(0.5) == pytest.approx(0.25)

    def test_get_easing_function_invalid(self):
        with pytest.raises(ValueError, match="Unknown easing function"):
            get_easing_function("nonexistent")

    def test_list_easing_functions(self):
        funcs = list_easing_functions()
        assert "linear" in funcs
        assert "ease_in_quad" in funcs
        assert "ease_out_bounce" in funcs
        assert len(funcs) >= 30

    def test_all_registered_functions_valid(self):
        for name, fn in EASING_FUNCTIONS.items():
            assert fn(0.0) == pytest.approx(0.0, abs=0.01), f"{name} at t=0"
            assert fn(1.0) == pytest.approx(1.0, abs=0.01), f"{name} at t=1"


class TestEasingMonotonicity:
    """Test that ease-in and ease-out functions are monotonic."""

    def test_ease_in_quad_monotone(self):
        prev = ease_in_quad(0.0)
        for i in range(1, 101):
            t = i / 100.0
            v = ease_in_quad(t)
            assert v >= prev
            prev = v

    def test_ease_out_cubic_monotone(self):
        prev = ease_out_cubic(0.0)
        for i in range(1, 101):
            t = i / 100.0
            v = ease_out_cubic(t)
            assert v >= prev
            prev = v


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
