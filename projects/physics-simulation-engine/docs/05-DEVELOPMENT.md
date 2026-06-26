# Development Guide: Physics Simulation Engine

## Prerequisites
- C++17 compiler (GCC 7+, Clang 5+, MSVC 2017+)
- CMake 3.16+
- Google Test (installed via package manager or fetched by CMake)

## Building

### Standard Build
```bash
mkdir build && cd build
cmake ..
make -j$(nproc)
```

### With Tests
```bash
mkdir build && cd build
cmake -DPHYSICS_BUILD_TESTS=ON ..
make
ctest
```

### Clean Build
```bash
rm -rf build
mkdir build && cd build
cmake ..
make
```

## Project Structure

```
physics-simulation-engine/
├── include/
│   └── physics_simulation/    # Public headers
│       ├── physics_simulation.h  # Main include
│       ├── vector2d.h            # Vec2
│       ├── aabb.h                # AABB
│       ├── rigid_body.h          # RigidBody
│       ├── collision.h           # Collision functions
│       └── constraint.h          # Constraints
├── src/                        # Implementation
├── tests/                      # Unit tests
├── examples/                   # Demo programs
├── docs/                       # Documentation
├── CMakeLists.txt              # Root build config
├── README.md
└── LEARNING_NOTES.md
```

## Adding New Features

### 1. Add new header in include/physics_simulation/
```cpp
#pragma once
// New feature header
```

### 2. Update physics_simulation.h to include the new header
```cpp
#include "new_feature.h"
```

### 3. Add tests in tests/
```cpp
TEST(NewFeatureTest, TestName) {
    // Test code
}
```

### 4. Add example in examples/
```cpp
// Demo of new feature
```

## Coding Conventions

- **Namespaces**: `physics_simulation` for all code
- **Naming**: camelCase for variables, PascalCase for types
- **Headers**: pragma once, include guards not needed
- **Smart pointers**: Use std::shared_ptr for body ownership
- **Math**: Vec2 for all 2D vectors
- **Precision**: double for all calculations

## Debugging Tips

1. Print body positions/velocities after each step
2. Use AABB visualization to check collision detection
3. Check constraint satisfaction after solving
4. Monitor sleep status for performance issues
5. Verify energy conservation in elastic collisions

## Common Issues

### Bodies tunneling through each other
- Reduce time step size
- Enable continuous collision detection

### Jittering contacts
- Increase position iterations
- Check penetration slop settings

### Constraints not holding
- Increase velocity iterations
- Check anchor points and rest distances

### Performance issues
- Enable sleep for static bodies
- Use spatial partitioning for many bodies
- Reduce iteration counts where possible
