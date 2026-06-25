"""
Tween animation system for simple property interpolation.

Tweens provide a simple way to animate numeric values between
a start and end state with easing.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from .easing import EasingFunction, get_easing_function, linear
from .types import TweenConfig
from .utils import clamp, lerp


class Tween:
    """A simple tween that interpolates numeric properties.

    Example::

        tween = Tween(TweenConfig(
            from_values={"x": 0, "y": 0, "alpha": 1.0},
            to_values={"x": 200, "y": 100, "alpha": 0.0},
            duration=1.5,
            easing="ease_out_cubic",
            on_update=lambda vals: print(f"Position: {vals['x']:.1f}, {vals['y']:.1f}"),
            on_complete=lambda: print("Done!"),
        ))
        tween.start()
        # In update loop:
        tween.update(delta_time)
    """

    def __init__(self, config: TweenConfig):
        self._from = dict(config.from_values)
        self._to = dict(config.to_values)
        self._duration = config.duration
        self._delay = config.delay
        self._easing: EasingFunction = get_easing_function(config.easing)
        self._on_update = config.on_update
        self._on_complete = config.on_complete

        # Validate that all keys match
        if set(self._from.keys()) != set(self._to.keys()):
            raise ValueError(
                f"from_values and to_values must have the same keys. "
                f"from: {set(self._from.keys())}, to: {set(self._to.keys())}"
            )

        # State
        self._elapsed: float = 0.0
        self._running: bool = False
        self._finished: bool = False
        self._started: bool = False
        self._current_values: Dict[str, float] = dict(self._from)

        # Chaining support
        self._next_tweens: List[Tween] = []
        self._on_start_callback: Optional[Callable] = None
        self._started_called: bool = False

    @property
    def current_values(self) -> Dict[str, float]:
        return dict(self._current_values)

    @property
    def progress(self) -> float:
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
    def remaining(self) -> float:
        """Get remaining time in seconds."""
        if self._finished:
            return 0.0
        return max(0, self._duration - self._elapsed)

    def start(self) -> Tween:
        """Start the tween. Returns self for chaining."""
        self._elapsed = 0.0
        self._running = True
        self._finished = False
        self._started = True
        self._started_called = False
        self._current_values = dict(self._from)
        return self

    def stop(self) -> None:
        """Stop the tween."""
        self._running = False
        self._finished = True

    def pause(self) -> None:
        """Pause the tween."""
        self._running = False

    def resume(self) -> None:
        """Resume a paused tween."""
        if self._started and not self._finished:
            self._running = True

    def reset(self) -> None:
        """Reset the tween to its initial state."""
        self._elapsed = 0.0
        self._running = False
        self._finished = False
        self._started = False
        self._started_called = False
        self._current_values = dict(self._from)

    def on_start(self, callback: Callable) -> Tween:
        """Set a callback for when the tween starts. Returns self for chaining."""
        self._on_start_callback = callback
        return self

    def then(self, next_tween: Tween) -> Tween:
        """Chain another tween to run after this one completes.

        Returns the next tween for further chaining.
        """
        self._next_tweens.append(next_tween)
        return next_tween

    def update(self, dt: float) -> Dict[str, float]:
        """Advance the tween by dt seconds.

        Returns current interpolated values.
        """
        if not self._running or self._finished:
            return self._current_values

        # Fire start callback once
        if not self._started_called and self._on_start_callback:
            self._on_start_callback()
            self._started_called = True

        self._elapsed += dt

        # Handle delay
        if self._elapsed < self._delay:
            return self._current_values

        effective_elapsed = self._elapsed - self._delay

        if self._duration <= 0:
            t = 1.0
        else:
            t = clamp(effective_elapsed / self._duration)

        # Apply easing
        eased_t = self._easing(t)

        # Interpolate
        for key in self._from:
            self._current_values[key] = lerp(self._from[key], self._to[key], eased_t)

        if self._on_update:
            self._on_update(self._current_values)

        # Check completion
        if t >= 1.0:
            self._running = False
            self._finished = True
            if self._on_complete:
                self._on_complete()

        return self._current_values

    def update_chained(self, dt: float) -> List[Tween]:
        """Update and return any newly-activated chained tweens."""
        self.update(dt)
        newly_started = []
        if self._finished:
            for tw in self._next_tweens:
                tw.start()
                newly_started.append(tw)
            self._next_tweens.clear()
        return newly_started

    def seek(self, t: float) -> Dict[str, float]:
        """Seek to normalized time t in [0, 1]."""
        t = clamp(t)
        eased_t = self._easing(t)
        for key in self._from:
            self._current_values[key] = lerp(self._from[key], self._to[key], eased_t)
        return self._current_values

    @staticmethod
    def sequence(*tweens: Tween) -> List[Tween]:
        """Chain multiple tweens in sequence.

        Returns the list of tweens with chaining set up.
        """
        for i in range(len(tweens) - 1):
            tweens[i].then(tweens[i + 1])
        return list(tweens)

    @staticmethod
    def parallel(*tweens: Tween) -> List[Tween]:
        """Start multiple tweens simultaneously.

        Returns the list of tweens (for convenience).
        """
        for tw in tweens:
            tw.start()
        return list(tweens)
