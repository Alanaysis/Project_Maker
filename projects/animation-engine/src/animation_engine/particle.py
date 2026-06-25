"""
Particle system for particle-based animations.

Supports particle emitters, physics simulation, and various
particle behaviors for effects like fire, smoke, sparks, etc.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from .types import Color, Vector3
from .utils import clamp, lerp


@dataclass
class Particle:
    """A single particle with position, velocity, and visual properties."""
    position: Vector3 = field(default_factory=Vector3)
    velocity: Vector3 = field(default_factory=Vector3)
    acceleration: Vector3 = field(default_factory=Vector3)

    # Visual properties
    color: Color = field(default_factory=Color)
    start_color: Color = field(default_factory=Color)
    end_color: Color = field(default_factory=Color)
    size: float = 1.0
    start_size: float = 1.0
    end_size: float = 0.0
    rotation: float = 0.0
    rotation_speed: float = 0.0
    opacity: float = 1.0

    # Lifecycle
    age: float = 0.0
    lifetime: float = 1.0
    alive: bool = True

    # Custom data for user-defined behaviors
    data: Dict[str, Any] = field(default_factory=dict)

    @property
    def progress(self) -> float:
        """Normalized age [0, 1]."""
        if self.lifetime <= 0:
            return 1.0
        return clamp(self.age / self.lifetime)

    @property
    def remaining(self) -> float:
        """Remaining lifetime in seconds."""
        return max(0, self.lifetime - self.age)

    def update(self, dt: float) -> None:
        """Update the particle by dt seconds."""
        if not self.alive:
            return

        self.age += dt

        # Check death
        if self.age >= self.lifetime:
            self.alive = False
            return

        t = self.progress

        # Physics
        self.velocity = Vector3(
            self.velocity.x + self.acceleration.x * dt,
            self.velocity.y + self.acceleration.y * dt,
            self.velocity.z + self.acceleration.z * dt,
        )
        self.position = Vector3(
            self.position.x + self.velocity.x * dt,
            self.position.y + self.velocity.y * dt,
            self.position.z + self.velocity.z * dt,
        )

        # Visual interpolation
        self.color = Color.lerp(self.start_color, self.end_color, t)
        self.size = lerp(self.start_size, self.end_size, t)
        self.rotation += self.rotation_speed * dt
        self.opacity = 1.0 - t  # Fade out over lifetime

    def reset(self) -> None:
        """Reset particle to initial state."""
        self.age = 0.0
        self.alive = True
        self.color = self.start_color.copy()


@dataclass
class EmitterConfig:
    """Configuration for a particle emitter."""
    # Emission
    rate: float = 10.0  # Particles per second
    burst: int = 0  # Burst count (spawned immediately)
    max_particles: int = 100

    # Position
    position: Vector3 = field(default_factory=Vector3)
    position_spread: Vector3 = field(default_factory=Vector3)  # Random offset range

    # Velocity
    velocity: Vector3 = field(default_factory=lambda: Vector3(0, 1, 0))
    velocity_spread: Vector3 = field(default_factory=Vector3)
    speed_min: float = 1.0
    speed_max: float = 2.0

    # Acceleration / forces
    gravity: Vector3 = field(default_factory=Vector3)
    acceleration: Vector3 = field(default_factory=Vector3)

    # Lifetime
    lifetime_min: float = 1.0
    lifetime_max: float = 2.0

    # Size
    size_start: float = 1.0
    size_end: float = 0.0
    size_spread: float = 0.0

    # Color
    color_start: Color = field(default_factory=lambda: Color(1, 1, 1, 1))
    color_end: Color = field(default_factory=lambda: Color(1, 1, 1, 0))

    # Rotation
    rotation_speed_min: float = 0.0
    rotation_speed_max: float = 0.0

    # Shape
    shape: str = "point"  # point, circle, sphere, cone, box
    shape_radius: float = 1.0
    shape_size: Vector3 = field(default_factory=lambda: Vector3(1, 1, 1))


class ParticleEmitter:
    """Emits and manages particles.

    Example::

        emitter = ParticleEmitter(EmitterConfig(
            rate=50,
            lifetime_min=1.0,
            lifetime_max=3.0,
            velocity=Vector3(0, 2, 0),
            velocity_spread=Vector3(1, 0.5, 1),
            gravity=Vector3(0, -9.8, 0),
            size_start=2.0,
            size_end=0.0,
            color_start=Color(1, 0.5, 0, 1),
            color_end=Color(1, 0, 0, 0),
        ))
        emitter.update(dt)
        for p in emitter.particles:
            render(p)
    """

    def __init__(self, config: EmitterConfig):
        self.config = config
        self.particles: List[Particle] = []
        self._accumulator: float = 0.0  # For fractional particle emission
        self._active: bool = True
        self._total_emitted: int = 0

    @property
    def active_particle_count(self) -> int:
        return sum(1 for p in self.particles if p.alive)

    @property
    def is_active(self) -> bool:
        return self._active

    def start(self) -> None:
        """Start emitting."""
        self._active = True

    def stop(self) -> None:
        """Stop emitting (existing particles continue)."""
        self._active = False

    def burst_emit(self, count: Optional[int] = None) -> None:
        """Emit a burst of particles immediately."""
        n = count if count is not None else self.config.burst
        for _ in range(n):
            self._emit_particle()

    def clear(self) -> None:
        """Remove all particles."""
        self.particles.clear()

    def update(self, dt: float) -> None:
        """Update emitter and all particles.

        Args:
            dt: Delta time in seconds.
        """
        # Emit new particles
        if self._active and self.config.rate > 0:
            self._accumulator += self.config.rate * dt
            while self._accumulator >= 1.0:
                if self.active_particle_count < self.config.max_particles:
                    self._emit_particle()
                self._accumulator -= 1.0

        # Update existing particles
        for particle in self.particles:
            particle.update(dt)

        # Remove dead particles periodically
        if len(self.particles) > self.config.max_particles * 2:
            self.particles = [p for p in self.particles if p.alive]

    def _emit_particle(self) -> Particle:
        """Create and initialize a new particle."""
        cfg = self.config

        # Position with spread
        pos = Vector3(
            cfg.position.x + random.uniform(-cfg.position_spread.x, cfg.position_spread.x),
            cfg.position.y + random.uniform(-cfg.position_spread.y, cfg.position_spread.y),
            cfg.position.z + random.uniform(-cfg.position_spread.z, cfg.position_spread.z),
        )

        # Apply shape offset
        if cfg.shape == "circle":
            angle = random.uniform(0, 2 * math.pi)
            r = random.uniform(0, cfg.shape_radius)
            pos = Vector3(pos.x + r * math.cos(angle), pos.y, pos.z + r * math.sin(angle))
        elif cfg.shape == "sphere":
            theta = random.uniform(0, 2 * math.pi)
            phi = random.uniform(0, math.pi)
            r = random.uniform(0, cfg.shape_radius)
            pos = Vector3(
                pos.x + r * math.sin(phi) * math.cos(theta),
                pos.y + r * math.cos(phi),
                pos.z + r * math.sin(phi) * math.sin(theta),
            )

        # Velocity
        speed = random.uniform(cfg.speed_min, cfg.speed_max)
        vel_dir = Vector3(
            cfg.velocity.x + random.uniform(-cfg.velocity_spread.x, cfg.velocity_spread.x),
            cfg.velocity.y + random.uniform(-cfg.velocity_spread.y, cfg.velocity_spread.y),
            cfg.velocity.z + random.uniform(-cfg.velocity_spread.z, cfg.velocity_spread.z),
        )
        vel_len = vel_dir.length()
        if vel_len > 0:
            vel = Vector3(vel_dir.x / vel_len * speed, vel_dir.y / vel_len * speed, vel_dir.z / vel_len * speed)
        else:
            vel = Vector3(0, speed, 0)

        # Lifetime
        lifetime = random.uniform(cfg.lifetime_min, cfg.lifetime_max)

        # Size
        size_start = cfg.size_start + random.uniform(-cfg.size_spread, cfg.size_spread)
        size_end = cfg.size_end + random.uniform(-cfg.size_spread, cfg.size_spread)

        # Rotation
        rot_speed = random.uniform(cfg.rotation_speed_min, cfg.rotation_speed_max)

        particle = Particle(
            position=pos,
            velocity=vel,
            acceleration=Vector3(
                cfg.gravity.x + cfg.acceleration.x,
                cfg.gravity.y + cfg.acceleration.y,
                cfg.gravity.z + cfg.acceleration.z,
            ),
            color=cfg.color_start.copy(),
            start_color=cfg.color_start.copy(),
            end_color=cfg.color_end.copy(),
            size=size_start,
            start_size=size_start,
            end_size=size_end,
            rotation=0.0,
            rotation_speed=rot_speed,
            lifetime=lifetime,
        )

        # Try to reuse a dead particle
        for i, p in enumerate(self.particles):
            if not p.alive:
                self.particles[i] = particle
                self._total_emitted += 1
                return particle

        self.particles.append(particle)
        self._total_emitted += 1
        return particle

    def __repr__(self) -> str:
        return f"ParticleEmitter(active={self.active_particle_count}, total={len(self.particles)})"


class ParticleSystem:
    """A system that manages multiple particle emitters.

    Example::

        system = ParticleSystem()

        # Fire emitter
        fire = ParticleEmitter(EmitterConfig(
            rate=100, position=Vector3(0, 0, 0),
            velocity=Vector3(0, 3, 0), velocity_spread=Vector3(0.5, 0.5, 0.5),
            lifetime_min=0.5, lifetime_max=1.5,
            color_start=Color(1, 0.8, 0, 1), color_end=Color(1, 0, 0, 0),
            size_start=3.0, size_end=0.5,
        ))
        system.add_emitter("fire", fire)

        # Smoke emitter
        smoke = ParticleEmitter(EmitterConfig(
            rate=30, position=Vector3(0, 2, 0),
            velocity=Vector3(0, 1, 0), velocity_spread=Vector3(0.3, 0.2, 0.3),
            lifetime_min=2.0, lifetime_max=4.0,
            color_start=Color(0.3, 0.3, 0.3, 0.5), color_end=Color(0.3, 0.3, 0.3, 0),
            size_start=1.0, size_end=4.0,
        ))
        system.add_emitter("smoke", smoke)

        system.update(dt)
    """

    def __init__(self):
        self._emitters: Dict[str, ParticleEmitter] = {}
        self._global_gravity = Vector3(0, -9.8, 0)
        self._use_global_gravity = False

    @property
    def global_gravity(self) -> Vector3:
        return self._global_gravity

    @global_gravity.setter
    def global_gravity(self, value: Vector3) -> None:
        self._global_gravity = value

    @property
    def use_global_gravity(self) -> bool:
        return self._use_global_gravity

    @use_global_gravity.setter
    def use_global_gravity(self, value: bool) -> None:
        self._use_global_gravity = value

    def add_emitter(self, name: str, emitter: ParticleEmitter) -> None:
        """Add a named emitter to the system."""
        self._emitters[name] = emitter

    def get_emitter(self, name: str) -> Optional[ParticleEmitter]:
        """Get an emitter by name."""
        return self._emitters.get(name)

    def remove_emitter(self, name: str) -> None:
        """Remove an emitter by name."""
        self._emitters.pop(name, None)

    @property
    def emitter_names(self) -> List[str]:
        return list(self._emitters.keys())

    @property
    def total_particles(self) -> int:
        return sum(e.active_particle_count for e in self._emitters.values())

    def update(self, dt: float) -> None:
        """Update all emitters and their particles."""
        for emitter in self._emitters.values():
            if self._use_global_gravity:
                # Apply global gravity to emitter config
                emitter.config.gravity = self._global_gravity
            emitter.update(dt)

    def start_all(self) -> None:
        """Start all emitters."""
        for emitter in self._emitters.values():
            emitter.start()

    def stop_all(self) -> None:
        """Stop all emitters."""
        for emitter in self._emitters.values():
            emitter.stop()

    def clear_all(self) -> None:
        """Clear all particles from all emitters."""
        for emitter in self._emitters.values():
            emitter.clear()

    def get_all_particles(self) -> List[Particle]:
        """Get all alive particles from all emitters."""
        result = []
        for emitter in self._emitters.values():
            result.extend(p for p in emitter.particles if p.alive)
        return result

    def __repr__(self) -> str:
        return f"ParticleSystem(emitters={len(self._emitters)}, particles={self.total_particles})"
