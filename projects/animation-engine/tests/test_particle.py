"""Tests for particle system."""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from animation_engine.particle import Particle, ParticleEmitter, EmitterConfig, ParticleSystem
from animation_engine.types import Vector3, Color


class TestParticle:
    def test_create(self):
        p = Particle()
        assert p.alive
        assert p.age == 0.0

    def test_update(self):
        p = Particle(
            position=Vector3(0, 0, 0),
            velocity=Vector3(1, 0, 0),
            lifetime=1.0,
        )
        p.update(0.5)
        assert p.position.x == pytest.approx(0.5)
        assert p.age == pytest.approx(0.5)
        assert p.alive

    def test_death(self):
        p = Particle(lifetime=1.0)
        p.update(1.5)
        assert not p.alive

    def test_progress(self):
        p = Particle(lifetime=2.0)
        p.update(1.0)
        assert p.progress == pytest.approx(0.5)

    def test_remaining(self):
        p = Particle(lifetime=2.0)
        p.update(0.5)
        assert p.remaining == pytest.approx(1.5)

    def test_color_interpolation(self):
        p = Particle(
            start_color=Color(1, 0, 0, 1),
            end_color=Color(0, 0, 1, 1),
            lifetime=1.0,
        )
        p.update(0.5)
        assert p.color.r == pytest.approx(0.5)
        assert p.color.b == pytest.approx(0.5)

    def test_size_interpolation(self):
        p = Particle(
            start_size=10.0,
            end_size=0.0,
            lifetime=1.0,
        )
        p.update(0.5)
        assert p.size == pytest.approx(5.0)

    def test_rotation(self):
        p = Particle(rotation_speed=90.0, lifetime=2.0)
        p.update(1.0)
        assert p.rotation == pytest.approx(90.0)

    def test_gravity(self):
        p = Particle(
            velocity=Vector3(0, 10, 0),
            acceleration=Vector3(0, -9.8, 0),
            lifetime=5.0,
        )
        # Semi-implicit Euler: update velocity first, then position with new velocity
        p.update(1.0)
        # v = 10 + (-9.8)*1 = 0.2
        # pos = 0 + 0.2*1 = 0.2 (using updated velocity)
        assert p.velocity.y == pytest.approx(0.2, abs=0.01)
        assert p.position.y == pytest.approx(0.2, abs=0.01)

    def test_reset(self):
        p = Particle(
            start_color=Color(1, 1, 1, 1),
            lifetime=1.0,
        )
        p.update(1.5)
        assert not p.alive
        p.reset()
        assert p.alive
        assert p.age == 0.0

    def test_dead_no_update(self):
        p = Particle(lifetime=0.1)
        p.update(0.2)
        pos_before = p.position.copy()
        p.update(1.0)  # Should not update
        assert p.position.x == pos_before.x


class TestParticleEmitter:
    def test_create(self):
        emitter = ParticleEmitter(EmitterConfig(rate=10))
        assert emitter.active_particle_count == 0

    def test_emission(self):
        emitter = ParticleEmitter(EmitterConfig(rate=10, lifetime_min=2.0, lifetime_max=2.0))
        emitter.update(1.0)  # Should emit ~10 particles
        assert emitter.active_particle_count >= 9

    def test_max_particles(self):
        emitter = ParticleEmitter(EmitterConfig(
            rate=1000, max_particles=50, lifetime_min=10.0, lifetime_max=10.0
        ))
        emitter.update(1.0)
        assert emitter.active_particle_count <= 50

    def test_burst(self):
        emitter = ParticleEmitter(EmitterConfig(
            rate=0, burst=20, lifetime_min=5.0, lifetime_max=5.0
        ))
        emitter.burst_emit(20)
        assert emitter.active_particle_count == 20

    def test_stop(self):
        emitter = ParticleEmitter(EmitterConfig(rate=10, lifetime_min=5.0))
        emitter.update(0.5)
        count_before = emitter.active_particle_count
        emitter.stop()
        emitter.update(1.0)
        # No new particles, but existing ones still alive
        assert emitter.active_particle_count <= count_before + 1

    def test_clear(self):
        emitter = ParticleEmitter(EmitterConfig(rate=10, lifetime_min=5.0))
        emitter.update(1.0)
        assert emitter.active_particle_count > 0
        emitter.clear()
        assert emitter.active_particle_count == 0

    def test_particle_lifetime(self):
        emitter = ParticleEmitter(EmitterConfig(
            rate=100, lifetime_min=0.5, lifetime_max=0.5
        ))
        emitter.update(1.0)  # Emit 100
        initial_count = emitter.active_particle_count
        emitter.update(1.0)  # All should die after 0.5s, new ones emitted
        # After 1s, the original 100 should be dead
        # New ones from second update should be alive
        assert emitter.active_particle_count < initial_count + 100

    def test_velocity_spread(self):
        emitter = ParticleEmitter(EmitterConfig(
            rate=10, velocity=Vector3(0, 1, 0),
            velocity_spread=Vector3(1, 0, 1),
            speed_min=1.0, speed_max=1.0,
            lifetime_min=5.0, lifetime_max=5.0,
        ))
        emitter.update(1.0)
        assert emitter.active_particle_count >= 1

    def test_shape_circle(self):
        emitter = ParticleEmitter(EmitterConfig(
            rate=100, shape="circle", shape_radius=5.0,
            lifetime_min=5.0, lifetime_max=5.0,
        ))
        emitter.update(1.0)
        for p in emitter.particles:
            if p.alive:
                dist = (p.position.x ** 2 + p.position.z ** 2) ** 0.5
                assert dist <= 5.0 + 0.01

    def test_repr(self):
        emitter = ParticleEmitter(EmitterConfig())
        assert "ParticleEmitter" in repr(emitter)


