# Physics Simulation Engine

A 2D physics simulation engine written in C++17 featuring rigid body dynamics, collision detection, and constraint solving.

## Features

- **Rigid Body Dynamics**: Position, velocity, acceleration, and angular motion
- **Collision Detection**: AABB (Axis-Aligned Bounding Box) and circle-circle collision detection
- **Collision Response**: Impulse-based collision response with friction and restitution
- **Physics World**: Add/remove bodies, step simulation, constraint solving
- **Gravity**: Configurable gravity vector
- **Friction**: Coulomb friction model
- **Restitution**: Bouncy collision response
- **Constraints**: Distance, pin, hinge, and weld constraints
- **Body Types**: Static, dynamic, and kinematic bodies
- **Sleep**: Automatic sleep for stationary bodies

## Building

```bash
mkdir build && cd build
cmake ..
make
```

## Running Tests

```bash
cd build
ctest --output-on-failure
```

## Quick Start

```cpp
#include "physics_simulation/physics_simulation.h"

using namespace physics_simulation;

WorldConfig config;
config.gravity = {0.0, -9.81};
World world(config);

// Create a ground
RigidBodyDef ground_def;
ground_def.type = BodyType::Static;
ground_def.position = {0.0, -10.0};
ground_def.radius = 10.0;
auto ground = world.create_body(ground_def);

// Create a ball
RigidBodyDef ball_def;
ball_def.type = BodyType::Dynamic;
ball_def.position = {0.0, 10.0};
ball_def.velocity = {2.0, 0.0};
ball_def.radius = 0.5;
ball_def.mass = 1.0;
ball_def.restitution = 0.7;
auto ball = world.create_body(ball_def);

// Simulate
for (int i = 0; i < 60; ++i) {
    world.step();
}
```

## Project Structure

```
physics-simulation-engine/
├── include/
│   └── physics_simulation/
│       ├── physics_simulation.h  # Main header (includes all)
│       ├── vector2d.h            # 2D vector math
│       ├── aabb.h                # Axis-aligned bounding box
│       ├── rigid_body.h          # Rigid body dynamics
│       ├── collision.h           # Collision detection
│       └── constraint.h          # Constraints & solver
├── src/
│   └── rigid_body.cpp            # Implementation
├── tests/
│   ├── test_physics.cpp          # Unit tests
│   └── CMakeLists.txt
├── examples/
│   ├── example_basic.cpp         # Basic simulation
│   ├── example_collision.cpp     # Collision demo
│   ├── example_gravity.cpp       # Gravity demo
│   └── CMakeLists.txt
├── docs/
│   ├── 01-RESEARCH.md
│   ├── 02-DESIGN.md
│   ├── 03-API.md
│   ├── 04-TESTING.md
│   └── 05-DEVELOPMENT.md
├── CMakeLists.txt
├── README.md
└── LEARNING_NOTES.md
```

## Dependencies

- C++17 compiler (GCC 7+, Clang 5+, MSVC 2017+)
- CMake 3.16+
- Google Test (for tests)

## License

MIT
