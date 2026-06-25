# Animation Engine - Implementation

## Implementation Summary

### Easing Functions (`easing.py`)
- 31 easing functions across 11 families
- Each function takes `t: float` in [0, 1] and returns eased value
- Registry maps string names to functions
- Supports both `ease_in_quad` and `ease-in-quad` naming

### Keyframe Animation (`keyframe.py`)
- Keyframes sorted by time at construction
- Segment-based interpolation: find surrounding keyframes, compute local t
- Per-segment easing via keyframe.easing attribute
- Direction support: normal, reverse, alternate, alternate-reverse
- Iteration tracking with automatic completion

### Tween (`tween.py`)
- Simple from/to numeric interpolation
- Easing applied to normalized progress
- Chaining via `then()` method
- `sequence()` and `parallel()` static helpers
- `remaining` property for time tracking

### Skeleton (`skeleton.py`)
- Tree-based bone hierarchy
- Local transforms (position, rotation, scale as Euler angles)
- World transforms computed by walking the hierarchy
- Rest (bind) pose stored separately
- Inverse bind transform computation for skinning
- 4x4 transform matrix generation (simplified)

### Skinning (`skeleton.py`)
- `SkinWeight`: Up to 4 bone influences per vertex
- `SkinnedMesh`: Rest positions + skin weights + current positions
- Deformation via blended transform matrices
- Weight normalization

### Skeletal Animation (`skeleton.py`)
- Per-bone keyframe sequences
- Time wrapping for looping
- Per-keyframe easing
- Direct application to skeleton

### Particle System (`particle.py`)
- `Particle`: Position, velocity, acceleration, color, size, rotation, lifetime
- `ParticleEmitter`: Rate-based emission with spread
- `ParticleSystem`: Multiple named emitters
- Emitter shapes: point, circle, sphere
- Dead particle reuse for performance

### Animation Queue (`queue.py`)
- Sequential item processing
- Item types: animation, tween, wait, callback
- Loop mode for repeating sequences
- Method chaining API

### Animation Engine (`engine.py`)
- Central registry for all animation types
- Unified `update(dt)` call
- Time scaling, pause/resume/stop
- FPS and frame time tracking
- Global update callback
- Stats reporting

## Key Algorithms

### Keyframe Interpolation
```python
def _interpolate(self, t):
    # Find surrounding keyframes
    for i in range(len(kfs) - 1):
        if kfs[i].time <= t <= kfs[i+1].time:
            seg_idx = i
            break

    # Local t within segment
    local_t = (t - kfs[seg_idx].time) / (kfs[seg_idx+1].time - kfs[seg_idx].time)

    # Apply segment easing
    eased_t = easing_fn(local_t)

    # Interpolate each property
    for prop in properties:
        values[prop] = lerp(kfs[seg_idx].values[prop], kfs[seg_idx+1].values[prop], eased_t)
```

### Direction Handling
```python
def normalize_time(elapsed, duration, direction, iteration):
    t = clamp(elapsed / duration)
    if direction == "alternate":
        return t if iteration % 2 == 0 else 1 - t
    elif direction == "reverse":
        return 1 - t
    return t
```

### Skeletal Transform Propagation
```python
def update_world_transform(self):
    if self.parent is None:
        self.world_position = self.position
    else:
        self.world_position = self.parent.world_position + self.position
    # Similar for rotation and scale
```

### Mesh Skinning
```python
def deform(self, skeleton):
    bone_transforms = skeleton.get_bone_transforms()
    for i, vertex in enumerate(rest_positions):
        blended = skin_weights[i].get_blended_transform(bone_transforms)
        current_positions[i] = apply_matrix(blended, vertex)
```

## Performance Considerations

1. **Particle pool**: Dead particles are reused instead of creating new objects
2. **Sorted keyframes**: Keyframes sorted once at construction
3. **Lazy cleanup**: Dead particles removed only when list grows large
4. **Minimal allocations**: `current_values` dict reused across frames
5. **Early exit**: Finished animations skip update

## Testing Strategy

- Unit tests for each module (easing, types, keyframe, tween, skeleton, particle, queue, engine)
- Boundary value testing for easing functions (t=0, t=1)
- Monotonicity tests for ease-in/ease-out functions
- Integration tests in engine combining multiple animation types
- Edge cases: empty keyframes, zero duration, infinite iterations
