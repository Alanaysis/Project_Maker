# Implementation Guide: ADAS Planning and Control System

## 1. Implementation Overview

This document provides detailed implementation guidance for each module in the ADAS Planning and Control System.

## 2. Environment Module Implementation

### 2.1 GridMap Class

**Key Implementation Details**:

```python
class GridMap:
    def __init__(self, width: int, height: int, resolution: float = 1.0):
        self.width = width
        self.height = height
        self.resolution = resolution
        self.grid = np.zeros((height, width), dtype=np.int8)
```

**Important Methods**:

1. **`add_obstacle(x, y)`**: Sets grid cell to obstacle value
2. **`is_obstacle(x, y)`**: Checks if cell is an obstacle
3. **`get_neighbors(x, y, allow_diagonal)`**: Returns valid neighboring cells
4. **`random(width, height, obstacle_density, seed)`**: Creates random grid

**Optimization Tips**:
- Use numpy arrays for efficient storage
- Vectorize operations where possible
- Cache frequently accessed values

### 2.2 SimulationEnvironment Class

**Key Implementation Details**:

```python
class SimulationEnvironment:
    def __init__(self, grid_map, start, goal, dt=0.1):
        self.grid_map = grid_map
        self.start = start
        self.goal = goal
        self.vehicle_position = np.array(start, dtype=float)
        self.vehicle_heading = 0.0
        self.vehicle_speed = 0.0
        self.dt = dt
```

**Important Methods**:

1. **`step(steering, acceleration)`**: Executes one simulation step
2. **`is_collision()`**: Checks for collision with obstacles
3. **`is_goal_reached(threshold)`**: Checks if goal is reached
4. **`reset()`**: Resets environment to initial state

## 3. Planner Module Implementation

### 3.1 A* Algorithm

**Core Algorithm**:

```python
def plan(self, grid_map, start, goal):
    # Initialize open list with start node
    open_list = [(heuristic(start, goal), start)]
    g_scores = {start: 0}
    came_from = {}

    while open_list:
        # Get node with lowest f-score
        current_f, current = heapq.heappop(open_list)

        # Goal reached
        if current == goal:
            return reconstruct_path(came_from, current)

        # Explore neighbors
        for neighbor in grid_map.get_neighbors(*current):
            tentative_g = g_scores[current] + distance(current, neighbor)

            if tentative_g < g_scores.get(neighbor, float('inf')):
                came_from[neighbor] = current
                g_scores[neighbor] = tentative_g
                f_score = tentative_g + heuristic(neighbor, goal)
                heapq.heappush(open_list, (f_score, neighbor))

    return None  # No path found
```

**Key Points**:
- Use priority queue (heapq) for efficient node selection
- Track g-scores to find optimal paths
- Use closed set to avoid revisiting nodes
- Reconstruct path by following parent pointers

### 3.2 Dijkstra's Algorithm

**Difference from A***:
- No heuristic (h(n) = 0)
- f(n) = g(n)
- Explores nodes in order of distance from start

### 3.3 RRT Algorithm

**Core Algorithm**:

```python
def plan(self, grid_map, start, goal):
    tree = {0: (start, None)}  # node_id: (position, parent_id)

    for i in range(max_iterations):
        # Sample random point (with goal bias)
        if random() < goal_sample_rate:
            random_point = goal
        else:
            random_point = random_point_in_space()

        # Find nearest node in tree
        nearest_id = find_nearest(tree, random_point)

        # Steer toward random point
        new_point = steer(tree[nearest_id], random_point)

        # Check if valid
        if is_collision_free(grid_map, tree[nearest_id], new_point):
            # Add to tree
            new_id = len(tree)
            tree[new_id] = (new_point, nearest_id)

            # Check if goal reached
            if distance(new_point, goal) < threshold:
                return reconstruct_path(tree, new_id)

    return None
```

**Key Points**:
- Goal bias improves convergence
- Step size limits expansion
- Collision checking along edges

## 4. Controller Module Implementation

### 4.1 PID Controller

**Core Algorithm**:

