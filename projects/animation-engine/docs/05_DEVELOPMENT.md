# Animation Engine - Development Guide

## Setup

### Prerequisites
- Python 3.8+
- pytest (for testing)

### Installation
```bash
cd projects/animation-engine
pip install -r requirements.txt
```

### Running Tests
```bash
# All tests
python -m pytest tests/ -v

# Specific module
python -m pytest tests/test_easing.py -v

# With coverage
python -m pytest tests/ -v --cov=animation_engine --cov-report=term-missing
```

### Running Examples
```bash
python examples/easing_demo.py
python examples/ui_animation.py
python examples/skeletal_animation.py
python examples/particle_demo.py
```

## Project Structure

```
animation-engine/
├── src/
│   └── animation_engine/
│       ├── __init__.py         # Public API
│       ├── types.py            # Data classes
│       ├── easing.py           # Easing functions
│       ├── utils.py            # Utilities
│       ├── keyframe.py         # Keyframe animation
│       ├── tween.py            # Tween animation
│       ├── skeleton.py         # Skeletal animation
│       ├── particle.py         # Particle system
│       ├── queue.py            # Animation queue
│       └── engine.py           # Main engine
├── tests/
│   ├── test_easing.py
│   ├── test_types.py
│   ├── test_keyframe.py
│   ├── test_tween.py
│   ├── test_skeleton.py
│   ├── test_particle.py
│   ├── test_queue.py
│   └── test_engine.py
├── examples/
│   ├── easing_demo.py
│   ├── ui_animation.py
│   ├── skeletal_animation.py
│   └── particle_demo.py
├── docs/
│   ├── 01_RESEARCH.md
│   ├── 02_REQUIREMENTS.md
│   ├── 03_DESIGN.md
│   ├── 04_IMPLEMENTATION.md
│   └── 05_DEVELOPMENT.md
├── requirements.txt
├── pyproject.toml
└── README.md
```

## API Quick Reference

### Create Engine
```python
from animation_engine import AnimationEngine

engine = AnimationEngine()
```

### Keyframe Animation
```python
from animation_engine import AnimationConfig, Keyframe

anim = engine.create_animation(AnimationConfig(
    keyframes=[
        Keyframe(time=0.0, values={"x": 0, "opacity": 1.0}),
        Keyframe(time=1.0, values={"x": 200, "opacity": 0.5}),
    ],
    duration=1.0,
    easing="ease_out_cubic",
    iterations=3,
    direction="alternate",
))
anim.start()
```

### Tween
```python
from animation_engine import TweenConfig

tween = engine.create_tween(TweenConfig(
    from_values={"x": 0, "y": 0},
    to_values={"x": 200, "y": 100},
    duration=0.5,
    easing="ease_out_cubic",
))
tween.start()
```

### Skeletal Animation
```python
from animation_engine import Skeleton, SkeletalAnimation, Vector3

skeleton = Skeleton()
root = skeleton.add_bone("root", position=Vector3(0, 0, 0))
spine = skeleton.add_bone("spine", parent=root, position=Vector3(0, 2, 0))

anim = SkeletalAnimation("walk", duration=1.0)
anim.add_bone_keyframe("spine", 0.0, rotation=Vector3(0, 0, 0))
anim.add_bone_keyframe("spine", 0.5, rotation=Vector3(0.2, 0, 0))
anim.add_bone_keyframe("spine", 1.0, rotation=Vector3(0, 0, 0))

engine.add_skeleton("character", skeleton)
engine.add_skeletal_animation("walk", anim)
```

### Particle System
```python
from animation_engine import ParticleEmitter, EmitterConfig, ParticleSystem, Vector3, Color

ps = ParticleSystem()
ps.add_emitter("fire", ParticleEmitter(EmitterConfig(
    rate=50,
    velocity=Vector3(0, 2, 0),
    lifetime_min=0.5, lifetime_max=1.5,
    color_start=Color(1, 0.8, 0, 1),
    color_end=Color(1, 0, 0, 0),
    size_start=2.0, size_end=0.0,
)))
engine.add_particle_system("effects", ps)
```

### Animation Queue
```python
queue = engine.create_queue("sequence")
queue.animate(config1)
queue.wait(0.5)
queue.call(lambda: print("mid"))
queue.animate(config2)
queue.start()
```

### Game Loop
```python
engine.start()
while running:
    dt = get_delta_time()
    engine.update(dt)
    render()
```

## Extending the Engine

### Custom Easing Function
```python
from animation_engine.easing import EASING_FUNCTIONS

def my_custom_ease(t):
    return t * t * (3 - 2 * t)  # Smoothstep

EASING_FUNCTIONS["my_custom_ease"] = my_custom_ease
```

### Custom Particle Behavior
```python
# Use the data dict on particles for custom state
particle.data["trail"] = []

# In your update loop:
for particle in emitter.particles:
    particle.data["trail"].append(particle.position.copy())
```

## Common Patterns

### Fade In/Out
```python
anim = engine.create_animation(AnimationConfig(
    keyframes=[
        Keyframe(time=0.0, values={"opacity": 0}),
        Keyframe(time=1.0, values={"opacity": 1}),
    ],
    duration=0.3,
    easing="ease_out_cubic",
))
```

### Bounce Effect
```python
anim = engine.create_animation(AnimationConfig(
    keyframes=[
        Keyframe(time=0.0, values={"scale": 0}),
        Keyframe(time=0.6, values={"scale": 1.1}),
        Keyframe(time=0.8, values={"scale": 0.95}),
        Keyframe(time=1.0, values={"scale": 1.0}),
    ],
    duration=0.5,
))
```

### Sequenced Animation
```python
queue = engine.create_queue("modal")
queue.animate(fade_in_config)
queue.wait(2.0)
queue.animate(fade_out_config)
queue.call(lambda: close_modal())
queue.start()
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Animation doesn't start | Call `anim.start()` before `engine.update()` |
| Values not updating | Check that `on_update` callback is set |
| Jittery animation | Use time-based update with proper delta time |
| Memory leak | Remove finished animations with `engine.remove_animation()` |
| Wrong easing | Check spelling with `list_easing_functions()` |
