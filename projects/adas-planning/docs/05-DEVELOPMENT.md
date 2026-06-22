# Development Guide: ADAS Planning and Control System

## 1. Development Setup

### 1.1 Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git (for version control)

### 1.2 Installation

```bash
# Clone the repository
git clone <repository-url>
cd adas-planning

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### 1.3 IDE Setup

**VS Code**:
- Install Python extension
- Install Python Test Explorer
- Configure pytest as test runner

**PyCharm**:
- Open project directory
- Configure Python interpreter
- Enable pytest integration

## 2. Project Structure

```
adas-planning/
├── src/                    # Source code
│   ├── __init__.py
│   ├── planner.py
│   ├── controller.py
│   ├── vehicle.py
│   ├── environment.py
│   ├── trajectory.py
│   ├── visualization.py
│   └── simulation.py
├── tests/                 # Unit tests
├── examples/              # Example scripts
├── docs/                  # Documentation
├── requirements.txt       # Dependencies
├── README.md             # Project overview
└── LEARNING_NOTES.md     # Learning notes
```

## 3. Development Workflow

### 3.1 Feature Development

1. Create feature branch
2. Implement feature
3. Write tests
4. Update documentation
5. Submit pull request

### 3.2 Code Style

Follow PEP 8 guidelines:
- 4 spaces for indentation
- 79 characters per line
- Blank lines between functions/classes
- Descriptive variable names

### 3.3 Docstrings

Use Google-style docstrings:

```python
def function(param1: int, param2: str) -> bool:
    """Short description.

    Longer description if needed.

    Args:
        param1: Description of param1.
        param2: Description of param2.

    Returns:
        Description of return value.

    Raises:
        ValueError: If param1 is negative.
    """
    pass
```

## 4. Adding New Features

### 4.1 Adding a New Planner

1. Create class inheriting from `PathPlanner`:

```python
from src.planner import PathPlanner

class MyPlanner(PathPlanner):
    def __init__(self, param1: float = 1.0):
        self.param1 = param1
        self.nodes_explored = 0

    def plan(self, grid_map, start, goal):
        # Implementation
        pass
```

2. Add tests:

```python
class TestMyPlanner:
    def test_simple_path(self):
        planner = MyPlanner()
        grid_map = GridMap(10, 10)
        path = planner.plan(grid_map, (0, 0), (9, 9))
        assert path is not None
```

3. Update `__init__.py`:

```python
from .planner import MyPlanner
```

4. Add to simulation configuration:

```python
# In simulation.py
if self.config.planner_type == "myplanner":
    self.planner = MyPlanner()
```

### 4.2 Adding a New Controller

1. Create class inheriting from `Controller`:

```python
from src.controller import Controller

class MyController(Controller):
    def __init__(self, gain: float = 1.0):
        self.gain = gain

    def compute(self, error, dt):
        return self.gain * error

    def reset(self):
        pass
```

2. Add tests:

```python
class TestMyController:
    def test_compute(self):
        controller = MyController(gain=2.0)
        output = controller.compute(1.0, 0.1)
        assert output == 2.0
```

### 4.3 Adding a New Vehicle Model

1. Create class inheriting from `VehicleModel`:

```python
from src.vehicle import VehicleModel

class MyVehicleModel(VehicleModel):
    def __init__(self, params=None):
        self.params = params or VehicleParameters()

    def update(self, state, control, dt):
        # Implementation
        return new_state

    def get_state_dim(self):
        return 4

    def get_control_dim(self):
        return 2
```

2. Register in factory function:

```python
def create_vehicle_model(model_type, params=None):
    models = {
        "mymodel": MyVehicleModel,
        # ... other models
    }
    return models[model_type](params)
```

## 5. Testing

### 5.1 Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_planner.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### 5.2 Writing Tests

```python
import pytest
from src.planner import AStarPlanner
from src.environment import GridMap

class TestAStarPlanner:
    def test_simple_path(self):
        """Test path planning on simple grid."""
        # Arrange
        grid_map = GridMap(10, 10)
        planner = AStarPlanner()

        # Act
        path = planner.plan(grid_map, (0, 0), (9, 9))

        # Assert
        assert path is not None
        assert path[0] == (0, 0)
        assert path[-1] == (9, 9)

    @pytest.fixture
    def grid_with_obstacles(self):
        grid_map = GridMap(10, 10)
        grid_map.add_obstacle(5, 5)
        return grid_map

    def test_avoids_obstacles(self, grid_with_obstacles):
        """Test that path avoids obstacles."""
        planner = AStarPlanner()
        path = planner.plan(grid_with_obstacles, (0, 0), (9, 9))

        for x, y in path:
            assert not grid_with_obstacles.is_obstacle(x, y)
