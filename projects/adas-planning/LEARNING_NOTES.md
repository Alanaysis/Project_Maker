# Learning Notes: ADAS Planning and Control System

## Table of Contents

1. [Path Planning Algorithms](#1-path-planning-algorithms)
2. [Control Theory](#2-control-theory)
3. [Vehicle Dynamics](#3-vehicle-dynamics)
4. [Trajectory Generation](#4-trajectory-generation)
5. [Implementation Insights](#5-implementation-insights)
6. [Key Takeaways](#6-key-takeaways)

---

## 1. Path Planning Algorithms

### 1.1 A* Algorithm

**Core Concept**: A* uses a best-first search with a heuristic function to find the shortest path.

**Key Formula**:
```
f(n) = g(n) + h(n)
```
- `g(n)`: Actual cost from start to node n
- `h(n)`: Heuristic estimated cost from n to goal
- `f(n)`: Total estimated cost

**What I Learned**:
- A* is optimal when the heuristic is admissible (never overestimates)
- The choice of heuristic significantly affects performance
- Manhattan distance is good for grid-based movement
- Euclidean distance allows diagonal movement
- Priority queues (heaps) are essential for efficient implementation

**Implementation Insights**:
```python
# Key data structures
open_list = []  # Priority queue (heap)
closed_set = set()  # Visited nodes
g_scores = {}  # Actual costs
came_from = {}  # Parent pointers
```

**Common Pitfalls**:
- Forgetting to check if neighbor is in closed set
- Not handling the case where start equals goal
- Using wrong heuristic for the movement model

### 1.2 Dijkstra's Algorithm

**Core Concept**: Dijkstra finds the shortest path by exploring nodes in order of distance from start.

**Key Difference from A***:
- No heuristic (h(n) = 0)
- Explores more nodes but guarantees optimality
- Better when no good heuristic is available

**When to Use Dijkstra**:
- When all edges have non-negative weights
- When you need shortest paths to all nodes
- When no admissible heuristic exists

### 1.3 RRT (Rapidly-exploring Random Tree)

**Core Concept**: RRT builds a tree by randomly sampling points and extending toward them.

**Key Steps**:
1. Sample random point (with goal bias)
2. Find nearest node in tree
3. Steer toward random point
4. Check collision
5. Add to tree if valid

**What I Learned**:
- RRT is probabilistically complete (finds path if one exists)
- Not optimal - paths may be suboptimal
- Good for high-dimensional spaces
- Goal bias improves convergence
- Step size affects exploration vs exploitation trade-off

**Implementation Insights**:
```python
# Goal bias: sample goal with probability p
if random.random() < goal_sample_rate:
    random_point = goal
else:
    random_point = random_point_in_space()
```

### 1.4 Theta* Algorithm

**Core Concept**: Theta* allows any-angle paths by checking line-of-sight between nodes.

**Key Advantage**:
- Produces smoother paths than grid-based A*
- Shorter paths due to any-angle movement
- Still optimal under certain conditions

**Implementation Insight**:
```python
# Line-of-sight check using Bresenham's algorithm
def line_of_sight(grid_map, start, end):
    x0, y0 = start
    x1, y1 = end
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    # ... Bresenham's line algorithm
```

---

## 2. Control Theory

### 2.1 PID Controller

**Core Concept**: PID combines three control terms to minimize error.

**Control Law**:
```
u(t) = Kp * e(t) + Ki * ∫e(t)dt + Kd * de(t)/dt
```

**What I Learned**:

**Proportional (P)**:
- Responds to current error
- Larger Kp = faster response
- Too large = oscillation

**Integral (I)**:
- Eliminates steady-state error
- Accumulates past errors
- Can cause windup

**Derivative (D)**:
- Predicts future error
- Reduces overshoot
- Sensitive to noise

**Tuning Rules**:
1. Start with only P
2. Increase P until oscillation
3. Add D to reduce oscillation
4. Add I to eliminate steady-state error

**Anti-Windup Techniques**:
```python
# Clamping
self.integral = np.clip(self.integral, -limit, limit)

# Conditional integration
if abs(output) < max_output:
    self.integral += error * dt
```

### 2.2 Stanley Controller

**Core Concept**: Stanley controller combines heading error and cross-track error for lateral control.

**Control Law**:
```
δ = θ_e + arctan(k * e_y / v)
```

**What I Learned**:
- Simple and intuitive
- Good for trajectory tracking
- Gain k affects convergence speed
- Speed in denominator prevents aggressive correction at low speeds

**Implementation Insight**:
```python
# Avoid division by zero
if abs(speed) < 0.1:
    speed = 0.1
```

### 2.3 MPC (Model Predictive Control)

**Core Concept**: MPC optimizes control inputs over a prediction horizon.

**Key Steps**:
1. Predict future states using model
2. Minimize cost function
3. Apply only first control input
4. Repeat at each time step

**Cost Function**:
```
J = Σ [x(k) - x_ref(k)]' Q [x(k) - x_ref(k)] + u(k)' R u(k)
```

**What I Learned**:
- Handles constraints explicitly
- Optimizes over time horizon
- Computationally expensive
- Requires accurate model

**Tuning Parameters**:
- Q: State cost (tracking error)
- R: Control cost (control effort)
- Rd: Control change cost (smoothness)
- Horizon: Prediction length

### 2.4 LQR (Linear Quadratic Regulator)

**Core Concept**: LQR is an optimal controller for linear systems.

**What I Learned**:
- Minimizes quadratic cost function
- Assumes linear system dynamics
- Provides optimal gain matrix
- Requires solving Riccati equation

---

## 3. Vehicle Dynamics

### 3.1 Point Mass Model

**State**: [x, y, v, θ]

**What I Learned**:
- Simplest model
- No dynamics constraints
- Good for basic path planning
- Not realistic for control

### 3.2 Bicycle Model

**State**: [x, y, θ, v]

**Key Equations**:
```
ẋ = v * cos(θ)
ẏ = v * sin(θ)
θ̇ = (v / L) * tan(δ)
```

**What I Learned**:
- Common model for autonomous driving
- Captures turning behavior
- Wheelbase L affects turning radius
- Good balance of accuracy and simplicity

### 3.3 Kinematic Model

**State**: [x, y, θ, v, δ]

**What I Learned**:
- Includes steering angle as state
- More accurate at low speeds
- Better for parking scenarios
- Can model steering dynamics

### 3.4 Dynamic Model

**State**: [x, y, θ, v_x, v_y, ω]

**What I Learned**:
- Includes lateral dynamics
- Tire force models (Pacejka)
- More accurate at high speeds
- Complex but realistic

---

## 4. Trajectory Generation

### 4.1 Cubic Spline Interpolation

**Core Concept**: Creates smooth curves through waypoints.

**What I Learned**:
- C² continuous (smooth curvature)
- Minimizes curvature variation
- Good for path smoothing
- scipy.interpolate.splrep/splev

**Implementation**:
```python
from scipy.interpolate import splrep, splev

# Fit cubic spline
tck = splrep(distances, coordinates, k=3)

# Evaluate at new points
values = splev(new_distances, tck)

# Get derivatives
derivatives = splev(new_distances, tck, der=1)
```

### 4.2 Velocity Profiling

**Core Concept**: Determines speed along a path considering constraints.

**Constraints**:
- Curvature limits (slow in turns)
- Acceleration limits
- Jerk limits (comfort)

**What I Learned**:
- Forward pass: limit by acceleration
- Backward pass: limit by deceleration
- Take minimum of all constraints

**Implementation**:
```python
# Forward pass
for i in range(1, len(path)):
    v_max_curvature = sqrt(max_accel / curvature[i])
    v_max_accel = sqrt(v_prev**2 + 2 * max_accel * ds)
    v[i] = min(v_max, v_max_curvature, v_max_accel)

# Backward pass
for i in range(len(path)-2, -1, -1):
    v_max_decel = sqrt(v_next**2 + 2 * max_decel * ds)
    v[i] = min(v[i], v_max_decel)
```

---

## 5. Implementation Insights

### 5.1 Grid Indexing

**Key Learning**: Be careful with (x, y) vs (row, col) indexing.

```python
# Grid access: grid[y, x] (row, col)
grid[y, x] = 1

# Position: (x, y) in functions
def get_neighbors(x, y):
    pass
```

### 5.2 Angle Normalization

**Key Learning**: Always normalize angles to [-π, π].

```python
angle = np.arctan2(np.sin(angle), np.cos(angle))
```

### 5.3 Priority Queues

**Key Learning**: Use heapq for efficient node selection.

```python
import heapq

# Push
heapq.heappush(open_list, (f_score, node))

# Pop
f_score, node = heapq.heappop(open_list)
```

### 5.4 NumPy Operations

**Key Learning**: Vectorize operations for performance.

```python
# Slow
for i in range(len(array)):
    result[i] = array[i] * 2

# Fast
result = array * 2
```

### 5.5 Matplotlib Visualization

**Key Learning**: Use LineCollection for efficient trajectory plotting.

```python
from matplotlib.collections import LineCollection

points = positions.reshape(-1, 1, 2)
segments = np.concatenate([points[:-1], points[1:]], axis=1)

lc = LineCollection(segments, cmap='viridis', linewidth=2)
lc.set_array(velocities[:-1])
ax.add_collection(lc)
```

---

## 6. Key Takeaways

### 6.1 Algorithm Selection

**Path Planning**:
- A* for optimal paths on grids
- Dijkstra when no good heuristic
- RRT for high-dimensional spaces
- Theta* for smooth any-angle paths

**Control**:
- PID for simple systems
- Stanley for lateral control
- MPC for complex constraints
- LQR for linear systems

### 6.2 Design Principles

1. **Modularity**: Separate planning, control, and visualization
2. **Extensibility**: Use abstract base classes
3. **Testability**: Write unit tests for each component
4. **Documentation**: Document algorithms and interfaces

### 6.3 Common Challenges

1. **Indexing Errors**: Grid vs coordinate systems
2. **Angle Wrapping**: Normalization issues
3. **Numerical Stability**: Division by zero, overflow
4. **Performance**: Loop vs vectorized operations

### 6.4 Best Practices

1. **Start Simple**: Begin with basic algorithms
2. **Test Early**: Write tests alongside code
3. **Visualize**: Plot results for verification
4. **Iterate**: Refine algorithms based on results

### 6.5 Learning Resources

1. **PythonRobotics**: Excellent reference implementations
2. **motion-planning**: Clear algorithm explanations
3. **Textbooks**: Planning algorithms, control theory
4. **Online Courses**: Robotics, autonomous driving

---

## 7. Future Learning Goals

### 7.1 Advanced Planning

- [ ] PRM (Probabilistic Roadmap)
- [ ] PRM* (Optimal PRM)
- [ ] Informed RRT*
- [ ] Dynamic obstacle avoidance

### 7.2 Advanced Control

- [ ] Adaptive PID
- [ ] Learning-based control
- [ ] Robust control
- [ ] Nonlinear MPC

### 7.3 Real-world Applications

- [ ] ROS2 integration
- [ ] Sensor simulation
- [ ] Hardware-in-the-loop
- [ ] Real vehicle testing

---

## 8. References

1. LaValle, S. M. (2006). Planning Algorithms. Cambridge University Press.
2. Thrun, S., Burgard, W., & Fox, D. (2005). Probabilistic Robotics. MIT Press.
3. Åström, K. J., & Murray, R. M. (2008). Feedback Systems. Princeton University Press.
4. PythonRobotics: https://github.com/AtsushiSakai/PythonRobotics
5. motion-planning: https://github.com/zhm-real/motion-planning
