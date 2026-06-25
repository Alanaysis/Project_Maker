"""
Utility functions for the Animation Engine.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional


def clamp(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Clamp a value to the given range."""
    return max(min_val, min(max_val, value))


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between two scalar values."""
    return a + (b - a) * t


def map_range(
    value: float,
    in_min: float,
    in_max: float,
    out_min: float,
    out_max: float,
) -> float:
    """Map a value from one range to another."""
    if in_max == in_min:
        return out_min
    return out_min + (value - in_min) * (out_max - out_min) / (in_max - in_min)


def normalize_time(
    elapsed: float,
    duration: float,
    direction: str = "normal",
    iteration: int = 0,
) -> float:
    """Compute normalized time t in [0, 1] considering direction.

    Args:
        elapsed: Elapsed time in current iteration.
        duration: Total duration of one iteration.
        direction: One of 'normal', 'reverse', 'alternate', 'alternate-reverse'.
        iteration: Current iteration index (0-based).

    Returns:
        Normalized time t in [0, 1].
    """
    if duration <= 0:
        return 1.0

    t = clamp(elapsed / duration)

    if direction == "normal":
        return t
    elif direction == "reverse":
        return 1.0 - t
    elif direction == "alternate":
        if iteration % 2 == 0:
            return t
        else:
            return 1.0 - t
    elif direction == "alternate-reverse":
        if iteration % 2 == 0:
            return 1.0 - t
        else:
            return t
    else:
        raise ValueError(f"Unknown direction: {direction!r}")


def merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two dicts, with override values taking precedence."""
    result = dict(base)
    result.update(override)
    return result


class Timer:
    """Simple high-resolution timer for animation timing."""

    def __init__(self):
        self._start_time: Optional[float] = None
        self._paused_time: float = 0.0
        self._pause_start: Optional[float] = None
        self._paused: bool = False

    def start(self) -> None:
        """Start or restart the timer."""
        self._start_time = time.perf_counter()
        self._paused_time = 0.0
        self._pause_start = None
        self._paused = False

    def pause(self) -> None:
        """Pause the timer."""
        if not self._paused and self._start_time is not None:
            self._pause_start = time.perf_counter()
            self._paused = True

    def resume(self) -> None:
        """Resume the timer."""
        if self._paused and self._pause_start is not None:
            self._paused_time += time.perf_counter() - self._pause_start
            self._pause_start = None
            self._paused = False

    def elapsed(self) -> float:
        """Get elapsed time in seconds (excluding paused periods)."""
        if self._start_time is None:
            return 0.0
        if self._paused:
            return self._pause_start - self._start_time - self._paused_time
        return time.perf_counter() - self._start_time - self._paused_time

    @property
    def is_paused(self) -> bool:
        return self._paused

    @property
    def is_running(self) -> bool:
        return self._start_time is not None and not self._paused


class FrameRateCounter:
    """Tracks frames per second."""

    def __init__(self, sample_size: int = 60):
        self._sample_size = sample_size
        self._frame_times: list = []
        self._last_time: Optional[float] = None

    def frame(self) -> None:
        """Record a frame."""
        now = time.perf_counter()
        if self._last_time is not None:
            dt = now - self._last_time
            self._frame_times.append(dt)
            if len(self._frame_times) > self._sample_size:
                self._frame_times.pop(0)
        self._last_time = now

    @property
    def fps(self) -> float:
        """Get current frames per second."""
        if len(self._frame_times) < 2:
            return 0.0
        avg_dt = sum(self._frame_times) / len(self._frame_times)
        return 1.0 / avg_dt if avg_dt > 0 else 0.0

    @property
    def frame_time(self) -> float:
        """Get average frame time in seconds."""
        if not self._frame_times:
            return 0.0
        return sum(self._frame_times) / len(self._frame_times)

    @property
    def frame_time_ms(self) -> float:
        """Get average frame time in milliseconds."""
        return self.frame_time * 1000.0


def color_to_tuple(color) -> tuple:
    """Convert a Color object or tuple to a standard tuple."""
    if hasattr(color, "to_tuple"):
        return color.to_tuple()
    return tuple(color)
