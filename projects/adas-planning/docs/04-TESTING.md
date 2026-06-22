# Testing Guide: ADAS Planning and Control System

## 1. Testing Overview

This document provides comprehensive testing guidance for the ADAS Planning and Control System. The testing strategy includes unit tests, integration tests, and visual tests.

## 2. Test Structure

```
tests/
├── __init__.py
├── test_planner.py        # Path planning tests
├── test_controller.py     # Control algorithm tests
├── test_environment.py    # Environment tests
├── test_vehicle.py        # Vehicle model tests
└── test_trajectory.py     # Trajectory tests
```

## 3. Running Tests

### 3.1 Run All Tests

```bash
pytest tests/ -v
```

### 3.2 Run Specific Test File

```bash
pytest tests/test_planner.py -v
```

### 3.3 Run Specific Test Class

```bash
pytest tests/test_planner.py::TestAStarPlanner -v
```

### 3.4 Run Specific Test

```bash
pytest tests/test_planner.py::TestAStarPlanner::test_simple_path -v
```

### 3.5 Run with Coverage

```bash
pytest tests/ --cov=src --cov-report=html
```

## 4. Test Categories

### 4.1 Unit Tests

Test individual components in isolation.

**Planner Tests**:
- Test path existence
- Test path validity
- Test optimality
- Test edge cases

**Controller Tests**:
- Test output computation
- Test limits and constraints
- Test convergence
- Test reset functionality

**Environment Tests**:
- Test grid operations
- Test collision detection
- Test goal detection
- Test state management

**Vehicle Model Tests**:
- Test dynamics
- Test constraints
- Test trajectory prediction

**Trajectory Tests**:
- Test generation
- Test smoothness
- Test velocity profiling

### 4.2 Integration Tests

Test component interactions.

**End-to-End Tests**:
- Complete planning and tracking
- Multiple planner/controller combinations
- Various map configurations

### 4.3 Visual Tests

Verify outputs visually.

**Visualization Tests**:
- Plot paths and trajectories
- Verify correctness by inspection
- Compare algorithms visually

## 5. Test Cases

### 5.1 Planner Tests

#### A* Planner Tests

```python
class TestAStarPlanner:
    def test_simple_path(self):
        """Test path planning on a simple grid."""
        # Arrange
        grid_map = GridMap(10, 10)
        planner = AStarPlanner(allow_diagonal=False)

        # Act
        path = planner.plan(grid_map, (0, 0), (9, 9))

        # Assert
        assert path is not None
        assert path[0] == (0, 0)
        assert path[-1] == (9, 9)
        assert len(path) > 0

    def test_path_around_obstacle(self):
        """Test that path avoids obstacles."""
        # Arrange
        grid_map = GridMap(10, 10)
        for y in range(10):
            if y != 5:
                grid_map.add_obstacle(5, y)

        planner = AStarPlanner(allow_diagonal=False)

        # Act
        path = planner.plan(grid_map, (0, 0), (9, 9))

        # Assert
        assert path is not None
        for x, y in path:
            assert not grid_map.is_obstacle(x, y)

    def test_no_path(self):
        """Test when no path exists."""
        # Arrange
        grid_map = GridMap(10, 10)
        for y in range(10):
            grid_map.add_obstacle(5, y)

        planner = AStarPlanner(allow_diagonal=False)

        # Act
        path = planner.plan(grid_map, (0, 0), (9, 9))

        # Assert
        assert path is None
```

#### Dijkstra Tests

```python
class TestDijkstraPlanner:
    def test_optimal_path(self):
        """Test that Dijkstra finds optimal path."""
        grid_map = GridMap(10, 10)
        planner = DijkstraPlanner(allow_diagonal=False)

        path = planner.plan(grid_map, (0, 0), (9, 9))

        # Manhattan distance for optimal path
        expected_length = 18  # 9 + 9
        path_length = len(path) - 1

        assert path_length == expected_length
```

### 5.2 Controller Tests

#### PID Controller Tests