```

## 6. Debugging

### 6.1 Common Issues

**Import Errors**:
```bash
# Ensure you're in the project directory
cd adas-planning

# Install in development mode
pip install -e .
```

**NumPy Version Issues**:
```bash
# Update NumPy
pip install --upgrade numpy
```

**Matplotlib Display Issues**:
```python
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
```

### 6.2 Debugging Tools

**Print Debugging**:
```python
print(f"Debug: state={state}, control={control}")
```

**Logging**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug(f"State: {state}")
```

**Debugger**:
```python
import pdb; pdb.set_trace()  # Breakpoint
```

## 7. Performance Optimization

### 7.1 Profiling

```python
import cProfile

def profile_function():
    cProfile.run('my_function()')
```

### 7.2 Optimization Tips

1. **Use NumPy**: Vectorize operations
2. **Avoid Loops**: Use broadcasting
3. **Cache Results**: Store expensive computations
4. **Use Appropriate Data Structures**: Sets for membership, heaps for priorities

### 7.3 Memory Management

```python
import gc

# Force garbage collection
gc.collect()

# Monitor memory
import tracemalloc
tracemalloc.start()
# ... code ...
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
```

## 8. Documentation

### 8.1 Code Documentation

- Add docstrings to all public functions
- Include type hints
- Provide usage examples

### 8.2 README Updates

- Update features list
- Add usage examples
- Document new algorithms

### 8.3 API Documentation

Generate API documentation:

```bash
# Using pdoc
pip install pdoc
pdoc src --html

# Using sphinx
pip install sphinx
sphinx-quickstart
```

## 9. Version Control

### 9.1 Branch Strategy

- `main`: Stable release
- `develop`: Development branch
- `feature/*`: Feature branches
- `bugfix/*`: Bug fix branches

### 9.2 Commit Messages

Follow conventional commits:

```
feat: Add new planner algorithm
fix: Fix collision detection bug
docs: Update README
test: Add unit tests for controller
refactor: Improve code structure
```

### 9.3 Pull Requests

1. Create feature branch
2. Make changes
3. Write tests
4. Update documentation
5. Submit PR
6. Address review comments
7. Merge after approval

## 10. Deployment

### 10.1 Package Distribution

```bash
# Create setup.py
# Build package
python setup.py sdist bdist_wheel

# Upload to PyPI
pip install twine
twine upload dist/*
```

### 10.2 Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "examples/simple_demo.py"]
```

## 11. Contributing

### 11.1 Contribution Guidelines

1. Fork the repository
2. Create feature branch
3. Make changes
4. Add tests
5. Update documentation
6. Submit pull request

### 11.2 Code Review Checklist

- [ ] Code follows style guidelines
- [ ] Tests pass
- [ ] Documentation updated
- [ ] No security issues
- [ ] Performance acceptable

## 12. Resources

### 12.1 Python Resources

- [Python Documentation](https://docs.python.org/3/)
- [PEP 8](https://peps.python.org/pep-0008/)
- [NumPy Documentation](https://numpy.org/doc/)
- [Matplotlib Documentation](https://matplotlib.org/)

### 12.2 Autonomous Driving Resources

- [PythonRobotics](https://github.com/AtsushiSakai/PythonRobotics)
- [motion-planning](https://github.com/zhm-real/motion-planning)
- [Apollo](https://github.com/ApolloAuto/apollo)

### 12.3 Testing Resources

- [pytest Documentation](https://docs.pytest.org/)
- [unittest Documentation](https://docs.python.org/3/library/unittest.html)

## 13. Troubleshooting

### 13.1 Common Problems

**Problem**: Import errors
**Solution**: Ensure package is installed in development mode

**Problem**: Tests fail
**Solution**: Check dependencies and Python version

**Problem**: Visualization doesn't show
**Solution**: Use `plt.show()` or save to file

### 13.2 Getting Help

1. Check documentation
2. Search issues
3. Ask in discussions
4. Create new issue

## 14. Future Plans

### 14.1 Short Term

- Add more planners (PRM, PRM*)
- Add more controllers
- Improve visualization

### 14.2 Medium Term

- Add 3D support
- Add ROS2 integration
- Add sensor simulation

### 14.3 Long Term

- Machine learning integration
- Real-world testing
- Production deployment

## 15. References

1. Python Best Practices: https://realpython.com/
2. NumPy Tutorial: https://numpy.org/doc/stable/user/quickstart.html
3. Matplotlib Tutorial: https://matplotlib.org/stable/tutorials/
4. pytest Tutorial: https://docs.pytest.org/en/stable/getting-started.html
