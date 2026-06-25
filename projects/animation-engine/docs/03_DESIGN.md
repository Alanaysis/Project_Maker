# Animation Engine - Design

## Architecture Overview

```
AnimationEngine (Orchestrator)
    |
    +-- KeyframeAnimation    (Multi-step property animation)
    +-- Tween                (Simple numeric interpolation)
    +-- AnimationQueue        (Sequential execution)
    +-- Skeleton + SkeletalAnimation  (Bone-based animation)
    +-- ParticleSystem        (Particle effects)
    +-- SkinnedMesh           (Mesh deformation)
```

## Module Structure

```
animation_engine/
    __init__.py       - Public API exports
    types.py          - Data classes (Vector3, Color, Keyframe, configs)
    easing.py         - 30+ easing functions + registry
    utils.py          - Timer, FrameRateCounter, clamp, lerp
    keyframe.py       - KeyframeAnimation class
    tween.py          - Tween class
    skeleton.py       - Bone, Skeleton, SkinWeight, SkinnedMesh, SkeletalAnimation
    particle.py       - Particle, ParticleEmitter, ParticleSystem
    queue.py          - AnimationQueue
    engine.py         - AnimationEngine (main orchestrator)
```

## Key Design Decisions

### 1. Time-Based Animation
All animations use real time (seconds) rather than frame counts. This
ensures consistent behavior regardless of frame rate.

```python
def update(self, dt: float):
    self._elapsed += dt
    t = self._elapsed / self._duration
    # ... interpolate
```

### 2. Normalized Time
Keyframes use normalized time [0, 1] internally. The actual time is
computed from duration and iteration.

### 3. Easing Function Registry
Easing functions are registered by name for easy lookup. Supports
both Python-style (`ease_in_quad`) and CSS-style (`ease-in-quad`) names.

```python
EASING_FUNCTIONS = {
    "linear": linear,
    "ease_in_quad": ease_in_quad,
    # ...
}

def get_easing_function(name: str) -> EasingFunction:
    normalized = name.replace("-", "_").lower()
    return EASING_FUNCTIONS[normalized]
```

### 4. Type-Based Interpolation
The `lerp_value` function dispatches interpolation based on value type:
- `int/float` -> scalar lerp
- `Vector3` -> vector lerp
- `Color` -> color lerp
- `list` -> element-wise lerp
- Other -> discrete (snap at t >= 0.5)

### 5. Composition Over Inheritance
Each animation type is self-contained. The engine composes them rather
than using a deep inheritance hierarchy.

### 6. Callbacks
All animations support `on_update` and `on_complete` callbacks for
reactive programming patterns.

## Data Flow

```
Application Loop
    |
    v
engine.update(dt)
    |
    +-> Update all KeyframeAnimations
    |       interpolate(t) -> current_values
    |
    +-> Update all Tweens
    |       lerp(from, to, eased_t) -> current_values
    |
    +-> Update all AnimationQueues
    |       process current item
    |
    +-> Update SkeletalAnimations
    |       apply bone keyframes -> skeleton.update()
    |
    +-> Update ParticleSystems
    |       emit particles, update physics, remove dead
    |
    +-> Update SkinnedMeshes
            deform(vertices, skeleton)
```

## Class Diagrams

### Keyframe Animation
```
KeyframeAnimation
    - _keyframes: List[Keyframe]  (sorted by time)
    - _duration: float
    - _iterations: int
    - _direction: str
    - _current_values: Dict[str, Any]
    + start()
    + stop()
    + pause() / resume()
    + update(dt) -> Dict
    + seek(time) -> Dict
    + evaluate_at(t) -> Dict
```

### Tween
```
Tween
    - _from: Dict[str, float]
    - _to: Dict[str, float]
    - _duration: float
    - _easing: EasingFunction
    + start() -> Tween
    + update(dt) -> Dict
    + then(next_tween) -> Tween
    + seek(t) -> Dict
```

### Skeleton
```
Bone
    - name: str
    - parent: Optional[Bone]
    - children: List[Bone]
    - position/rotation/scale: Vector3
    - world_position/world_rotation/world_scale: Vector3
    - rest_position/rest_rotation/rest_scale: Vector3

Skeleton
    - bones: List[Bone]
    + add_bone(name, parent, ...) -> Bone
    + update()  (propagate world transforms)
    + get_bone_transforms() -> List[Matrix4x4]
```

### Particle System
```
ParticleEmitter
    - config: EmitterConfig
    - particles: List[Particle]
    + update(dt)
    + burst_emit(count)

ParticleSystem
    - _emitters: Dict[str, ParticleEmitter]
    + add_emitter(name, emitter)
    + update(dt)
```

## Error Handling

- Invalid keyframe times raise `ValueError`
- Unknown easing function names raise `ValueError`
- Mismatched tween keys raise `ValueError`
- Duplicate bone names raise `ValueError`
- All validation happens at construction time (fail fast)

## Thread Safety

The current implementation is NOT thread-safe. All animation updates
should happen on the main thread. For multi-threaded usage, external
synchronization is required.
