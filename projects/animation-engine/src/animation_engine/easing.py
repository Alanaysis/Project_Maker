"""
Easing functions for smooth animation transitions.

All easing functions take a normalized time t in [0, 1] and return
an eased value, typically also in [0, 1] but some functions may
exceed this range for overshoot effects.
"""

from __future__ import annotations

import math
from typing import Callable, Dict

EasingFunction = Callable[[float], float]


# ---------------------------------------------------------------------------
# Linear
# ---------------------------------------------------------------------------

def linear(t: float) -> float:
    return t


# ---------------------------------------------------------------------------
# Quadratic
# ---------------------------------------------------------------------------

def ease_in_quad(t: float) -> float:
    return t * t


def ease_out_quad(t: float) -> float:
    return t * (2 - t)


def ease_in_out_quad(t: float) -> float:
    if t < 0.5:
        return 2 * t * t
    return -1 + (4 - 2 * t) * t


# ---------------------------------------------------------------------------
# Cubic
# ---------------------------------------------------------------------------

def ease_in_cubic(t: float) -> float:
    return t * t * t


def ease_out_cubic(t: float) -> float:
    t1 = t - 1
    return t1 * t1 * t1 + 1


def ease_in_out_cubic(t: float) -> float:
    if t < 0.5:
        return 4 * t * t * t
    t1 = 2 * t - 2
    return 0.5 * t1 * t1 * t1 + 1


# ---------------------------------------------------------------------------
# Quartic
# ---------------------------------------------------------------------------

def ease_in_quart(t: float) -> float:
    return t * t * t * t


def ease_out_quart(t: float) -> float:
    t1 = t - 1
    return 1 - t1 * t1 * t1 * t1


def ease_in_out_quart(t: float) -> float:
    if t < 0.5:
        return 8 * t * t * t * t
    t1 = t - 1
    return 1 - 8 * t1 * t1 * t1 * t1


# ---------------------------------------------------------------------------
# Quintic
# ---------------------------------------------------------------------------

def ease_in_quint(t: float) -> float:
    return t * t * t * t * t


def ease_out_quint(t: float) -> float:
    t1 = t - 1
    return 1 + t1 * t1 * t1 * t1 * t1


def ease_in_out_quint(t: float) -> float:
    if t < 0.5:
        return 16 * t * t * t * t * t
    t1 = 2 * t - 2
    return 0.5 * t1 * t1 * t1 * t1 * t1 + 1


# ---------------------------------------------------------------------------
# Sine
# ---------------------------------------------------------------------------

def ease_in_sine(t: float) -> float:
    return 1 - math.cos(t * math.pi / 2)


def ease_out_sine(t: float) -> float:
    return math.sin(t * math.pi / 2)


def ease_in_out_sine(t: float) -> float:
    return -(math.cos(math.pi * t) - 1) / 2


# ---------------------------------------------------------------------------
# Exponential
# ---------------------------------------------------------------------------

def ease_in_expo(t: float) -> float:
    if t == 0:
        return 0
    return pow(2, 10 * (t - 1))


def ease_out_expo(t: float) -> float:
    if t == 1:
        return 1
    return 1 - pow(2, -10 * t)


def ease_in_out_expo(t: float) -> float:
    if t == 0:
        return 0
    if t == 1:
        return 1
    if t < 0.5:
        return 0.5 * pow(2, 20 * t - 10)
    return 1 - 0.5 * pow(2, -20 * t + 10)


# ---------------------------------------------------------------------------
# Circular
# ---------------------------------------------------------------------------

def ease_in_circ(t: float) -> float:
    return 1 - math.sqrt(1 - t * t)


def ease_out_circ(t: float) -> float:
    return math.sqrt(1 - (t - 1) * (t - 1))


def ease_in_out_circ(t: float) -> float:
    if t < 0.5:
        return 0.5 * (1 - math.sqrt(1 - 4 * t * t))
    return 0.5 * (math.sqrt(1 - (2 * t - 2) * (2 * t - 2)) + 1)


# ---------------------------------------------------------------------------
# Elastic
# ---------------------------------------------------------------------------

def ease_in_elastic(t: float) -> float:
    if t == 0:
        return 0
    if t == 1:
        return 1
    return -pow(2, 10 * t - 10) * math.sin((t * 10 - 10.75) * (2 * math.pi) / 3)


def ease_out_elastic(t: float) -> float:
    if t == 0:
        return 0
    if t == 1:
        return 1
    return pow(2, -10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi) / 3) + 1


