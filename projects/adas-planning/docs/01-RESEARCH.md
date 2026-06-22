# Research: ADAS Planning and Control

## Overview

This document summarizes the research conducted before implementing the ADAS Planning and Control system. It covers the fundamental concepts, algorithms, and design decisions.

## 1. Autonomous Driving Architecture

### Typical ADAS Architecture

An autonomous driving system typically consists of:

1. **Perception**: Understanding the environment (sensors, object detection)
2. **Localization**: Determining vehicle position (GPS, SLAM)
3. **Planning**: Deciding where to go (path planning, motion planning)
4. **Control**: Executing the plan (steering, throttle, braking)

This project focuses on the **Planning** and **Control** components.

### Core Loop

```
Map Information → Path Planning → Trajectory Generation → Control Execution → State Feedback
```

## 2. Path Planning Algorithms

### 2.1 A* Algorithm

**Overview**: A* is a best-first search algorithm that finds the shortest path between nodes in a graph.

**Key Concepts**:
- Uses a heuristic function to guide search
- Combines actual cost (g) and estimated cost (h)
- f(n) = g(n) + h(n)
- Optimal when heuristic is admissible

**Heuristics**:
- Manhattan distance: |x1-x2| + |y1-y2| (grid movement)
- Euclidean distance: sqrt((x1-x2)² + (y1-y2)²) (any direction)
- Chebyshev distance: max(|x1-x2|, |y1-y2|) (8-connected grid)

**Complexity**:
- Time: O(b^d) where b is branching factor, d is depth
- Space: O(b^d) for open and closed sets

### 2.2 Dijkstra's Algorithm

**Overview**: Dijkstra finds the shortest path from a source to all reachable nodes.

**Key Differences from A***:
- No heuristic (h(n) = 0)
- Explores nodes in order of distance from start
- Guaranteed optimal but explores more nodes

**When to Use**:
- When no good heuristic is available
- When all edges have non-negative weights
- When you need shortest paths to all nodes

### 2.3 RRT (Rapidly-exploring Random Tree)

**Overview**: RRT is a sampling-based algorithm for path planning.

**Key Concepts**:
- Randomly samples points in configuration space
- Builds a tree by extending toward samples
- Probabilistically complete (finds path if one exists)
- Good for high-dimensional spaces

**Advantages**:
- Works in continuous spaces
- Handles complex constraints
- Fast for many problems

**Disadvantages**:
- Not optimal
- Paths may be jerky
- Random nature can be inefficient

### 2.4 Theta* Algorithm

**Overview**: Theta* is an any-angle path planning algorithm.

**Key Concepts**:
- Extension of A* that allows any-angle paths
- Uses line-of-sight checks
- Produces smoother paths than grid-based A*

**Advantages**:
- Shorter paths than A*
- Smoother trajectories
- Still optimal under certain conditions

## 3. Control Algorithms

### 3.1 PID Controller

**Overview**: PID is the most widely used control algorithm.

**Components**:
- **Proportional (P)**: Responds to current error
- **Integral (I)**: Eliminates steady-state error
- **Derivative (D)**: Reduces overshoot and oscillation

**Control Law**:
```
u(t) = Kp * e(t) + Ki * ∫e(t)dt + Kd * de(t)/dt
```

**Tuning Methods**:
- Manual tuning
- Ziegler-Nichols method
- Cohen-Coon method
- Auto-tuning algorithms

**Anti-Windup**:
- Prevents integral term from accumulating too much
- Clamping: Limit integral magnitude
- Back-calculation: Adjust integral based on output saturation

### 3.2 Stanley Controller

**Overview**: Stanley controller is designed for lateral control of autonomous vehicles.

**Control Law**:
```
δ = θ_e + arctan(k * e_y / v)
```

Where:
- δ: Steering angle
- θ_e: Heading error
- e_y: Cross-track error
- k: Gain parameter
- v: Vehicle speed

**Advantages**:
- Simple implementation
- Intuitive tuning
- Good performance at moderate speeds

### 3.3 MPC (Model Predictive Control)

**Overview**: MPC optimizes control inputs over a prediction horizon.

**Key Concepts**:
- Predicts future states using vehicle model
- Minimizes cost function over horizon
- Applies only first control input
- Repeats at each time step

**Cost Function**:
```
J = Σ [x(k) - x_ref(k)]' Q [x(k) - x_ref(k)] + u(k)' R u(k)
```

