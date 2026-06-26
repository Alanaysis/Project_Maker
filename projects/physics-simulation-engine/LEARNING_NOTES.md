# Learning Notes: Physics Simulation Engine

## Key Concepts Learned

### 1. Rigid Body Dynamics
- Position, velocity, acceleration form the core state
- Forces integrate to acceleration via F = ma
- Velocity integrates to position over time
- Angular dynamics follow similar principles with torque and inertia

### 2. Collision Detection
- **Broad phase**: AABB overlap test for quick rejection
- **Narrow phase**: Precise collision detection (AABB-AABB, circle-circle)
- **Penetration depth**: How much two objects overlap
- **Contact normal**: Direction to separate objects

### 3. Collision Response
- **Impulse-based**: Calculate impulse j and apply instantaneously
- **Restitution**: Controls bounciness (0 = no bounce, 1 = perfect elastic)
- **Friction**: Coulomb friction model limits tangential impulse
- **Relative velocity**: At contact point, considering rotation

### 4. Constraint Solving
- **Distance constraint**: Maintains fixed distance between two points
- **Pin constraint**: Anchors a point to a world location
- **Hinge constraint**: Allows rotation, prevents translation
- **Weld constraint**: Fully rigid connection
- **Sequential impulse solver**: Iteratively solves constraints

### 5. World Management
- **Gravity**: Applied as force each step (F = m * g)
- **Integration**: Euler integration for simplicity
- **Damping**: Linear and angular damping for stability
- **Sleep**: Bodies with low velocity are put to sleep for performance

## Algorithms

### Impulse Calculation
```
j = -(1 + e) * v_rel · n / (1/m1 + 1/m2 + (r1 × n)²/I1 + (r2 × n)²/I2)
```
Where:
- e = restitution coefficient
- v_rel = relative velocity at contact
- n = contact normal
- m = mass
- r = vector from center to contact
- I = inertia

### AABB Overlap Test
```
overlap_x = min(a.max.x, b.max.x) - max(a.min.x, b.min.x)
overlap_y = min(a.max.y, b.max.y) - max(a.min.y, b.min.y)
collides = overlap_x > 0 && overlap_y > 0
```

### Circle Overlap Test
```
dist = |center_b - center_a|
collides = dist < radius_a + radius_b
```

## Design Decisions

1. **Header-only for math**: Vector2D, AABB, and collision functions are header-only for performance
2. **Shared pointers for bodies**: Enables constraint references and ownership
3. **Sequential constraint solving**: Simpler than parallel, sufficient for most cases
4. **Euler integration**: Simple and predictable, though not symplectic
5. **Fixed time step**: Easier to reason about, supports variable dt

## Challenges

1. **Stability**: Large timesteps cause instability; need smaller steps or implicit integration
2. **Tunneling**: Fast objects can pass through walls; need continuous collision detection
3. **Jitter**: Small gaps between objects cause oscillation; need position correction
4. **Constraint conflicts**: Multiple constraints on same body can conflict

## Future Improvements

1. Spatial partitioning (quadtree) for broad phase
2. Continuous collision detection
3. Joint limits and motors
4. Ray casting and shape casting
5. Contact caching for better stability
6. Symplectic Euler or Verlet integration
7. Sub-stepping for better accuracy
