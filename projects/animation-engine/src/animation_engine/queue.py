"""
Animation queue for sequential animation execution.

Provides a way to chain animations, waits, and callbacks
in a sequential pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from .keyframe import KeyframeAnimation
from .tween import Tween
from .types import AnimationConfig, Keyframe, TweenConfig


@dataclass
class QueueItem:
    """An item in the animation queue."""
    kind: str  # "animation", "tween", "wait", "callback"
    data: Any = None
    duration: float = 0.0


class AnimationQueue:
    """Sequential animation queue with blocking execution.

    Items are processed one at a time. Each animation must complete
    before the next one starts.

    Example::

        queue = AnimationQueue()

        queue.animate(AnimationConfig(
            keyframes=[...],
            duration=1.0,
        ))
        queue.wait(0.5)
        queue.call(lambda: print("mid-point"))
        queue.animate(AnimationConfig(
            keyframes=[...],
            duration=0.8,
        ))
        queue.call(lambda: print("done!"))

        # In update loop:
        queue.update(dt)
    """

    def __init__(self):
        self._items: List[QueueItem] = []
        self._current_index: int = 0
        self._current_animation: Optional[Any] = None
        self._wait_remaining: float = 0.0
        self._running: bool = False
        self._finished: bool = False
        self._loop: bool = False
        self._on_complete: Optional[Callable] = None

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def is_finished(self) -> bool:
        return self._finished

    @property
    def progress(self) -> float:
        """Overall queue progress [0, 1]."""
        if not self._items:
            return 1.0
        return self._current_index / len(self._items)

    @property
    def current_step(self) -> int:
        return self._current_index

    @property
    def total_steps(self) -> int:
        return len(self._items)

    def animate(self, config: AnimationConfig) -> AnimationQueue:
        """Add a keyframe animation to the queue.

        Returns self for chaining.
        """
        self._items.append(QueueItem(kind="animation", data=config, duration=config.duration))
        return self

    def tween(self, config: TweenConfig) -> AnimationQueue:
        """Add a tween to the queue.

        Returns self for chaining.
        """
        self._items.append(QueueItem(kind="tween", data=config, duration=config.duration))
        return self

    def wait(self, duration: float) -> AnimationQueue:
        """Add a wait/delay to the queue.

        Returns self for chaining.
        """
        self._items.append(QueueItem(kind="wait", duration=duration))
        return self

    def call(self, callback: Callable) -> AnimationQueue:
        """Add a callback to the queue.

        Returns self for chaining.
        """
        self._items.append(QueueItem(kind="callback", data=callback))
        return self

    def on_complete(self, callback: Callable) -> AnimationQueue:
        """Set callback for when entire queue completes.

        Returns self for chaining.
        """
        self._on_complete = callback
        return self

    def loop(self, enable: bool = True) -> AnimationQueue:
        """Enable/disable looping.

        Returns self for chaining.
        """
        self._loop = enable
        return self

    def start(self) -> None:
        """Start processing the queue."""
        self._current_index = 0
        self._running = True
        self._finished = False
        self._current_animation = None
        self._wait_remaining = 0.0
        self._start_current_item()

    def stop(self) -> None:
        """Stop the queue."""
        self._running = False
        self._finished = True
        self._current_animation = None

    def pause(self) -> None:
        """Pause the queue."""
        self._running = False

    def resume(self) -> None:
        """Resume the queue."""
        if not self._finished:
            self._running = True

    def reset(self) -> None:
        """Reset the queue to the beginning."""
        self._current_index = 0
        self._running = False
        self._finished = False
        self._current_animation = None
        self._wait_remaining = 0.0

    def clear(self) -> None:
        """Clear all items from the queue."""
        self._items.clear()
        self.reset()

    def update(self, dt: float) -> None:
        """Advance the queue by dt seconds."""
        if not self._running or self._finished:
            return

        # Process items. Callbacks are synchronous; other items block.
        # Limit iterations to prevent infinite loops on callback-only queues.
        max_iterations = len(self._items) + 1
        iterations = 0

        while self._running and not self._finished and iterations < max_iterations:
            iterations += 1

            if self._current_index >= len(self._items):
                self._finish()
                return

            item = self._items[self._current_index]

            if item.kind == "callback":
                callback = item.data
                callback()
                self._advance()
            elif item.kind == "wait":
                self._wait_remaining -= dt
                dt = 0  # Only apply dt once
                if self._wait_remaining <= 0:
                    self._advance()
                else:
                    break  # Wait not done yet
            elif item.kind in ("animation", "tween"):
                if self._current_animation is not None:
                    self._current_animation.update(dt)
                    dt = 0  # Only apply dt once
                    if self._current_animation.is_finished:
                        self._advance()
                    else:
                        break  # Animation not done yet
                else:
                    break
            else:
                break

    def _start_current_item(self) -> None:
        """Initialize the current queue item."""
        if self._current_index >= len(self._items):
            self._finish()
            return

        item = self._items[self._current_index]

        if item.kind == "wait":
            self._wait_remaining = item.duration
            self._current_animation = None
        elif item.kind == "callback":
            self._current_animation = None
        elif item.kind == "animation":
            anim = KeyframeAnimation(item.data)
            anim.start()
            self._current_animation = anim
        elif item.kind == "tween":
            tw = Tween(item.data)
            tw.start()
            self._current_animation = tw

    def _advance(self) -> None:
        """Move to the next item."""
        self._current_index += 1
        self._current_animation = None

        if self._current_index >= len(self._items):
            if self._loop:
                self._current_index = 0
                self._start_current_item()
            else:
                self._finish()
        else:
            self._start_current_item()

    def _finish(self) -> None:
        """Handle queue completion."""
        self._running = False
        self._finished = True
        self._current_animation = None
        if self._on_complete:
            self._on_complete()

    def __len__(self) -> int:
        return len(self._items)

    def __repr__(self) -> str:
        return (
            f"AnimationQueue(steps={len(self._items)}, "
            f"current={self._current_index}, running={self._running})"
        )