**Advantages**:
- Handles constraints explicitly
- Optimizes over time horizon
- Can incorporate complex objectives

**Disadvantages**:
- Computationally expensive
- Requires accurate model
- Tuning can be complex

### 3.4 LQR (Linear Quadratic Regulator)

**Overview**: LQR is an optimal controller for linear systems.

**Key Concepts**:
- Minimizes quadratic cost function
- Assumes linear system dynamics
- Provides optimal gain matrix

**Cost Function**:
```
J = ∫ [x(t)' Q x(t) + u(t)' R u(t)] dt
```

## 4. Vehicle Models

### 4.1 Point Mass Model

**State**: [x, y, v, θ]

**Assumptions**:
- Vehicle is a point
- No dynamics constraints
- Instantaneous velocity changes

### 4.2 Bicycle Model

**State**: [x, y, θ, v]

**Assumptions**:
- Two wheels (front and rear)
- No lateral slip
- Constant wheelbase

**Dynamics**:
```
ẋ = v * cos(θ)
ẏ = v * sin(θ)
θ̇ = (v / L) * tan(δ)
```

### 4.3 Kinematic Bicycle Model

**State**: [x, y, θ, v, δ]

**Extensions**:
- Includes steering angle as state
- More accurate at low speeds
- Better for parking scenarios

### 4.4 Dynamic Bicycle Model

**State**: [x, y, θ, v_x, v_y, ω]

**Extensions**:
- Includes lateral dynamics
- Tire force models
- More accurate at high speeds

## 5. Trajectory Generation

### 5.1 Cubic Spline Interpolation

**Overview**: Creates smooth curves through waypoints.

**Properties**:
- C² continuous (smooth curvature)
- Minimizes curvature variation
- Good for path smoothing

### 5.2 Velocity Profiling

**Overview**: Determines speed along a path.

**Considerations**:
- Curvature limits (slow in turns)
- Acceleration limits
- Jerk limits (comfort)

## 6. Simulation Environment

### 6.1 Grid-based Representation

**Advantages**:
- Simple implementation
- Efficient collision checking
- Easy to visualize

**Disadvantages**:
- Discretization errors
- Memory intensive for large maps
- Limited to 2D

### 6.2 Continuous Representation

**Advantages**:
- More accurate
- Better for complex geometries
- Supports any-angle planning

**Disadvantages**:
- More complex implementation
- Harder collision checking
- May require sampling

## 7. Existing Projects

### 7.1 PythonRobotics

**URL**: https://github.com/AtsushiSakai/PythonRobotics

**Features**:
- Comprehensive robotics algorithms
- Well-documented code
- Visualization examples

**Algorithms Included**:
- Path planning (A*, Dijkstra, RRT, etc.)
- Localization (EKF, UKF, Particle Filter)
- SLAM (EKF SLAM, Graph SLAM)
- Path tracking (Stanley, LQR, MPC)

### 7.2 motion-planning

**URL**: https://github.com/zhm-real/motion-planning

**Features**:
- Motion planning algorithms
- Clear implementations
- Good visualizations

### 7.3 tuplan_garage

**URL**: https://github.com/motional/tuplan_garage

**Features**:
- Real-world autonomous driving
- NuPlan dataset support
- Production-quality code

## 8. Design Decisions

Based on research, the following design decisions were made:

1. **Grid-based Environment**: Simple and efficient for demonstration
2. **A* as Primary Planner**: Optimal and well-understood
3. **PID and Stanley Controllers**: Common and effective for trajectory tracking
4. **Bicycle Model**: Good balance of accuracy and simplicity
5. **Modular Architecture**: Easy to extend and test
6. **Matplotlib Visualization**: Standard and widely available

## 9. References

1. Hart, P. E., Nilsson, N. J., & Raphael, B. (1968). A formal basis for the heuristic determination of minimum cost paths.
2. Dijkstra, E. W. (1959). A note on two problems in connexion with graphs.
3. LaValle, S. M. (1998). Rapidly-exploring random trees: A new tool for path planning.
4. Nash, A., Daniel, K., Koenig, S., & Felner, A. (2010). Theta*: Any-angle path planning on grids.
5. Hoffmann, G. M., Tomlin, C. J., Montemerlo, M., & Thrun, S. (2007). Autonomous automobile trajectory tracking for off-road driving.
6. Kong, J., Pfeiffer, M., Schildbach, G., & Borrelli, F. (2015). Kinematic and dynamic vehicle models for autonomous driving control design.
