# Testing Strategy: Physics Simulation Engine

## Test Framework
Google Test (gtest) for C++ unit testing.

## Test Categories

### 1. Vector Math Tests (Vec2Test)
- Addition, subtraction, scalar multiplication
- Dot product, cross product
- Length, length squared, normalization
- Static methods (zero, unit vectors)

### 2. AABB Tests (AABBTest)
- Center, size, half_size calculations
- Point containment
- Intersection detection
- Merge and expand operations
- Validity check

### 3. Collision Detection Tests (CollisionTest)
- AABB vs AABB (collision and non-collision cases)
- Circle vs circle (collision, touching, non-collision)
- AABB vs circle (collision, inside, non-collision)
- Contact point and normal accuracy
- Penetration depth calculation

### 4. RigidBody Tests (RigidBodyTest)
- Body creation (dynamic, static, kinematic)
- Property accessors and setters
- Force and impulse application
- Integration (Euler)
- Static body immunity to forces
- AABB computation
- Mass change and inertia update
- Velocity at point calculation
- Clear forces
- User data storage

### 5. World Tests (WorldTest)
- World creation and configuration
- Body creation and destruction
- Gravity simulation
- Multi-body simulation
- Static body stability
- Collision callback invocation
- Custom time step
- Damping effects
- Restitution (bouncing)
- Body ID uniqueness
- Clear and reset

### 6. Constraint Tests (ConstraintTest)
- Pin constraint (anchoring)
- Distance constraint (maintaining distance)
- Hinge constraint (rotational joint)
- Constraint solver
- Constraint destruction
- Kinematic body behavior
- Sensor body behavior
- Multiple time step stability

## Test Coverage Goals
- All public API methods tested
- Edge cases (zero mass, static bodies, touching objects)
- Numerical accuracy (double precision)
- Boundary conditions (sleep thresholds, damping)

## Running Tests
```bash
cd build
ctest --output-on-failure
```
