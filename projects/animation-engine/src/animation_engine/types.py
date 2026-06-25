"""
Type definitions for the Animation Engine.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

# Easing function type: takes normalized time t in [0,1], returns eased value
EasingFunction = Callable[[float], float]
# Update callback type
UpdateCallback = Callable[[Dict[str, Any]], None]
# Complete callback type
CompleteCallback = Callable[[], None]


@dataclass
class Vector3:
    """3D vector for positions, rotations, scales."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def __add__(self, other: Vector3) -> Vector3:
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: Vector3) -> Vector3:
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> Vector3:
        return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)

    def __rmul__(self, scalar: float) -> Vector3:
        return self.__mul__(scalar)

    def length(self) -> float:
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)

    def normalized(self) -> Vector3:
        ln = self.length()
        if ln == 0:
            return Vector3(0, 0, 0)
        return Vector3(self.x / ln, self.y / ln, self.z / ln)

    def dot(self, other: Vector3) -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other: Vector3) -> Vector3:
        return Vector3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )

    def to_tuple(self) -> Tuple[float, float, float]:
        return (self.x, self.y, self.z)

    def copy(self) -> Vector3:
        return Vector3(self.x, self.y, self.z)

    @staticmethod
    def lerp(a: Vector3, b: Vector3, t: float) -> Vector3:
        """Linear interpolation between two vectors."""
        return Vector3(
            a.x + (b.x - a.x) * t,
            a.y + (b.y - a.y) * t,
            a.z + (b.z - a.z) * t,
        )


@dataclass
class Color:
    """RGBA color with values in [0, 1]."""
    r: float = 1.0
    g: float = 1.0
    b: float = 1.0
    a: float = 1.0

    def to_tuple(self) -> Tuple[float, float, float, float]:
        return (self.r, self.g, self.b, self.a)

    def to_hex(self) -> str:
        ri = max(0, min(255, int(self.r * 255)))
        gi = max(0, min(255, int(self.g * 255)))
        bi = max(0, min(255, int(self.b * 255)))
        return f"#{ri:02x}{gi:02x}{bi:02x}"

    def copy(self) -> Color:
        return Color(self.r, self.g, self.b, self.a)

    @staticmethod
    def lerp(a: Color, b: Color, t: float) -> Color:
        """Linear interpolation between two colors."""
        return Color(
            a.r + (b.r - a.r) * t,
            a.g + (b.g - a.g) * t,
            a.b + (b.b - a.b) * t,
            a.a + (b.a - a.a) * t,
        )

    @staticmethod
    def from_hex(hex_str: str) -> Color:
        """Create color from hex string like '#ff0000' or 'ff0000'."""
        hex_str = hex_str.lstrip("#")
        r = int(hex_str[0:2], 16) / 255.0
        g = int(hex_str[2:4], 16) / 255.0
        b = int(hex_str[4:6], 16) / 255.0
        return Color(r, g, b, 1.0)


@dataclass
class Keyframe:
    """A single keyframe in an animation."""
    time: float  # Normalized time [0, 1]
    values: Dict[str, Any]  # Property values at this keyframe
    easing: Optional[str] = None  # Easing function name to next keyframe

    def __post_init__(self):
        if not 0.0 <= self.time <= 1.0:
            raise ValueError(f"Keyframe time must be in [0, 1], got {self.time}")


@dataclass
class AnimationConfig:
    """Configuration for a keyframe animation."""
    keyframes: List[Keyframe]
    duration: float = 1.0  # Duration in seconds
    delay: float = 0.0  # Delay before starting
    iterations: int = 1  # Number of iterations (0 = infinite)
    direction: str = "normal"  # normal, reverse, alternate, alternate-reverse
    easing: Optional[str] = None  # Default easing function name
    fill_mode: str = "none"  # none, forwards, backwards, both
    on_update: Optional[UpdateCallback] = None
    on_complete: Optional[CompleteCallback] = None


@dataclass
class TweenConfig:
    """Configuration for a tween animation."""
    from_values: Dict[str, float]
    to_values: Dict[str, float]
    duration: float = 1.0
    delay: float = 0.0
    easing: str = "linear"
    on_update: Optional[UpdateCallback] = None
    on_complete: Optional[CompleteCallback] = None


def lerp_value(a: Any, b: Any, t: float) -> Any:
    """Interpolate between two values based on their type."""
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a + (b - a) * t
    elif isinstance(a, Vector3) and isinstance(b, Vector3):
        return Vector3.lerp(a, b, t)
    elif isinstance(a, Color) and isinstance(b, Color):
        return Color.lerp(a, b, t)
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        return [lerp_value(ai, bi, t) for ai, bi in zip(a, b)]
    else:
        # Discrete interpolation: snap at t >= 0.5
        return a if t < 0.5 else b
