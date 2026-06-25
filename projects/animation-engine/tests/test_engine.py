"""Tests for the main animation engine."""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from animation_engine.engine import AnimationEngine
from animation_engine.keyframe import KeyframeAnimation
from animation_engine.tween import Tween
from animation_engine.types import AnimationConfig, Keyframe, TweenConfig, Vector3
from animation_engine.skeleton import Skeleton, SkeletalAnimation, SkinnedMesh, SkinWeight
from animation_engine.particle import ParticleEmitter, EmitterConfig, ParticleSystem


class TestAnimationEngine:
    def test_create(self):
        engine = AnimationEngine()
        assert engine.fps == 0.0

    def test_create_animation(self):
        engine = AnimationEngine()
        anim = engine.create_animation(AnimationConfig(
            keyframes=[
                Keyframe(time=0.0, values={"x": 0}),
                Keyframe(time=1.0, values={"x": 100}),
            ],
            duration=1.0,
        ))
        assert isinstance(anim, KeyframeAnimation)

    def test_create_tween(self):
        engine = AnimationEngine()
        tw = engine.create_tween(TweenConfig(
            from_values={"x": 0}, to_values={"x": 100}, duration=1.0
        ))
        assert isinstance(tw, Tween)

    def test_create_queue(self):
        engine = AnimationEngine()
        q = engine.create_queue("test")
        assert q is not None

    def test_update(self):
        engine = AnimationEngine()
        anim = engine.create_animation(AnimationConfig(
            keyframes=[
                Keyframe(time=0.0, values={"x": 0}),
                Keyframe(time=1.0, values={"x": 100}),
            ],
            duration=1.0,
        ), name="test")
        anim.start()

        engine.update(0.5)
        assert anim.current_values["x"] == pytest.approx(50)

    def test_time_scale(self):
        engine = AnimationEngine()
        anim = engine.create_animation(AnimationConfig(
            keyframes=[
                Keyframe(time=0.0, values={"x": 0}),
                Keyframe(time=1.0, values={"x": 100}),
            ],
            duration=1.0,
        ), name="test")
        anim.start()

        engine.time_scale = 0.5
        engine.update(1.0)  # Effective 0.5s
        assert anim.current_values["x"] == pytest.approx(50)

    def test_pause_resume(self):
        engine = AnimationEngine()
        anim = engine.create_animation(AnimationConfig(
            keyframes=[
                Keyframe(time=0.0, values={"x": 0}),
                Keyframe(time=1.0, values={"x": 100}),
            ],
            duration=1.0,
        ), name="test")
        anim.start()

        engine.update(0.5)
        engine.pause()
        engine.update(1.0)
        assert anim.current_values["x"] == pytest.approx(50)

        engine.resume()
        engine.update(0.49)
        assert anim.current_values["x"] == pytest.approx(99)

        engine.update(0.01)
        assert anim.current_values["x"] == pytest.approx(100)

    def test_stop(self):
        engine = AnimationEngine()
        anim = engine.create_animation(AnimationConfig(
            keyframes=[
                Keyframe(time=0.0, values={"x": 0}),
                Keyframe(time=1.0, values={"x": 100}),
            ],
            duration=1.0,
        ), name="test")
        anim.start()
        engine.stop()
        assert anim.is_finished

    def test_play_animation(self):
        engine = AnimationEngine()
        engine.create_animation(AnimationConfig(
            keyframes=[
                Keyframe(time=0.0, values={"x": 0}),
                Keyframe(time=1.0, values={"x": 100}),
            ],
            duration=1.0,
        ), name="test")

        anim = engine.play_animation("test")
        assert anim.is_running

    def test_play_tween(self):
        engine = AnimationEngine()
        engine.create_tween(TweenConfig(
            from_values={"x": 0}, to_values={"x": 100}, duration=1.0
        ), name="move")

        tw = engine.play_tween("move")
        assert tw.is_running

    def test_remove_animation(self):
        engine = AnimationEngine()
        engine.create_animation(AnimationConfig(
            keyframes=[Keyframe(time=0, values={"x": 0})],
        ), name="test")
        engine.remove_animation("test")
        assert engine.get_animation("test") is None

    def test_remove_tween(self):
        engine = AnimationEngine()
        engine.create_tween(TweenConfig(
            from_values={"x": 0}, to_values={"x": 100}
        ), name="test")
        engine.remove_tween("test")
        assert engine.get_tween("test") is None

    def test_remove_queue(self):
        engine = AnimationEngine()
        engine.create_queue("test")
        engine.remove_queue("test")
        assert engine.get_queue("test") is None

    def test_skeleton_integration(self):
        engine = AnimationEngine()
        skeleton = Skeleton()
        root = skeleton.add_bone("root")
        skeleton.add_bone("spine", parent=root, position=Vector3(0, 2, 0))
        engine.add_skeleton("character", skeleton)

        skel_anim = SkeletalAnimation("walk", duration=1.0)
        skel_anim.add_bone_keyframe("spine", 0.0, rotation=Vector3(0, 0, 0))
        skel_anim.add_bone_keyframe("spine", 1.0, rotation=Vector3(0.3, 0, 0))
        engine.add_skeletal_animation("walk", skel_anim)

        engine.update(0.5)
        spine = skeleton.get_bone("spine")
        assert spine.rotation.x != 0  # Should have rotated

    def test_particle_system_integration(self):
        engine = AnimationEngine()
        ps = ParticleSystem()
        ps.add_emitter("fire", ParticleEmitter(EmitterConfig(
            rate=50, lifetime_min=2.0, lifetime_max=2.0
        )))
        engine.add_particle_system("effects", ps)

        # Use small dt so particles are emitted and stay alive
        for _ in range(60):
            engine.update(1 / 60)
        assert ps.total_particles > 0

    def test_mesh_integration(self):
        engine = AnimationEngine()
        skeleton = Skeleton()
        root = skeleton.add_bone("root", position=Vector3(0, 0, 0))
        skeleton.add_bone("bone1", parent=root, position=Vector3(10, 0, 0))
        skeleton.update()

        mesh = SkinnedMesh()
        sw = SkinWeight()
        sw.add_influence(0, 0.5)
        sw.add_influence(1, 0.5)
        mesh.add_vertex(Vector3(0, 0, 0), sw)

        engine.add_skeleton("char", skeleton)
        engine.add_mesh("char_mesh", mesh)

        engine.update(0.016)
        # Mesh should be deformed
        assert len(mesh.current_positions) == 1

    def test_on_update_callback(self):
        engine = AnimationEngine()
        calls = []
        engine.on_update(lambda dt: calls.append(dt))
        engine.update(0.016)
        assert len(calls) == 1

    def test_get_stats(self):
        engine = AnimationEngine()
        engine.create_animation(AnimationConfig(
            keyframes=[Keyframe(time=0, values={"x": 0})],
        ), name="a")
        engine.create_tween(TweenConfig(
            from_values={"x": 0}, to_values={"x": 1}
        ), name="t")

        stats = engine.get_stats()
        assert stats["animations"] == 1
        assert stats["tweens"] == 1
        assert stats["time_scale"] == 1.0

    def test_auto_naming(self):
        engine = AnimationEngine()
        engine.create_animation(AnimationConfig(
            keyframes=[Keyframe(time=0, values={"x": 0})],
        ))
        engine.create_animation(AnimationConfig(
            keyframes=[Keyframe(time=0, values={"x": 0})],
        ))
        # Should auto-name as anim_0, anim_1
        assert engine.get_animation("anim_0") is not None
        assert engine.get_animation("anim_1") is not None

    def test_total_time(self):
        engine = AnimationEngine()
        engine.update(1.0)
        engine.update(1.0)
        assert engine.total_time == pytest.approx(2.0)

    def test_repr(self):
        engine = AnimationEngine()
        assert "AnimationEngine" in repr(engine)

    def test_complex_scenario(self):
        """Test a complex scenario with multiple animation types."""
        engine = AnimationEngine()

        # UI fade animation
        fade = engine.create_animation(AnimationConfig(
            keyframes=[
                Keyframe(time=0.0, values={"opacity": 0, "y": -20}),
                Keyframe(time=1.0, values={"opacity": 1, "y": 0}),
            ],
            duration=0.5,
            easing="ease_out_cubic",
        ), name="fade_in")
        fade.start()

        # Position tween
        move = engine.create_tween(TweenConfig(
            from_values={"x": 0}, to_values={"x": 300},
            duration=1.0, easing="ease_in_out_cubic",
        ), name="slide")
        move.start()

        # Run for 1 second
        for _ in range(60):
            engine.update(1 / 60)

        assert fade.is_finished
        assert move.is_finished
        assert engine.total_time == pytest.approx(1.0, abs=0.01)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