```python
class TestPIDController:
    def test_proportional_only(self):
        """Test P-only controller."""
        controller = PIDController(Kp=1.0, Ki=0.0, Kd=0.0)

        # Positive error should give positive output
        output = controller.compute(1.0, 0.1)
        assert output > 0

    def test_output_limits(self):
        """Test output limiting."""
        controller = PIDController(
            Kp=100.0, Ki=0.0, Kd=0.0,
            output_limits=(-1.0, 1.0)
        )

        output = controller.compute(100.0, 0.1)
        assert output == pytest.approx(1.0)

    def test_convergence(self):
        """Test that PID can converge to zero error."""
        controller = PIDController(Kp=2.0, Ki=0.5, Kd=0.1)

        error = 10.0
        dt = 0.1

        for _ in range(100):
            output = controller.compute(error, dt)
            error -= output * dt

        assert abs(error) < 1.0
```

#### Stanley Controller Tests

```python
class TestStanleyController:
    def test_cross_track_error_correction(self):
        """Test that controller corrects cross-track error."""
        controller = StanleyController(k=2.0)

        current_pos = np.array([1.0, 1.0])
        current_heading = 0.0
        path = [np.array([0.0, 0.0]), np.array([1.0, 0.0]), np.array([2.0, 0.0])]
        speed = 5.0

        steering = controller.compute_steering(current_pos, current_heading, path, speed)

        # Should steer left to correct
        assert steering < 0
```

### 5.3 Environment Tests

```python
class TestGridMap:
    def test_bounds_checking(self):
        """Test bounds checking."""
        grid_map = GridMap(10, 10)

        assert grid_map.in_bounds(0, 0)
        assert grid_map.in_bounds(9, 9)
        assert not grid_map.in_bounds(-1, 0)
        assert not grid_map.in_bounds(10, 0)

    def test_get_neighbors(self):
        """Test neighbor retrieval."""
        grid_map = GridMap(10, 10)

        neighbors = grid_map.get_neighbors(5, 5, allow_diagonal=True)
        assert len(neighbors) == 8

        neighbors = grid_map.get_neighbors(5, 5, allow_diagonal=False)
        assert len(neighbors) == 4

class TestSimulationEnvironment:
    def test_step(self):
        """Test simulation step."""
        grid_map = GridMap(10, 10)
        env = SimulationEnvironment(grid_map, start=(0, 0), goal=(9, 9), dt=0.1)

        pos, heading, speed = env.step(0.0, 1.0)

        assert speed > 0.0
        assert pos[0] > 0.0 or pos[1] > 0.0
```

### 5.4 Vehicle Model Tests

```python
class TestBicycleModel:
    def test_straight_line(self):
        """Test straight line motion."""
        model = BicycleModel()
        state = np.array([0.0, 0.0, 0.0, 5.0])
        control = np.array([0.0, 0.0])

        new_state = model.update(state, control, 0.1)

        assert new_state[0] > 0.0
        assert abs(new_state[1]) < 0.01

    def test_turning(self):
        """Test turning behavior."""
        model = BicycleModel()
        state = np.array([0.0, 0.0, 0.0, 5.0])
        control = np.array([0.0, 0.5])

        new_state = model.update(state, control, 0.1)

        assert new_state[2] > 0.0
```

### 5.5 Trajectory Tests

```python
class TestTrajectory:
    def test_from_waypoints(self):
        """Test creation from waypoints."""
        waypoints = [(0, 0), (1, 0), (2, 0)]

        trajectory = Trajectory.from_waypoints(waypoints)

        assert len(trajectory) == 3
        assert trajectory[0].x == 0.0

    def test_get_length(self):
        """Test trajectory length calculation."""
        trajectory = Trajectory.from_waypoints([(0, 0), (3, 0), (3, 4)])

        length = trajectory.get_length()

        assert length == pytest.approx(7.0)

class TestTrajectoryGenerator:
    def test_generate_smooth(self):
        """Test that generated trajectory is smooth."""
        generator = TrajectoryGenerator(ds=0.5)
        waypoints = [(0, 0), (5, 5), (10, 0)]

        trajectory = generator.generate(waypoints, target_velocity=5.0)

        headings = trajectory.get_headings()
        heading_diffs = np.abs(np.diff(headings))
        assert np.max(heading_diffs) < np.pi / 2
```

## 6. Test Data

### 6.1 Test Grid Maps

**Empty Grid**:
```python
grid_map = GridMap(10, 10)
```