def ease_in_out_elastic(t: float) -> float:
    if t == 0:
        return 0
    if t == 1:
        return 1
    if t < 0.5:
        return -(pow(2, 20 * t - 10) * math.sin((20 * t - 11.125) * (2 * math.pi) / 4.5)) / 2
    return (pow(2, -20 * t + 10) * math.sin((20 * t - 11.125) * (2 * math.pi) / 4.5)) / 2 + 1


# ---------------------------------------------------------------------------
# Back
# ---------------------------------------------------------------------------

_C1 = 1.70158
_C2 = _C1 * 1.525
_C3 = _C1 + 1


def ease_in_back(t: float) -> float:
    return _C3 * t * t * t - _C1 * t * t


def ease_out_back(t: float) -> float:
    t1 = t - 1
    return 1 + _C3 * t1 * t1 * t1 + _C1 * t1 * t1


def ease_in_out_back(t: float) -> float:
    if t < 0.5:
        return (pow(2 * t, 2) * ((_C2 + 1) * 2 * t - _C2)) / 2
    return (pow(2 * t - 2, 2) * ((_C2 + 1) * (2 * t - 2) + _C2) + 2) / 2


# ---------------------------------------------------------------------------
# Bounce
# ---------------------------------------------------------------------------

def _bounce_out(t: float) -> float:
    if t < 1 / 2.75:
        return 7.5625 * t * t
    elif t < 2 / 2.75:
        t -= 1.5 / 2.75
        return 7.5625 * t * t + 0.75
    elif t < 2.5 / 2.75:
        t -= 2.25 / 2.75
        return 7.5625 * t * t + 0.9375
    else:
        t -= 2.625 / 2.75
        return 7.5625 * t * t + 0.984375


def ease_in_bounce(t: float) -> float:
    return 1 - _bounce_out(1 - t)


def ease_out_bounce(t: float) -> float:
    return _bounce_out(t)


def ease_in_out_bounce(t: float) -> float:
    if t < 0.5:
        return (1 - _bounce_out(1 - 2 * t)) / 2
    return (1 + _bounce_out(2 * t - 1)) / 2


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

EASING_FUNCTIONS: Dict[str, EasingFunction] = {
    "linear": linear,
    "ease_in_quad": ease_in_quad,
    "ease_out_quad": ease_out_quad,
    "ease_in_out_quad": ease_in_out_quad,
    "ease_in_cubic": ease_in_cubic,
    "ease_out_cubic": ease_out_cubic,
    "ease_in_out_cubic": ease_in_out_cubic,
    "ease_in_quart": ease_in_quart,
    "ease_out_quart": ease_out_quart,
    "ease_in_out_quart": ease_in_out_quart,
    "ease_in_quint": ease_in_quint,
    "ease_out_quint": ease_out_quint,
    "ease_in_out_quint": ease_in_out_quint,
    "ease_in_sine": ease_in_sine,
    "ease_out_sine": ease_out_sine,
    "ease_in_out_sine": ease_in_out_sine,
    "ease_in_expo": ease_in_expo,
    "ease_out_expo": ease_out_expo,
    "ease_in_out_expo": ease_in_out_expo,
    "ease_in_circ": ease_in_circ,
    "ease_out_circ": ease_out_circ,
    "ease_in_out_circ": ease_in_out_circ,
    "ease_in_elastic": ease_in_elastic,
    "ease_out_elastic": ease_out_elastic,
    "ease_in_out_elastic": ease_in_out_elastic,
    "ease_in_back": ease_in_back,
    "ease_out_back": ease_out_back,
    "ease_in_out_back": ease_in_out_back,
    "ease_in_bounce": ease_in_bounce,
    "ease_out_bounce": ease_out_bounce,
    "ease_in_out_bounce": ease_in_out_bounce,
}


def get_easing_function(name: str) -> EasingFunction:
    """Get an easing function by name.

    Supports both underscore format (ease_in_quad) and CSS format (ease-in-quad).
    """
    # Normalize CSS-style names to underscore format
    normalized = name.replace("-", "_").lower()
    if normalized in EASING_FUNCTIONS:
        return EASING_FUNCTIONS[normalized]
    raise ValueError(f"Unknown easing function: {name!r}. "
                     f"Available: {', '.join(sorted(EASING_FUNCTIONS.keys()))}")


def list_easing_functions() -> list:
    """Return sorted list of available easing function names."""
    return sorted(EASING_FUNCTIONS.keys())
