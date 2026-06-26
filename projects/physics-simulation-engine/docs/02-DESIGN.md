# Design Document: Physics Simulation Engine

## Architecture

### Core Components

1. **Vector2D** - 2D vector math operations
2. **AABB** - Axis-aligned bounding box for spatial queries
3. **RigidBody** - Physics body state and behavior
4. **Collision** - Collision detection algorithms
5. **Constraint** - Joint systems (distance, pin, hinge, weld)
6. **World** - Simulation manager

### Data Flow

```
World::step()
  ├── apply_gravity()    - Add gravity force to dynamic bodies
  ├── integrate()        - Update velocities and positions
  ├── detect_collisions() - Find overlapping body pairs
  ├── resolve_collisions() - Apply impulse response
  ├── solve_constraints() - Satisfy joint constraints
  └── correct_positions() - Fix penetration
```

### Design Patterns

- **Composition**: World composed of bodies and constraints
- **Factory**: World creates bodies and constraints
- **Observer**: Collision callback pattern
- **Strategy**: Constraint solver as pluggable component

## API Design

### Body Creation
```cpp
RigidBodyDef def;
def.type = BodyType::Dynamic;
def.position = {x, y};
def.radius = r;
def.mass = m;
auto body = world.create_body(def);
```

### Simulation
```cpp
world.step(dt);  // Fixed or custom timestep
```

### Force Application
```cpp
body->apply_force({fx, fy});
body->apply_impulse({ix, iy});
body->apply_torque(torque);
```

## Performance Considerations

- Use header-only for math operations
- Shared pointers for body ownership
- Sequential constraint solving for simplicity
- Sleep for idle bodies
- AABB broad phase reduces narrow phase checks

## Future Extensions

- Spatial hashing for broad phase
- Continuous collision detection
- Ray casting
- Shape casting
- Joint limits and motors
