"""Tests for animation queue."""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from animation_engine.queue import AnimationQueue
from animation_engine.types import AnimationConfig, Keyframe, TweenConfig


class TestAnimationQueue:
    def test_create(self):
        q = AnimationQueue()
        assert len(q) == 0
        assert not q.is_running

    def test_wait(self):
        q = AnimationQueue()
        q.wait(1.0)
        assert len(q) == 1

    def test_callback(self):
        results = []
        q = AnimationQueue()
        q.call(lambda: results.append("done"))
        q.start()
        q.update(0)
        assert results == ["done"]

    def test_animate(self):
        q = AnimationQueue()
        q.animate(AnimationConfig(
            keyframes=[
                Keyframe(time=0.0, values={"x": 0}),
                Keyframe(time=1.0, values={"x": 100}),
            ],
            duration=1.0,
        ))
        assert len(q) == 1

    def test_tween(self):
        q = AnimationQueue()
        q.tween(TweenConfig(
            from_values={"x": 0}, to_values={"x": 100}, duration=1.0
        ))
        assert len(q) == 1

    def test_sequential_execution(self):
        order = []
        q = AnimationQueue()
        q.call(lambda: order.append(1))
        q.call(lambda: order.append(2))
        q.call(lambda: order.append(3))
        q.start()
        q.update(0)
        assert order == [1, 2, 3]

    def test_wait_then_callback(self):
        results = []
        q = AnimationQueue()
        q.wait(0.5)
        q.call(lambda: results.append("after_wait"))
        q.start()

        q.update(0.3)
        assert len(results) == 0

        q.update(0.3)
        assert results == ["after_wait"]

    def test_animation_then_wait(self):
        results = []
        q = AnimationQueue()
        q.animate(AnimationConfig(
            keyframes=[
                Keyframe(time=0.0, values={"x": 0}),
                Keyframe(time=1.0, values={"x": 100}),
            ],
            duration=1.0,
        ))
        q.wait(0.5)
        q.call(lambda: results.append("done"))
        q.start()

        q.update(1.5)  # Animation + wait
        assert len(results) == 0

        q.update(0.5)  # Wait finishes
        assert results == ["done"]

    def test_on_complete(self):
        completed = []
        q = AnimationQueue()
        q.call(lambda: None)
        q.on_complete(lambda: completed.append(True))
        q.start()
        q.update(0)
        assert len(completed) == 1

    def test_loop(self):
        count = []
        q = AnimationQueue()
        q.loop(True)
        q.call(lambda: count.append(1))
        q.start()

        # Process multiple times - should loop
        for _ in range(5):
            q.update(0)

        assert len(count) >= 5

    def test_stop(self):
        q = AnimationQueue()
        q.wait(1.0)
        q.start()
        q.stop()
        assert q.is_finished
        q.update(1.0)  # Should not advance

    def test_pause_resume(self):
        q = AnimationQueue()
        q.wait(1.0)
        q.start()

        q.update(0.3)
        q.pause()
        q.update(1.0)  # Should not advance
        assert not q.is_finished

        q.resume()
        q.update(0.8)
        assert q.is_finished

    def test_reset(self):
        q = AnimationQueue()
        q.wait(1.0)
        q.start()
        q.update(1.5)
        assert q.is_finished

        q.reset()
        assert not q.is_running
        assert not q.is_finished

    def test_clear(self):
        q = AnimationQueue()
        q.wait(1.0)
        q.call(lambda: None)
        q.clear()
        assert len(q) == 0

    def test_progress(self):
        q = AnimationQueue()
        q.wait(1.0)
        q.wait(1.0)
        q.wait(1.0)
        q.start()

        q.update(1.5)  # First wait done
        assert q.progress == pytest.approx(1 / 3)

    def test_chaining(self):
        q = AnimationQueue()
        q.wait(0.5).wait(0.5).call(lambda: None)
        assert len(q) == 3

    def test_repr(self):
        q = AnimationQueue()
        q.wait(1.0)
        assert "AnimationQueue" in repr(q)

    def test_empty_queue_finishes(self):
        q = AnimationQueue()
        q.start()
        q.update(0)
        assert q.is_finished


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