class TestParticleSystem:
    def test_create(self):
        system = ParticleSystem()
        assert system.total_particles == 0

    def test_add_emitter(self):
        system = ParticleSystem()
        emitter = ParticleEmitter(EmitterConfig(rate=10))
        system.add_emitter("fire", emitter)
        assert "fire" in system.emitter_names

    def test_get_emitter(self):
        system = ParticleSystem()
        emitter = ParticleEmitter(EmitterConfig())
        system.add_emitter("fire", emitter)
        assert system.get_emitter("fire") is emitter
        assert system.get_emitter("smoke") is None

    def test_remove_emitter(self):
        system = ParticleSystem()
        system.add_emitter("fire", ParticleEmitter(EmitterConfig()))
        system.remove_emitter("fire")
        assert "fire" not in system.emitter_names

    def test_update(self):
        system = ParticleSystem()
        system.add_emitter("fire", ParticleEmitter(EmitterConfig(
            rate=10, lifetime_min=2.0, lifetime_max=2.0
        )))
        system.update(1.0)
        assert system.total_particles > 0

    def test_multi_emitter(self):
        system = ParticleSystem()
        system.add_emitter("fire", ParticleEmitter(EmitterConfig(
            rate=10, lifetime_min=2.0, lifetime_max=2.0
        )))
        system.add_emitter("smoke", ParticleEmitter(EmitterConfig(
            rate=5, lifetime_min=3.0, lifetime_max=3.0
        )))
        system.update(1.0)
        fire = system.get_emitter("fire")
        smoke = system.get_emitter("smoke")
        assert fire.active_particle_count > 0
        assert smoke.active_particle_count > 0

    def test_start_stop_all(self):
        system = ParticleSystem()
        system.add_emitter("a", ParticleEmitter(EmitterConfig(rate=100, lifetime_min=5.0)))
        system.add_emitter("b", ParticleEmitter(EmitterConfig(rate=100, lifetime_min=5.0)))
        system.update(0.1)

        system.stop_all()
        count_before = system.total_particles
        system.update(0.5)
        # Some new from the 0.1s accumulation, but emitters are stopped
        assert system.total_particles <= count_before + 20

    def test_clear_all(self):
        system = ParticleSystem()
        system.add_emitter("a", ParticleEmitter(EmitterConfig(rate=10, lifetime_min=5.0)))
        system.update(1.0)
        assert system.total_particles > 0
        system.clear_all()
        assert system.total_particles == 0

    def test_global_gravity(self):
        system = ParticleSystem()
        system.global_gravity = Vector3(0, -20, 0)
        system.use_global_gravity = True
        emitter = ParticleEmitter(EmitterConfig(
            rate=1, velocity=Vector3(0, 10, 0), lifetime_min=5.0, lifetime_max=5.0
        ))
        system.add_emitter("test", emitter)
        system.update(1.0)
        p = emitter.particles[0]
        assert p.acceleration.y == pytest.approx(-20)

    def test_get_all_particles(self):
        system = ParticleSystem()
        system.add_emitter("a", ParticleEmitter(EmitterConfig(rate=10, lifetime_min=5.0)))
        system.add_emitter("b", ParticleEmitter(EmitterConfig(rate=10, lifetime_min=5.0)))
        system.update(1.0)
        all_p = system.get_all_particles()
        assert len(all_p) == system.total_particles

    def test_repr(self):
        system = ParticleSystem()
        assert "ParticleSystem" in repr(system)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
