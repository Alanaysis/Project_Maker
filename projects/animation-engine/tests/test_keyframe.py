"""Tests for keyframe animation."""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from animation_engine.keyframe import KeyframeAnimation
from animation_engine.types import AnimationConfig, Keyframe, Vector3, Color


class TestKeyframeAnimation:
    def test_create_simple(self):
        anim = KeyframeAnimation(AnimationConfig(
            keyframes=[
                Keyframe(time=0.0, values={"x": 0}),
                Keyframe(time=1.0, values={"x": 100}),
            ],
            duration=1.0,
        ))
        assert not anim.is_running
        assert not anim.is_finished

    def test_create_empty_keyframes(self):
        with pytest.raises(ValueError, match="At least one keyframe"):
            KeyframeAnimation(AnimationConfig(keyframes=[]))

    def test_single_keyframe(self):
        anim = KeyframeAnimation(AnimationConfig(
            keyframes=[Keyframe(time=0.0, values={"x": 42})],
            duration=1.0,
        ))
        anim.start()
        vals = anim.update(0.5)
        assert vals["x"] == 42

    def test_basic_interpolation(self):
        anim = KeyframeAnimation(AnimationConfig(
            keyframes=[
                Keyframe(time=0.0, values={"x": 0}),
                Keyframe(time=1.0, values={"x": 100}),
            ],
            duration=1.0,
        ))
        anim.start()

        vals = anim.update(0.25)
        assert vals["x"] == pytest.approx(25)

        vals = anim.update(0.25)
        assert vals["x"] == pytest.approx(50)

        vals = anim.update(0.25)
        assert vals["x"] == pytest.approx(75)

        vals = anim.update(0.24)
        assert vals["x"] == pytest.approx(99)

        vals = anim.update(0.01)
        assert vals["x"] == pytest.approx(100)

    def test_multi_keyframe(self):
        anim = KeyframeAnimation(AnimationConfig(
            keyframes=[
                Keyframe(time=0.0, values={"x": 0}),
                Keyframe(time=0.5, values={"x": 50}),
                Keyframe(time=1.0, values={"x": 0}),
            ],
            duration=2.0,
        ))
        anim.start()

        # At t=0.25 (quarter of 2s = 0.5s, normalized = 0.25)
        vals = anim.update(0.5)
        assert vals["x"] == pytest.approx(25)

        # At t=0.5 (half of 2s = 1s, normalized = 0.5)
        vals = anim.update(0.5)
        assert vals["x"] == pytest.approx(50)

    def test_easing_per_keyframe(self):
        anim = KeyframeAnimation(AnimationConfig(
            keyframes=[
                Keyframe(time=0.0, values={"x": 0}, easing="ease_in_quad"),
                Keyframe(time=1.0, values={"x": 100}),
            ],
            duration=1.0,
        ))
        anim.start()

        # With ease-in-quad, midpoint should be less than linear (25 vs 50)
        vals = anim.update(0.5)
        assert vals["x"] < 50  # Ease-in starts slow

    def test_iterations(self):
        anim = KeyframeAnimation(AnimationConfig(
            keyframes=[
                Keyframe(time=0.0, values={"x": 0}),
                Keyframe(time=1.0, values={"x": 100}),
            ],
            duration=1.0,
            iterations=2,
        ))
        anim.start()

        # First iteration
        anim.update(1.0)
        assert not anim.is_finished

        # Second iteration
        anim.update(1.0)
        assert anim.is_finished

    def test_infinite_iterations(self):
        anim = KeyframeAnimation(AnimationConfig(
            keyframes=[
                Keyframe(time=0.0, values={"x": 0}),
                Keyframe(time=1.0, values={"x": 100}),
            ],
            duration=1.0,
            iterations=0,  # infinite
        ))
        anim.start()

        for _ in range(10):
            anim.update(1.0)
            assert not anim.is_finished

    def test_direction_reverse(self):
        anim = KeyframeAnimation(AnimationConfig(
            keyframes=[
                Keyframe(time=0.0, values={"x": 0}),
                Keyframe(time=1.0, values={"x": 100}),
            ],
            duration=1.0,
            direction="reverse",
        ))
        anim.start()

        vals = anim.update(0.5)
        assert vals["x"] == pytest.approx(50)  # 100 - 50

        vals = anim.update(0.5)
        assert vals["x"] == pytest.approx(0)

    def test_direction_alternate(self):
        anim = KeyframeAnimation(AnimationConfig(
            keyframes=[
                Keyframe(time=0.0, values={"x": 0}),
                Keyframe(time=1.0, values={"x": 100}),
            ],
            duration=1.0,
            iterations=2,
            direction="alternate",
        ))
        anim.start()

        # First iteration: forward
        vals = anim.update(1.0)
        assert vals["x"] == pytest.approx(100)

        # Second iteration: reverse
        vals = anim.update(1.0)
        assert vals["x"] == pytest.approx(0)
        assert anim.is_finished

    def test_delay(self):
        anim = KeyframeAnimation(AnimationConfig(
            keyframes=[
                Keyframe(time=0.0, values={"x": 0}),
                Keyframe(time=1.0, values={"x": 100}),
            ],
            duration=1.0,
            delay=0.5,
        ))
        anim.start()

        # During delay, values shouldn't change
        vals = anim.update(0.3)
        assert vals["x"] == pytest.approx(0)

        # After delay
        vals = anim.update(0.5)
        assert vals["x"] > 0

    def test_callback(self):
        completed = []

        anim = KeyframeAnimation(AnimationConfig(
            keyframes=[
                Keyframe(time=0.0, values={"x": 0}),
                Keyframe(time=1.0, values={"x": 100}),
            ],
            duration=1.0,
            on_complete=lambda: completed.append(True),
        ))
        anim.start()
        anim.update(1.5)
        assert len(completed) == 1

    def test_update_callback(self):
        updates = []

        anim = KeyframeAnimation(AnimationConfig(
            keyframes=[
                Keyframe(time=0.0, values={"x": 0}),
                Keyframe(time=1.0, values={"x": 100}),
            ],
            duration=1.0,
            on_update=lambda v: updates.append(v["x"]),
        ))
        anim.start()
        anim.update(0.5)
        assert len(updates) == 1

    def test_pause_resume(self):
        anim = KeyframeAnimation(AnimationConfig(
            keyframes=[
                Keyframe(time=0.0, values={"x": 0}),
                Keyframe(time=1.0, values={"x": 100}),
            ],
            duration=1.0,
        ))
        anim.start()
        anim.update(0.5)

        anim.pause()
        vals = anim.update(1.0)  # Should not advance
        assert vals["x"] == pytest.approx(50)

        anim.resume()
        vals = anim.update(0.49)
        assert vals["x"] == pytest.approx(99)

        vals = anim.update(0.01)
        assert vals["x"] == pytest.approx(100)

    def test_reset(self):
        anim = KeyframeAnimation(AnimationConfig(
            keyframes=[
                Keyframe(time=0.0, values={"x": 0}),
                Keyframe(time=1.0, values={"x": 100}),
            ],
            duration=1.0,
        ))
        anim.start()
        anim.update(1.0)
        assert anim.is_finished

        anim.reset()
        assert not anim.is_running
        assert not anim.is_finished
        assert anim.current_values["x"] == 0

    def test_seek(self):
        anim = KeyframeAnimation(AnimationConfig(
            keyframes=[
                Keyframe(time=0.0, values={"x": 0}),
                Keyframe(time=1.0, values={"x": 100}),
            ],
            duration=2.0,
        ))
        vals = anim.seek(1.0)
        assert vals["x"] == pytest.approx(50)

    def test_evaluate_at(self):
        anim = KeyframeAnimation(AnimationConfig(
            keyframes=[
                Keyframe(time=0.0, values={"x": 0}),
                Keyframe(time=1.0, values={"x": 100}),
            ],
            duration=1.0,
        ))
        vals = anim.evaluate_at(0.75)
        assert vals["x"] == pytest.approx(75)

    def test_vector3_interpolation(self):
        anim = KeyframeAnimation(AnimationConfig(
            keyframes=[
                Keyframe(time=0.0, values={"pos": Vector3(0, 0, 0)}),
                Keyframe(time=1.0, values={"pos": Vector3(10, 20, 30)}),
            ],
            duration=1.0,
        ))
        anim.start()
        vals = anim.update(0.5)
        pos = vals["pos"]
        assert pos.x == pytest.approx(5)
        assert pos.y == pytest.approx(10)
        assert pos.z == pytest.approx(15)

    def test_color_interpolation(self):
        anim = KeyframeAnimation(AnimationConfig(
            keyframes=[
                Keyframe(time=0.0, values={"color": Color(1, 0, 0, 1)}),
                Keyframe(time=1.0, values={"color": Color(0, 0, 1, 1)}),
            ],
            duration=1.0,
        ))
        anim.start()
        vals = anim.update(0.5)
        c = vals["color"]
        assert c.r == pytest.approx(0.5)
        assert c.b == pytest.approx(0.5)

    def test_multi_property(self):
        anim = KeyframeAnimation(AnimationConfig(
            keyframes=[
                Keyframe(time=0.0, values={"x": 0, "y": 0, "opacity": 1.0}),
                Keyframe(time=1.0, values={"x": 100, "y": 200, "opacity": 0.0}),
            ],
            duration=1.0,
        ))
        anim.start()
        vals = anim.update(0.5)
        assert vals["x"] == pytest.approx(50)
        assert vals["y"] == pytest.approx(100)
        assert vals["opacity"] == pytest.approx(0.5)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
