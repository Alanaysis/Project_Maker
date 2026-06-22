# Design Document: ADAS Planning and Control System

## 1. System Overview

The ADAS Planning and Control System is designed as a modular, extensible framework for autonomous driving planning and control. The system follows a pipeline architecture where each component can be independently tested and replaced.

## 2. Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Simulation Engine                         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Environment │→│   Planner   │→│  Trajectory  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│         ↓                                              ↓    │
│  ┌─────────────┐                              ┌─────────────┐
│  │   Vehicle   │←─────────────────────────────│  Controller │
│  └─────────────┘                              └─────────────┘
│         ↓                                              ↓    │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                    Visualization                         ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Module Structure

```
src/
├── __init__.py          # Package initialization
├── environment.py       # Grid map and simulation environment
├── planner.py           # Path planning algorithms
├── controller.py        # Control algorithms
├── vehicle.py           # Vehicle dynamics models
├── trajectory.py        # Trajectory generation
├── visualization.py     # Visualization tools
└── simulation.py        # Main simulation engine
```

## 3. Module Design

### 3.1 Environment Module (`environment.py`)

**Purpose**: Represents the world as a grid map and provides simulation environment.

**Classes**:
- `GridMap`: 2D grid representation with obstacles
- `SimulationEnvironment`: Complete simulation environment

**Key Responsibilities**:
- Store grid map with obstacles
- Provide collision checking
- Manage vehicle state
- Execute simulation steps

**Design Decisions**:
- Grid-based representation for simplicity
- Numpy arrays for efficient computation
- Resolution parameter for scaling

### 3.2 Planner Module (`planner.py`)

**Purpose**: Implement path planning algorithms.

**Classes**:
- `PathPlanner`: Abstract base class
- `AStarPlanner`: A* search algorithm
- `DijkstraPlanner`: Dijkstra's algorithm
- `RRTPlanner`: Rapidly-exploring Random Tree
- `ThetaStarPlanner`: Any-angle planning

**Key Responsibilities**:
- Find paths from start to goal
- Handle obstacles and constraints
- Provide optimality guarantees

**Design Decisions**:
- Abstract base class for extensibility
- Configurable heuristics
- Support for diagonal movement

### 3.3 Controller Module (`controller.py`)

**Purpose**: Implement control algorithms for trajectory tracking.

**Classes**:
- `Controller`: Abstract base class
- `PIDController`: PID control
- `MPCController`: Model Predictive Control
- `StanleyController`: Stanley lateral control
- `LQRController`: Linear Quadratic Regulator

**Key Responsibilities**:
- Compute control inputs
- Handle constraints
- Provide stability guarantees

**Design Decisions**:
- Abstract base class for extensibility
- Configurable parameters
- Anti-windup protection

### 3.4 Vehicle Module (`vehicle.py`)

**Purpose**: Provide vehicle dynamics models.

**Classes**:
- `VehicleModel`: Abstract base class
- `PointMassModel`: Simple kinematic model
- `BicycleModel`: Standard bicycle dynamics
- `KinematicModel`: Kinematic bicycle model
- `DynamicBicycleModel`: Full dynamic model

**Key Responsibilities**:
- Simulate vehicle dynamics
- Predict future states
- Handle constraints

**Design Decisions**:
- Multiple model fidelity levels
- Factory pattern for creation
- Configurable parameters

### 3.5 Trajectory Module (`trajectory.py`)

**Purpose**: Generate and manage trajectories.

**Classes**:
- `TrajectoryPoint`: Single trajectory point
- `Trajectory`: Ordered sequence of points
- `TrajectoryGenerator`: Smooth trajectory generation

**Key Responsibilities**:
- Generate smooth trajectories
- Compute curvatures
- Provide velocity profiles

**Design Decisions**:
- Cubic spline interpolation
- Velocity profiling with curvature limits
- Efficient nearest-point queries

### 3.6 Visualization Module (`visualization.py`)

**Purpose**: Provide visualization tools.

**Classes**:
- `Visualizer`: Main visualization class

**Key Responsibilities**:
- Visualize grid maps
- Plot paths and trajectories
- Create animations
- Generate comparison plots

