"""
Keyframe animation system.

Supports multi-step animations with per-keyframe easing,
direction control, and iteration.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Set

from .easing import EasingFunction, get_easing_function, linear
from .types import AnimationConfig, Keyframe, lerp_value
from .utils import clamp, normalize_time


class KeyframeAnimation:
    """A keyframe-based animation that interpolates between defined states.

    Example::

        anim = KeyframeAnimation(AnimationConfig(
            keyframes=[
                Keyframe(time=0.0, values={"x": 0, "opacity": 1.0}),
                Keyframe(time=0.5, values={"x": 100, "opacity": 0.5}),
                Keyframe(time=1.0, values={"x": 200, "opacity": 1.0}),
            ],
            duration=2.0,
            iterations=3,
            direction="alternate",
        ))
        anim.start()
        # In update loop:
        anim.update(delta_time)
        current_values = anim.current_values
    """

    def __init__(self, config: AnimationConfig):
        if not config.keyframes:
            raise ValueError("At least one keyframe is required")

        # Sort keyframes by time
        self._keyframes = sorted(config.keyframes, key=lambda kf: kf.time)
        self._duration = config.duration
        self._delay = config.delay
        self._iterations = config.iterations  # 0 = infinite
        self._direction = config.direction
        self._fill_mode = config.fill_mode
        self._default_easing_name = config.easing or "linear"
        self._default_easing: EasingFunction = get_easing_function(
            self._default_easing_name
        )
        self._on_update = config.on_update
        self._on_complete = config.on_complete

        # State
        self._elapsed: float = 0.0
        self._current_iteration: int = 0
        self._running: bool = False
        self._finished: bool = False
        self._started: bool = False
        self._current_values: Dict[str, Any] = {}

        # Collect all animated property names
        self._properties: Set[str] = set()
        for kf in self._keyframes:
            self._properties.update(kf.values.keys())

        # Pre-parse per-segment easing functions
        self._segment_easings: List[EasingFunction] = []
        for i in range(len(self._keyframes) - 1):
            kf = self._keyframes[i]
            if kf.easing:
                self._segment_easings.append(get_easing_function(kf.easing))
            else:
                self._segment_easings.append(self._default_easing)

        # Initialize values from first keyframe
        self._init_values()

    def _init_values(self) -> None:
        """Initialize current values from the first keyframe."""
        if self._keyframes:
            self._current_values = dict(self._keyframes[0].values)

    @property
    def current_values(self) -> Dict[str, Any]:
        """Get the current interpolated property values."""
        return dict(self._current_values)

    @property
    def progress(self) -> float:
        """Get overall progress [0, 1] across all iterations."""
        if self._iterations == 0:
            # Infinite: just show current iteration progress
            if self._duration <= 0:
                return 0.0
            return clamp(self._elapsed / self._duration)
        total = self._duration * self._iterations
        if total <= 0:
            return 1.0
        return clamp(self._elapsed / total)

    @property
    def iteration_progress(self) -> float:
        """Get progress within the current iteration [0, 1]."""
        if self._duration <= 0:
            return 1.0
        return clamp(self._elapsed / self._duration)

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def is_finished(self) -> bool:
        return self._finished

    @property
    def current_iteration(self) -> int:
        return self._current_iteration

    def start(self) -> None:
        """Start or restart the animation."""
        self._elapsed = 0.0
        self._current_iteration = 0
        self._running = True
        self._finished = False
        self._started = True
        self._init_values()

    def stop(self) -> None:
        """Stop the animation."""
        self._running = False
        self._finished = True

    def pause(self) -> None:
        """Pause the animation."""
        self._running = False

    def resume(self) -> None:
        """Resume a paused animation."""
        if self._started and not self._finished:
            self._running = True

    def reset(self) -> None:
        """Reset the animation to its initial state."""
        self._elapsed = 0.0
        self._current_iteration = 0
        self._running = False
        self._finished = False
        self._started = False
        self._init_values()

    def update(self, dt: float) -> Dict[str, Any]:
        """Advance the animation by dt seconds.

        Args:
            dt: Delta time in seconds.

        Returns:
            Current interpolated values.
        """
        if not self._running or self._finished:
            return self._current_values

        self._elapsed += dt

        # Handle delay
        if self._elapsed < self._delay:
            return self._current_values

        effective_elapsed = self._elapsed - self._delay

        # Determine current iteration
        if self._duration > 0:
            self._current_iteration = int(effective_elapsed / self._duration)

        # Check completion
        if self._iterations > 0 and self._current_iteration >= self._iterations:
            self._current_iteration = self._iterations - 1
            # Interpolate at final state before completing
            t = normalize_time(
                self._duration,
                self._duration,
                self._direction,
                self._current_iteration,
            )
            self._interpolate(t)
            self._running = False
            self._finished = True
            if self._on_update:
                self._on_update(self._current_values)
            if self._on_complete:
                self._on_complete()
            return self._current_values

        # Calculate time within current iteration
        if self._duration > 0:
            iteration_elapsed = effective_elapsed % self._duration
        else:
            iteration_elapsed = 0

        # Apply direction
        t = normalize_time(
            iteration_elapsed if self._duration > 0 else 0,
            self._duration,
            self._direction,
            self._current_iteration,
        )

        # Interpolate values
        self._interpolate(t)

        if self._on_update:
            self._on_update(self._current_values)

        return self._current_values

    def _interpolate(self, t: float) -> None:
        """Interpolate all properties at normalized time t."""
        kfs = self._keyframes

        if len(kfs) == 1:
            self._current_values = dict(kfs[0].values)
            return

        # Find the two surrounding keyframes
        if t <= kfs[0].time:
            self._current_values = dict(kfs[0].values)
            return
        if t >= kfs[-1].time:
            self._current_values = dict(kfs[-1].values)
            return

        # Find segment
        seg_idx = 0
        for i in range(len(kfs) - 1):
            if kfs[i].time <= t <= kfs[i + 1].time:
                seg_idx = i
                break

        kf_a = kfs[seg_idx]
        kf_b = kfs[seg_idx + 1]

        # Local t within segment
        seg_duration = kf_b.time - kf_a.time
        if seg_duration <= 0:
            local_t = 1.0
        else:
            local_t = clamp((t - kf_a.time) / seg_duration)

        # Apply segment easing
        easing_fn = self._segment_easings[seg_idx]
        eased_t = easing_fn(local_t)

        # Interpolate each property
        for prop in self._properties:
            val_a = kf_a.values.get(prop)
            val_b = kf_b.values.get(prop)

            if val_a is not None and val_b is not None:
                self._current_values[prop] = lerp_value(val_a, val_b, eased_t)
            elif val_b is not None:
                self._current_values[prop] = val_b
            elif val_a is not None:
                self._current_values[prop] = val_a

    def _apply_final_state(self) -> None:
        """Apply fill mode to determine final state."""
        if self._fill_mode in ("forwards", "both"):
            # Keep the last computed values
            pass
        elif self._fill_mode == "none":
            self._init_values()
        # "backwards" keeps initial values (already set)

    def seek(self, time: float) -> Dict[str, Any]:
        """Seek to a specific time and return interpolated values.

        Args:
            time: Time in seconds (will be normalized to iterations).

        Returns:
            Interpolated values at the given time.
        """
        if self._duration <= 0:
            t = 1.0
        else:
            t = clamp(time / self._duration)

        t = normalize_time(
            time % self._duration if self._duration > 0 else 0,
            self._duration,
            self._direction,
            int(time / self._duration) if self._duration > 0 else 0,
        )

        self._interpolate(t)
        return self._current_values

    def evaluate_at(self, t: float) -> Dict[str, Any]:
        """Evaluate animation at normalized time t in [0, 1].

        Args:
            t: Normalized time.

        Returns:
            Interpolated values.
        """
        t = clamp(t)
        self._interpolate(t)
        return dict(self._current_values)
