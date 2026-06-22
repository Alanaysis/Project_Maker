# ADAS Planning and Control System

A comprehensive autonomous driving planning and control system implemented in Python. This project demonstrates core algorithms used in Advanced Driver Assistance Systems (ADAS) including path planning and trajectory tracking.

## Features

### Path Planning Algorithms
- **A* Search**: Optimal pathfinding with admissible heuristics (Manhattan, Euclidean, Chebyshev)
- **Dijkstra's Algorithm**: Shortest path without heuristic guidance
- **RRT (Rapidly-exploring Random Tree)**: Sampling-based probabilistic planning
- **Theta***: Any-angle path planning for smoother trajectories

### Control Algorithms
- **PID Controller**: Classic Proportional-Integral-Derivative control with anti-windup
- **Stanley Controller**: Lateral control combining heading and cross-track error
- **MPC Controller**: Model Predictive Control for optimal trajectory tracking
- **LQR Controller**: Linear Quadratic Regulator for lateral control

### Vehicle Models
- **Point Mass Model**: Simple kinematic model
- **Bicycle Model**: Standard bicycle dynamics for path tracking
- **Kinematic Model**: Kinematic bicycle model with slip angle
- **Dynamic Bicycle Model**: Full dynamic model with tire forces

### Visualization
- Grid map visualization with obstacles
- Path and trajectory visualization with velocity coloring
- Vehicle animation
- Performance comparison plots

## Installation

### Prerequisites
- Python 3.8+
- pip

### Install Dependencies

```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install numpy matplotlib scipy
```

## Quick Start

### 1. Simple Demo

Run the basic demo to see A* planning and PID tracking:

```bash
python examples/simple_demo.py
```

### 2. Algorithm Comparison

Compare different planning algorithms:

```bash
python examples/algorithm_comparison.py
```

### 3. Controller Comparison

Compare PID and Stanley controllers:

```bash
python examples/controller_comparison.py
```

### 4. Run Tests

```bash
pytest tests/ -v
```

## Project Structure

```
adas-planning/
├── src/                    # Source code
│   ├── __init__.py        # Package initialization
│   ├── planner.py         # Path planning algorithms
│   ├── controller.py      # Control algorithms
│   ├── vehicle.py         # Vehicle models
│   ├── environment.py     # Grid map and simulation environment
│   ├── trajectory.py      # Trajectory generation
│   ├── visualization.py   # Visualization tools
│   └── simulation.py      # Main simulation engine
├── tests/                 # Unit tests
│   ├── test_planner.py
│   ├── test_controller.py
│   ├── test_environment.py
│   ├── test_vehicle.py
│   └── test_trajectory.py
├── examples/              # Example scripts
│   ├── simple_demo.py
│   ├── algorithm_comparison.py
│   └── controller_comparison.py
├── docs/                  # Documentation
│   ├── 01-RESEARCH.md
│   ├── 02-DESIGN.md
│   ├── 03-IMPLEMENTATION.md
│   ├── 04-TESTING.md
│   └── 05-DEVELOPMENT.md
├── README.md
├── requirements.txt
└── LEARNING_NOTES.md
```

## Usage Examples

### Basic Path Planning

```python
from src.environment import GridMap
from src.planner import AStarPlanner

# Create a grid map
grid_map = GridMap(50, 50)
grid_map.add_obstacle(25, 25)
grid_map.add_obstacle(25, 26)

# Plan a path
planner = AStarPlanner(allow_diagonal=True)
path = planner.plan(grid_map, (0, 0), (49, 49))

if path:
    print(f"Path found: {len(path)} points")
```

### Trajectory Tracking

```python
from src.environment import GridMap, SimulationEnvironment
from src.controller import PIDController
from src.trajectory import TrajectoryGenerator

# Create environment
grid_map = GridMap(50, 50)
env = SimulationEnvironment(grid_map, start=(0, 0), goal=(49, 49))

# Create controller
controller = PIDController(Kp=1.0, Ki=0.01, Kd=0.5)

# Run simulation loop
while not env.is_goal_reached():
    # Compute control
    error = compute_tracking_error(env, trajectory)
    steering = controller.compute(error, env.dt)

    # Execute step
    env.step(steering, acceleration=1.0)
```

### Visualization

```python
from src.visualization import Visualizer

visualizer = Visualizer()

# Plot grid map
visualizer.plot_grid_map(grid_map)

# Plot path
visualizer.plot_path(path)

# Show plot
visualizer.show()
```

## Algorithm Details

### A* Path Planning

A* uses a best-first search with a heuristic function:

```
f(n) = g(n) + h(n)
```

Where:
- `g(n)`: Actual cost from start to node n
- `h(n)`: Heuristic estimated cost from n to goal
- `f(n)`: Total estimated cost

The algorithm is optimal when using an admissible heuristic (never overestimates).

### PID Controller

PID control combines three terms:

```
u(t) = Kp * e(t) + Ki * ∫e(t)dt + Kd * de(t)/dt
```

Where:
- `Kp`: Proportional gain (responds to current error)
- `Ki`: Integral gain (eliminates steady-state error)
- `Kd`: Derivative gain (reduces overshoot)

### Stanley Controller

The Stanley controller computes steering angle as:

```
δ = θ_e + arctan(k * e_y / v)
```

Where:
- `θ_e`: Heading error
- `e_y`: Cross-track error
- `k`: Gain parameter
- `v`: Vehicle speed

## Learning Objectives

This project helps you understand:

1. **Motion Planning Algorithms**
   - Graph search (A*, Dijkstra)
   - Sampling-based planning (RRT)
   - Any-angle planning (Theta*)

2. **Control Theory**
   - PID tuning and anti-windup
   - Model Predictive Control
   - Lateral vehicle control

3. **Vehicle Dynamics**
   - Bicycle model
   - Kinematic vs dynamic models
   - Slip angle and tire forces

4. **Software Engineering**
   - Modular design
   - Unit testing
   - Visualization

## References

- [PythonRobotics](https://github.com/AtsushiSakai/PythonRobotics) - Python implementations of robotics algorithms
- [motion-planning](https://github.com/zhm-real/motion-planning) - Motion planning algorithms
- [tuplan_garage](https://github.com/motional/tuplan_garage) - Autonomous driving planning

## License

This project is for educational purposes.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