```python
class PIDController:
    def compute(self, error, dt):
        # Proportional term
        P = self.Kp * error

        # Integral term (with anti-windup)
        self.integral += error * dt
        if self.integral_limits:
            self.integral = np.clip(self.integral, *self.integral_limits)
        I = self.Ki * self.integral

        # Derivative term
        if dt > 0:
            derivative = (error - self.prev_error) / dt
        else:
            derivative = 0.0
        D = self.Kd * derivative

        # Total output
        output = P + I + D

        # Apply output limits
        if self.output_limits:
            output = np.clip(output, *self.output_limits)

        # Update state
        self.prev_error = error

        return output
```

**Anti-Windup Techniques**:
1. **Clamping**: Limit integral magnitude
2. **Back-calculation**: Adjust integral based on output saturation
3. **Conditional integration**: Only integrate when output is not saturated

### 4.2 Stanley Controller

**Core Algorithm**:

```python
def compute_steering(self, current_pos, current_heading, path, speed):
    # Find nearest point on path
    nearest_idx = find_nearest(path, current_pos)

    # Get path heading
    path_heading = get_heading(path[nearest_idx], path[nearest_idx + 1])

    # Compute heading error
    heading_error = path_heading - current_heading

    # Compute cross-track error
    cross_track_error = compute_cross_track_error(current_pos, path[nearest_idx], path_heading)

    # Stanley control law
    if abs(speed) < 0.1:
        speed = 0.1  # Avoid division by zero

    steering = heading_error + np.arctan2(k * cross_track_error, speed)

    # Limit steering
    steering = np.clip(steering, -max_steer, max_steer)

    return steering
```

### 4.3 MPC Controller

**Core Algorithm**:

```python
def compute(self, state, reference_trajectory, speed):
    # Initialize control sequence
    controls = np.zeros(horizon)

    # Optimization loop
    for _ in range(num_iterations):
        # Compute gradient
        gradient = compute_gradient(state, controls, reference_trajectory, speed)

        # Update controls
        controls -= learning_rate * gradient

        # Apply limits
        controls = np.clip(controls, -max_steer, max_steer)

    # Return first control input
    return controls[0]

def compute_cost(self, state, controls, reference, speed):
    cost = 0.0
    current_state = state.copy()

    for t in range(horizon):
        # Predict next state
        next_state = predict_state(current_state, controls[t], speed)

        # Tracking error cost
        error = next_state - reference[t]
        cost += error.T @ Q @ error

        # Control effort cost
        cost += controls[t] * R * controls[t]

        # Control change cost
        if t > 0:
            delta = controls[t] - controls[t-1]
            cost += delta * Rd * delta

        current_state = next_state

    return cost
```

## 5. Vehicle Model Implementation

### 5.1 Bicycle Model

**Core Dynamics**:

```python
def update(self, state, control, dt):
    x, y, theta, v = state
    accel, steering = control

    # Update speed
    v_new = v + accel * dt
    v_new = np.clip(v_new, 0, max_speed)

    # Update heading
    theta_dot = (v_new / wheelbase) * np.tan(steering)
    theta_new = theta + theta_dot * dt

    # Update position
    x_new = x + v_new * np.cos(theta_new) * dt
    y_new = y + v_new * np.sin(theta_new) * dt

    return np.array([x_new, y_new, theta_new, v_new])
```

## 6. Trajectory Module Implementation

### 6.1 Cubic Spline Interpolation

**Using scipy**:

```python
from scipy.interpolate import splrep, splev

# Fit cubic spline
tck_x = splrep(distances, x_coords, k=3)
tck_y = splrep(distances, y_coords, k=3)

# Evaluate at new points
x_new = splev(s_new, tck_x)
y_new = splev(s_new, tck_y)

# Get derivatives (for heading and curvature)
dx_ds = splev(s_new, tck_x, der=1)
dy_ds = splev(s_new, tck_y, der=1)
heading = np.arctan2(dy_ds, dx_ds)
```

### 6.2 Velocity Profiling

**Forward Pass** (acceleration limits):

```python
for i in range(1, len(trajectory)):
    # Maximum velocity based on curvature
    v_max_curvature = sqrt(max_accel / curvature[i])

    # Maximum velocity based on acceleration
    v_max_accel = sqrt(v_prev^2 + 2 * max_accel * ds)

    # Take minimum
    v[i] = min(v_max, v_max_curvature, v_max_accel)
```

**Backward Pass** (deceleration limits):