**Design Decisions**:
- Matplotlib for portability
- Modular plotting functions
- Animation support

### 3.7 Simulation Module (`simulation.py`)

**Purpose**: Orchestrate the complete simulation.

**Classes**:
- `SimulationConfig`: Configuration parameters
- `SimulationResult`: Simulation results
- `Simulation`: Main simulation engine

**Key Responsibilities**:
- Initialize components
- Run simulation loop
- Collect results
- Generate visualizations

**Design Decisions**:
- Configuration-based setup
- Result collection for analysis
- Comparison capabilities

## 4. Data Flow

### 4.1 Planning Phase

```
GridMap → Planner → Path (list of grid cells)
```

### 4.2 Trajectory Generation

```
Path → TrajectoryGenerator → Trajectory (smooth curve with velocities)
```

### 4.3 Control Phase

```
Current State + Reference Trajectory → Controller → Control Inputs
```

### 4.4 Simulation Step

```
Control Inputs → Vehicle Model → New State
New State → Environment → Updated State
```

## 5. Interface Design

### 5.1 Planner Interface

```python
class PathPlanner(ABC):
    @abstractmethod
    def plan(self, grid_map: GridMap, start: Tuple[int, int],
             goal: Tuple[int, int]) -> Optional[List[Tuple[int, int]]]:
        pass
```

### 5.2 Controller Interface

```python
class Controller(ABC):
    @abstractmethod
    def compute(self, error: float, dt: float) -> float:
        pass

    @abstractmethod
    def reset(self) -> None:
        pass
```

### 5.3 Vehicle Model Interface

```python
class VehicleModel(ABC):
    @abstractmethod
    def update(self, state: np.ndarray, control: np.ndarray, dt: float) -> np.ndarray:
        pass

    @abstractmethod
    def get_state_dim(self) -> int:
        pass

    @abstractmethod
    def get_control_dim(self) -> int:
        pass
```

## 6. Error Handling

### 6.1 No Path Found

- Planner returns `None`
- Simulation terminates gracefully
- User is notified

### 6.2 Collision Detection

- Environment checks collision each step
- Simulation terminates on collision
- Results are saved up to collision point

### 6.3 Controller Limits

- Output saturation with clipping
- Anti-windup for integral terms
- Rate limiting for smooth control

## 7. Extensibility

### 7.1 Adding New Planners

1. Create new class inheriting from `PathPlanner`
2. Implement `plan()` method
3. Register in simulation configuration

### 7.2 Adding New Controllers

1. Create new class inheriting from `Controller`
2. Implement `compute()` and `reset()` methods
3. Register in simulation configuration

### 7.3 Adding New Vehicle Models

1. Create new class inheriting from `VehicleModel`
2. Implement `update()`, `get_state_dim()`, `get_control_dim()` methods
3. Register in factory function

## 8. Performance Considerations

### 8.1 Grid Operations

- Numpy arrays for efficient storage
- Vectorized operations where possible
- Lazy evaluation for expensive computations

### 8.2 Planning Algorithms

- Priority queues for A* and Dijkstra
- Spatial indexing for RRT
- Caching of computed values

### 8.3 Control Algorithms

- Efficient matrix operations for MPC
- Pre-computed gains for LQR
- History limits for PID

## 9. Testing Strategy

### 9.1 Unit Tests

- Test each module independently
- Test edge cases and error conditions
- Verify algorithm correctness

### 9.2 Integration Tests

- Test module interactions
- End-to-end simulation tests
- Performance benchmarks

### 9.3 Visual Tests

- Plot outputs for verification
- Compare with reference implementations
- Animate simulations

## 10. Future Extensions

### 10.1 Advanced Planning

- Dynamic obstacles
- Multi-vehicle coordination
- Real-time replanning

### 10.2 Advanced Control

- Adaptive control
- Learning-based control
- Robust control

### 10.3 Real-world Integration

- ROS2 integration
- Sensor simulation
- Hardware-in-the-loop testing

## 11. References

1. PythonRobotics: https://github.com/AtsushiSakai/PythonRobotics
2. motion-planning: https://github.com/zhm-real/motion-planning
3. tuplan_garage: https://github.com/motional/tuplan_garage
