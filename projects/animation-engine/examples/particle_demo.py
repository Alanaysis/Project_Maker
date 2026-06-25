"""
Particle System Demo

Demonstrates particle emitters for effects like fire, smoke, sparks, and rain.
"""

import sys
import os
import math
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from animation_engine.particle import ParticleEmitter, EmitterConfig, ParticleSystem
from animation_engine.types import Vector3, Color


def create_fire_effect():
    """Create a fire particle effect."""
    system = ParticleSystem()

    # Main fire
    fire = ParticleEmitter(EmitterConfig(
        rate=80,
        max_particles=200,
        position=Vector3(0, 0, 0),
        position_spread=Vector3(0.3, 0, 0.3),
        velocity=Vector3(0, 2.0, 0),
        velocity_spread=Vector3(0.3, 0.5, 0.3),
        speed_min=1.0,
        speed_max=2.5,
        lifetime_min=0.5,
        lifetime_max=1.2,
        size_start=2.0,
        size_end=0.2,
        color_start=Color(1.0, 0.8, 0.2, 1.0),
        color_end=Color(1.0, 0.1, 0.0, 0.0),
    ))
    system.add_emitter("fire", fire)

    # Embers / sparks
    sparks = ParticleEmitter(EmitterConfig(
        rate=15,
        max_particles=50,
        position=Vector3(0, 0.5, 0),
        position_spread=Vector3(0.2, 0, 0.2),
        velocity=Vector3(0, 3.0, 0),
        velocity_spread=Vector3(1.0, 1.0, 1.0),
        speed_min=2.0,
        speed_max=4.0,
        lifetime_min=0.8,
        lifetime_max=2.0,
        size_start=0.5,
        size_end=0.1,
        color_start=Color(1.0, 0.9, 0.3, 1.0),
        color_end=Color(1.0, 0.3, 0.0, 0.0),
    ))
    system.add_emitter("sparks", sparks)

    # Smoke
    smoke = ParticleEmitter(EmitterConfig(
        rate=20,
        max_particles=60,
        position=Vector3(0, 1.5, 0),
        position_spread=Vector3(0.3, 0, 0.3),
        velocity=Vector3(0, 0.8, 0),
        velocity_spread=Vector3(0.2, 0.3, 0.2),
        speed_min=0.3,
        speed_max=0.8,
        lifetime_min=2.0,
        lifetime_max=4.0,
        size_start=1.0,
        size_end=3.0,
        color_start=Color(0.3, 0.3, 0.3, 0.6),
        color_end=Color(0.2, 0.2, 0.2, 0.0),
    ))
    system.add_emitter("smoke", smoke)

    return system


def create_rain_effect():
    """Create a rain particle effect."""
    system = ParticleSystem()

    rain = ParticleEmitter(EmitterConfig(
        rate=200,
        max_particles=500,
        position=Vector3(0, 10, 0),
        position_spread=Vector3(10, 0, 10),
        velocity=Vector3(0, -8, 0),
        velocity_spread=Vector3(0.5, 1, 0.5),
        speed_min=6.0,
        speed_max=10.0,
        lifetime_min=1.0,
        lifetime_max=2.0,
        size_start=0.1,
        size_end=0.05,
        color_start=Color(0.6, 0.7, 0.9, 0.7),
        color_end=Color(0.6, 0.7, 0.9, 0.0),
    ))
    system.add_emitter("rain", rain)

    return system


def create_explosion_effect():
    """Create an explosion particle effect."""
    system = ParticleSystem()

    # Core explosion
    core = ParticleEmitter(EmitterConfig(
        rate=0,  # Burst only
        burst=100,
        max_particles=100,
        position=Vector3(0, 0, 0),
        velocity=Vector3(0, 0, 0),
        velocity_spread=Vector3(1, 1, 1),
        speed_min=3.0,
        speed_max=8.0,
        lifetime_min=0.3,
        lifetime_max=1.0,
        size_start=1.5,
        size_end=0.0,
        color_start=Color(1.0, 0.9, 0.3, 1.0),
        color_end=Color(1.0, 0.2, 0.0, 0.0),
    ))
    system.add_emitter("core", core)

    # Debris
    debris = ParticleEmitter(EmitterConfig(
        rate=0,
        burst=30,
        max_particles=30,
        position=Vector3(0, 0, 0),
        velocity=Vector3(0, 2, 0),
        velocity_spread=Vector3(1, 1, 1),
        speed_min=2.0,
        speed_max=6.0,
        gravity=Vector3(0, -9.8, 0),
        lifetime_min=1.0,
        lifetime_max=2.5,
        size_start=0.5,
        size_end=0.3,
        color_start=Color(0.4, 0.3, 0.2, 1.0),
        color_end=Color(0.2, 0.15, 0.1, 0.0),
        rotation_speed_min=-180,
        rotation_speed_max=180,
    ))
    system.add_emitter("debris", debris)

    # Smoke ring
    smoke = ParticleEmitter(EmitterConfig(
        rate=0,
        burst=40,
        max_particles=40,
        position=Vector3(0, 0.5, 0),
        velocity=Vector3(0, 0.5, 0),
        velocity_spread=Vector3(1, 0.3, 1),
        speed_min=0.5,
        speed_max=2.0,
        lifetime_min=2.0,
        lifetime_max=4.0,
        size_start=0.5,
        size_end=4.0,
        color_start=Color(0.3, 0.3, 0.3, 0.8),
        color_end=Color(0.2, 0.2, 0.2, 0.0),
    ))
    system.add_emitter("smoke", smoke)

    return system