```python
for i in range(len(trajectory)-2, -1, -1):
    v_max_decel = sqrt(v_next^2 + 2 * max_decel * ds)
    v[i] = min(v[i], v_max_decel)
```

## 7. Visualization Implementation

### 7.1 Grid Map Visualization

```python
def plot_grid_map(grid_map, ax=None):
    if ax is None:
        fig, ax = plt.subplots()

    # Create obstacle mask
    obstacle_mask = grid_map.grid == CellType.OBSTACLE.value

    # Plot obstacles
    ax.imshow(obstacle_mask.T, origin='lower', cmap='binary',
              extent=[0, grid_map.width, 0, grid_map.height])

    # Add grid lines
    ax.grid(True, linewidth=0.5, alpha=0.3)
```

### 7.2 Trajectory Visualization with Velocity

```python
def plot_trajectory(trajectory, ax=None, show_velocity=True):
    positions = trajectory.get_positions()

    if show_velocity:
        # Color by velocity
        velocities = trajectory.get_velocities()
        points = positions.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)

        lc = LineCollection(segments, cmap='viridis', linewidth=2)
        lc.set_array(velocities[:-1])
        ax.add_collection(lc)

        # Add colorbar
        plt.colorbar(lc, ax=ax, label='Velocity (m/s)')
```

## 8. Testing Implementation

### 8.1 Unit Test Example

```python
class TestAStarPlanner:
    def test_simple_path(self):
        grid_map = GridMap(10, 10)
        planner = AStarPlanner()

        path = planner.plan(grid_map, (0, 0), (9, 9))

        assert path is not None
        assert path[0] == (0, 0)
        assert path[-1] == (9, 9)

    def test_no_path(self):
        grid_map = GridMap(10, 10)
        # Create complete wall
        for y in range(10):
            grid_map.add_obstacle(5, y)

        planner = AStarPlanner()
        path = planner.plan(grid_map, (0, 0), (9, 9))

        assert path is None
```

### 8.2 Integration Test Example

```python
def test_end_to_end():
    # Setup
    grid_map = GridMap(20, 20)
    planner = AStarPlanner()
    controller = PIDController(Kp=1.0, Ki=0.01, Kd=0.5)

    # Plan path
    path = planner.plan(grid_map, (0, 0), (19, 19))
    assert path is not None

    # Generate trajectory
    generator = TrajectoryGenerator()
    trajectory = generator.generate([(p[0], p[1]) for p in path])

    # Run simulation
    env = SimulationEnvironment(grid_map, (0, 0), (19, 19))
    for _ in range(1000):
        error = compute_error(env, trajectory)
        steering = controller.compute(error, 0.1)
        env.step(steering, 1.0)

        if env.is_goal_reached():
            break

    assert env.is_goal_reached()
```

## 9. Common Pitfalls and Solutions

### 9.1 Grid Indexing

**Problem**: Confusion between (x, y) and (row, col) indexing.

**Solution**: Use consistent convention:
- Grid access: `grid[y, x]` (row, col)
- Position: `(x, y)` in functions

### 9.2 Angle Wrapping

**Problem**: Angles can exceed ±π.

**Solution**: Normalize angles:
```python
angle = np.arctan2(np.sin(angle), np.cos(angle))
```

### 9.3 Division by Zero

**Problem**: Speed can be zero in Stanley controller.

**Solution**: Add minimum speed threshold:
```python
speed = max(speed, 0.1)
```

### 9.4 Integral Windup

**Problem**: PID integral term grows unbounded.

**Solution**: Use anti-windup:
```python
self.integral = np.clip(self.integral, -limit, limit)
```

## 10. Performance Optimization

### 10.1 Numpy Operations

- Use vectorized operations
- Avoid Python loops for large arrays
- Use numpy broadcasting

### 10.2 Data Structures

- Use heapq for priority queues
- Use sets for O(1) membership testing
- Use deques for history with max length

### 10.3 Caching

- Cache computed curvatures
- Cache nearest point indices
- Pre-compute trigonometric values

## 11. References

1. PythonRobotics: https://github.com/AtsushiSakai/PythonRobotics
2. scipy.interpolate: https://docs.scipy.org/doc/scipy/reference/interpolate.html
3. matplotlib.collections: https://matplotlib.org/stable/api/collections_api.html
