"""Tests for tween animation."""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from animation_engine.tween import Tween
from animation_engine.types import TweenConfig


class TestTween:
    def test_create(self):
        tw = Tween(TweenConfig(
            from_values={"x": 0}, to_values={"x": 100}, duration=1.0
        ))
        assert not tw.is_running
        assert not tw.is_finished

    def test_basic_interpolation(self):
        tw = Tween(TweenConfig(
            from_values={"x": 0.0}, to_values={"x": 100.0}, duration=1.0
        ))
        tw.start()

        vals = tw.update(0.5)
        assert vals["x"] == pytest.approx(50)

    def test_easing(self):
        tw = Tween(TweenConfig(
            from_values={"x": 0.0}, to_values={"x": 100.0},
            duration=1.0, easing="ease_in_quad"
        ))
        tw.start()

        vals = tw.update(0.5)
        assert vals["x"] < 50  # Ease-in starts slow

    def test_multi_property(self):
        tw = Tween(TweenConfig(
            from_values={"x": 0.0, "y": 0.0},
            to_values={"x": 100.0, "y": 200.0},
            duration=1.0,
        ))
        tw.start()

        vals = tw.update(0.5)
        assert vals["x"] == pytest.approx(50)
        assert vals["y"] == pytest.approx(100)

    def test_mismatched_keys(self):
        with pytest.raises(ValueError, match="same keys"):
            Tween(TweenConfig(
                from_values={"x": 0}, to_values={"y": 100}
            ))

    def test_completion(self):
        tw = Tween(TweenConfig(
            from_values={"x": 0.0}, to_values={"x": 100.0}, duration=1.0
        ))
        tw.start()
        tw.update(1.5)
        assert tw.is_finished
        assert tw.current_values["x"] == pytest.approx(100)

    def test_callback(self):
        completed = []
        tw = Tween(TweenConfig(
            from_values={"x": 0.0}, to_values={"x": 100.0},
            duration=1.0, on_complete=lambda: completed.append(True)
        ))
        tw.start()
        tw.update(1.5)
        assert len(completed) == 1

    def test_update_callback(self):
        updates = []
        tw = Tween(TweenConfig(
            from_values={"x": 0.0}, to_values={"x": 100.0},
            duration=1.0, on_update=lambda v: updates.append(v["x"])
        ))
        tw.start()
        tw.update(0.5)
        assert len(updates) == 1

    def test_pause_resume(self):
        tw = Tween(TweenConfig(
            from_values={"x": 0.0}, to_values={"x": 100.0}, duration=1.0
        ))
        tw.start()
        tw.update(0.5)

        tw.pause()
        tw.update(1.0)
        assert tw.current_values["x"] == pytest.approx(50)

        tw.resume()
        tw.update(0.5)
        assert tw.current_values["x"] == pytest.approx(100)

    def test_reset(self):
        tw = Tween(TweenConfig(
            from_values={"x": 0.0}, to_values={"x": 100.0}, duration=1.0
        ))
        tw.start()
        tw.update(1.5)
        assert tw.is_finished

        tw.reset()
        assert not tw.is_running
        assert not tw.is_finished
        assert tw.current_values["x"] == pytest.approx(0)

    def test_delay(self):
        tw = Tween(TweenConfig(
            from_values={"x": 0.0}, to_values={"x": 100.0},
            duration=1.0, delay=0.5
        ))
        tw.start()

        vals = tw.update(0.3)
        assert vals["x"] == pytest.approx(0)

        vals = tw.update(0.5)
        assert vals["x"] > 0

    def test_progress(self):
        tw = Tween(TweenConfig(
            from_values={"x": 0.0}, to_values={"x": 100.0}, duration=1.0
        ))
        tw.start()

        tw.update(0.25)
        assert tw.progress == pytest.approx(0.25)

        tw.update(0.25)
        assert tw.progress == pytest.approx(0.5)

    def test_seek(self):
        tw = Tween(TweenConfig(
            from_values={"x": 0.0}, to_values={"x": 100.0}, duration=1.0
        ))
        vals = tw.seek(0.75)
        assert vals["x"] == pytest.approx(75)

    def test_chaining(self):
        tw1 = Tween(TweenConfig(
            from_values={"x": 0.0}, to_values={"x": 100.0}, duration=1.0
        ))
        tw2 = Tween(TweenConfig(
            from_values={"y": 0.0}, to_values={"y": 100.0}, duration=1.0
        ))

        tw1.then(tw2)
        tw1.start()

        # First tween
        tw1.update(1.5)
        assert tw1.is_finished

        # Chain should be started
        newly = tw1.update_chained(0)
        assert len(newly) == 1
        assert newly[0] is tw2

    def test_sequence(self):
        tweens = Tween.sequence(
            Tween(TweenConfig(from_values={"x": 0}, to_values={"x": 50}, duration=0.5)),
            Tween(TweenConfig(from_values={"x": 50}, to_values={"x": 100}, duration=0.5)),
        )
        assert len(tweens) == 2

    def test_parallel(self):
        tweens = Tween.parallel(
            Tween(TweenConfig(from_values={"x": 0}, to_values={"x": 100}, duration=1.0)),
            Tween(TweenConfig(from_values={"y": 0}, to_values={"y": 100}, duration=1.0)),
        )
        assert len(tweens) == 2
        for tw in tweens:
            assert tw.is_running

    def test_remaining(self):
        tw = Tween(TweenConfig(
            from_values={"x": 0}, to_values={"x": 100}, duration=2.0
        ))
        tw.start()
        tw.update(0.5)
        assert tw.remaining == pytest.approx(1.5)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