**Grid with Wall**:
```python
grid_map = GridMap(10, 10)
for y in range(10):
    grid_map.add_obstacle(5, y)
grid_map.remove_obstacle(5, 5)  # Gap
```

**Random Grid**:
```python
grid_map = GridMap.random(20, 20, obstacle_density=0.3, seed=42)
```

### 6.2 Test Trajectories

**Straight Line**:
```python
trajectory = Trajectory.from_waypoints([(0, 0), (10, 0)])
```

**Curved Path**:
```python
trajectory = Trajectory.from_waypoints([(0, 0), (5, 5), (10, 0)])
```

## 7. Mocking and Fixtures

### 7.1 Pytest Fixtures

```python
@pytest.fixture
def empty_grid():
    return GridMap(10, 10)

@pytest.fixture
def grid_with_obstacles():
    grid_map = GridMap(10, 10)
    grid_map.add_obstacle(5, 5)
    return grid_map

@pytest.fixture
def astar_planner():
    return AStarPlanner(allow_diagonal=True)

@pytest.fixture
def pid_controller():
    return PIDController(Kp=1.0, Ki=0.01, Kd=0.5)
```

### 7.2 Using Fixtures

```python
def test_with_fixtures(empty_grid, astar_planner):
    path = astar_planner.plan(empty_grid, (0, 0), (9, 9))
    assert path is not None
```

## 8. Performance Testing

### 8.1 Timing Tests

```python
import time

def test_planner_performance():
    grid_map = GridMap.random(50, 50, obstacle_density=0.3, seed=42)
    planner = AStarPlanner()

    start_time = time.time()
    for _ in range(100):
        planner.plan(grid_map, (0, 0), (49, 49))
    elapsed = time.time() - start_time

    assert elapsed < 10.0  # Should complete in 10 seconds
```

### 8.2 Memory Tests

```python
import tracemalloc

def test_memory_usage():
    tracemalloc.start()

    # Run operations
    grid_map = GridMap(100, 100)
    planner = AStarPlanner()
    planner.plan(grid_map, (0, 0), (99, 99))

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    assert peak < 100 * 1024 * 1024  # Less than 100MB
```

## 9. Edge Cases

### 9.1 Empty Grid

```python
def test_empty_grid():
    grid_map = GridMap(1, 1)
    planner = AStarPlanner()
    path = planner.plan(grid_map, (0, 0), (0, 0))
    assert path is not None
```

### 9.2 Start Equals Goal

```python
def test_start_equals_goal():
    grid_map = GridMap(10, 10)
    planner = AStarPlanner()
    path = planner.plan(grid_map, (5, 5), (5, 5))
    assert path is not None
    assert len(path) == 1
```

### 9.3 Invalid Positions

```python
def test_invalid_start():
    grid_map = GridMap(10, 10)
    grid_map.add_obstacle(0, 0)
    planner = AStarPlanner()
    path = planner.plan(grid_map, (0, 0), (9, 9))
    assert path is None
```

### 9.4 Large Errors

```python
def test_large_error():
    controller = PIDController(
        Kp=1.0, Ki=0.0, Kd=0.0,
        output_limits=(-1.0, 1.0)
    )
    output = controller.compute(1000.0, 0.1)
    assert -1.0 <= output <= 1.0
```

## 10. Continuous Integration

### 10.1 GitHub Actions

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          pytest tests/ -v --cov=src
```

## 11. Test Reports

### 11.1 Coverage Report

```bash
pytest tests/ --cov=src --cov-report=html
```

This generates an HTML coverage report in `htmlcov/`.

### 11.2 JUnit XML Report

```bash
pytest tests/ --junitxml=results.xml
```

## 12. Best Practices

1. **Test Early, Test Often**: Write tests before or alongside code
2. **Isolate Tests**: Each test should be independent
3. **Use Descriptive Names**: Test names should describe what they test
4. **Test Edge Cases**: Don't just test the happy path
5. **Keep Tests Fast**: Tests should run quickly
6. **Use Fixtures**: Avoid code duplication
7. **Test One Thing**: Each test should verify one behavior
8. **Clean Up**: Tests should not leave artifacts

## 13. References

1. pytest documentation: https://docs.pytest.org/
2. pytest-cov: https://pytest-cov.readthedocs.io/
3. unittest.mock: https://docs.python.org/3/library/unittest.mock.html
