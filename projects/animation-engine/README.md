# Animation Engine

A comprehensive Python animation framework supporting keyframe animations,
tween animations with easing functions, skeletal animation, and particle systems.

## Features

- **Keyframe Animations**: Multi-step animations with per-keyframe easing, direction control, and iteration
- **Tween Animations**: Simple numeric property interpolation with chaining support
- **30+ Easing Functions**: Linear, quadratic, cubic, sine, exponential, elastic, bounce, and more
- **Skeletal Animation**: Bone hierarchy, skinning weights, mesh deformation
- **Particle System**: Particle emitters with physics, color/size interpolation, multiple shapes
- **Animation Queue**: Sequential execution of animations, waits, and callbacks
- **Unified Engine**: Central orchestrator with time scaling, FPS tracking, and stats

## Quick Start

```python
from animation_engine import (
    AnimationEngine, Keyframe, AnimationConfig, TweenConfig,
    Vector3, Color, Skeleton, SkeletalAnimation,
    ParticleEmitter, EmitterConfig, ParticleSystem,
)

engine = AnimationEngine()

# Keyframe animation
fade = engine.create_animation(AnimationConfig(
    keyframes=[
        Keyframe(time=0.0, values={"opacity": 0, "y": -20}),
        Keyframe(time=1.0, values={"opacity": 1, "y": 0}),
    ],
    duration=0.5,
    easing="ease_out_cubic",
))
fade.start()

# Tween
move = engine.create_tween(TweenConfig(
    from_values={"x": 0}, to_values={"x": 300},
    duration=1.0, easing="ease_in_out_cubic",
))
move.start()

# Game loop
while running:
    dt = get_delta_time()
    engine.update(dt)
```

## Project Structure

```
animation-engine/
├── src/animation_engine/
│   ├── __init__.py         # Public API exports
│   ├── types.py            # Vector3, Color, Keyframe, configs
│   ├── easing.py           # 30+ easing functions
│   ├── utils.py            # Timer, FrameRateCounter, utilities
│   ├── keyframe.py         # KeyframeAnimation class
│   ├── tween.py            # Tween class
│   ├── skeleton.py         # Bone, Skeleton, SkinWeight, SkeletalAnimation
│   ├── particle.py         # Particle, ParticleEmitter, ParticleSystem
│   ├── queue.py            # AnimationQueue
│   └── engine.py           # AnimationEngine
├── tests/                  # Unit tests (8 modules)
├── examples/               # Demo scripts
├── docs/                   # Design documents
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Easing Functions

| Family | Functions |
|--------|-----------|
| Linear | `linear` |
| Quadratic | `ease_in_quad`, `ease_out_quad`, `ease_in_out_quad` |
| Cubic | `ease_in_cubic`, `ease_out_cubic`, `ease_in_out_cubic` |
| Quartic | `ease_in_quart`, `ease_out_quart`, `ease_in_out_quart` |
| Quintic | `ease_in_quint`, `ease_out_quint`, `ease_in_out_quint` |
| Sine | `ease_in_sine`, `ease_out_sine`, `ease_in_out_sine` |
| Exponential | `ease_in_expo`, `ease_out_expo`, `ease_in_out_expo` |
| Circular | `ease_in_circ`, `ease_out_circ`, `ease_in_out_circ` |
| Elastic | `ease_in_elastic`, `ease_out_elastic`, `ease_in_out_elastic` |
| Back | `ease_in_back`, `ease_out_back`, `ease_in_out_back` |
| Bounce | `ease_in_bounce`, `ease_out_bounce`, `ease_in_out_bounce` |

## Skeletal Animation

```python
skeleton = Skeleton()
root = skeleton.add_bone("root", position=Vector3(0, 0, 0))
spine = skeleton.add_bone("spine", parent=root, position=Vector3(0, 2, 0))
head = skeleton.add_bone("head", parent=spine, position=Vector3(0, 1.5, 0))

anim = SkeletalAnimation("walk", duration=1.0)
anim.add_bone_keyframe("spine", 0.0, rotation=Vector3(0, 0, 0))
anim.add_bone_keyframe("spine", 0.5, rotation=Vector3(0.2, 0, 0))
anim.apply(skeleton, time=0.25)
```

## Particle System

```python
ps = ParticleSystem()
ps.add_emitter("fire", ParticleEmitter(EmitterConfig(
    rate=80, max_particles=200,
    velocity=Vector3(0, 2, 0), velocity_spread=Vector3(0.3, 0.5, 0.3),
    lifetime_min=0.5, lifetime_max=1.2,
    color_start=Color(1.0, 0.8, 0.2, 1.0),
    color_end=Color(1.0, 0.1, 0.0, 0.0),
    size_start=2.0, size_end=0.2,
)))
ps.start_all()
ps.update(dt)
```

## Animation Queue

```python
queue = engine.create_queue("sequence")
queue.animate(fade_config)
queue.wait(0.5)
queue.call(lambda: print("mid-point"))
queue.animate(slide_config)
queue.on_complete(lambda: print("done!"))
queue.start()
```

## Development

```bash
# Install
pip install -r requirements.txt

# Test
python -m pytest tests/ -v

# Coverage
python -m pytest tests/ -v --cov=animation_engine

# Examples
python examples/easing_demo.py
python examples/ui_animation.py
python examples/skeletal_animation.py
python examples/particle_demo.py
```

## Learning Goals

- Understand animation principles and timing functions
- Master easing function mathematics
- Learn skeletal animation and skinning
- Explore particle system design
- Practice Python dataclass-based API design

## License

MIT