def render_particles_ascii(particles, width=60, height=25):
    """Render particles as ASCII art."""
    grid = [[" " for _ in range(width)] for _ in range(height)]
    cx, cy = width // 2, height - 3
    scale = 3.0

    for p in particles:
        if not p.alive:
            continue
        x = int(cx + p.position.x * scale)
        y = int(cy - p.position.y * scale)
        if 0 <= x < width and 0 <= y < height:
            # Use different chars based on size/opacity
            if p.opacity > 0.7:
                ch = "*"
            elif p.opacity > 0.4:
                ch = "+"
            elif p.opacity > 0.1:
                ch = "."
            else:
                ch = ","
            grid[y][x] = ch

    return "\n".join("".join(row) for row in grid)


def main():
    print("=" * 60)
    print("  Particle System Demo")
    print("=" * 60)
    print()

    # 1. Fire effect
    print("1. Fire Effect")
    print("-" * 40)
    fire = create_fire_effect()
    fire.start_all()

    for frame in range(6):
        fire.update(0.1)
        particles = fire.get_all_particles()
        print(f"  Frame {frame}: {len(particles)} particles")
        if frame >= 3:
            print(render_particles_ascii(particles))
    print()

    # 2. Rain effect
    print("2. Rain Effect")
    print("-" * 40)
    rain = create_rain_effect()
    rain.start_all()

    for frame in range(5):
        rain.update(0.1)
        particles = rain.get_all_particles()
        print(f"  Frame {frame}: {len(particles)} particles")
        if frame >= 2:
            print(render_particles_ascii(particles, width=50, height=15))
    print()

    # 3. Explosion
    print("3. Explosion Effect")
    print("-" * 40)
    explosion = create_explosion_effect()
    # Trigger burst
    for emitter_name in explosion.emitter_names:
        emitter = explosion.get_emitter(emitter_name)
        emitter.burst_emit()

    for frame in range(8):
        explosion.update(0.1)
        particles = explosion.get_all_particles()
        print(f"  Frame {frame}: {len(particles)} particles")
        if frame >= 4:
            print(render_particles_ascii(particles))
    print()

    # 4. Custom fountain
    print("4. Fountain Effect")
    print("-" * 40)
    fountain = ParticleSystem()
    fountain.add_emitter("water", ParticleEmitter(EmitterConfig(
        rate=60,
        max_particles=200,
        position=Vector3(0, 0, 0),
        velocity=Vector3(0, 5, 0),
        velocity_spread=Vector3(0.5, 0, 0.5),
        speed_min=3.0,
        speed_max=6.0,
        gravity=Vector3(0, -9.8, 0),
        lifetime_min=1.0,
        lifetime_max=2.0,
        size_start=0.3,
        size_end=0.1,
        color_start=Color(0.3, 0.5, 1.0, 0.8),
        color_end=Color(0.2, 0.4, 0.9, 0.0),
    )))
    fountain.start_all()

    for frame in range(10):
        fountain.update(0.05)
        particles = fountain.get_all_particles()
        print(f"  Frame {frame}: {len(particles)} particles")
        if frame >= 6:
            print(render_particles_ascii(particles, width=40, height=15))
    print()

    # 5. Stats
    print("5. Particle Statistics")
    print("-" * 40)
    fire = create_fire_effect()
    fire.start_all()
    for _ in range(30):
        fire.update(0.05)

    print(f"  Fire system: {fire}")
    for name in fire.emitter_names:
        emitter = fire.get_emitter(name)
        print(f"    {name}: {emitter.active_particle_count} active particles")

    print()
    print("=" * 60)
    print("  Particle demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
