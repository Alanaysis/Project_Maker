# Research Notes: Physics Simulation Engines

## Overview
This research explores 2D physics engine architecture for game development and simulation.

## Key Topics

### 1. Rigid Body Physics
- **State**: Position (x, y), rotation (θ), velocity (vx, vy), angular velocity (ω)
- **Forces**: Gravity, friction, spring forces, user-applied forces
- **Integration**: Euler, Verlet, RK4 methods
- **Mass properties**: Mass, inertia tensor, center of mass

### 2. Collision Detection
- **Broad phase**: Sweep and prune, spatial hashing, BVH trees
- **Narrow phase**: GJK, EPA, SAT (Separating Axis Theorem)
- **2D specific**: AABB overlap, circle-circle distance, line-segment intersection

### 3. Collision Response
- **Impulse method**: Instantaneous velocity change
- **Contact constraint**: Position-based correction
- **Restitution**: Energy retention in collisions
- **Friction**: Static and kinetic friction models

### 4. Constraints
- **Distance**: Fixed length between two points
- **Pivot/Pin**: Anchored to world point
- **Hinge/Revolute**: Rotational joint
- **Weld**: Rigid connection
- **Spring**: Elastic constraint

### 5. Optimization
- **Sleep**: Stop simulating stationary bodies
- **Spatial partitioning**: Reduce collision check pairs
- **Fixed timestep**: Deterministic simulation
- **Caching**: Contact point reuse

## References
- Erin Catto - Box2D (gafferongames.com)
- David Eberly - Physics Simulation
- Game Physics Cookbook by David Geary
- Real-Time Collision Detection by Christer Ericson
