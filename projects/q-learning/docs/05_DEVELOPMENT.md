# Development: Q-Learning Workflow

## Overview

This document describes the development workflow for the Q-Learning project, including setup, coding standards, and contribution guidelines.

## Development Setup

### Prerequisites

- Python 3.8+
- NumPy
- pytest

### Installation

```bash
# Clone repository
cd projects/q-learning

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install numpy pytest pytest-cov

# Verify installation
pytest tests/ -v
```

### IDE Setup

**VS Code**:
1. Install Python extension
2. Select Python interpreter from venv
3. Enable pytest discovery
4. Configure linting (optional)

**PyCharm**:
1. Open project
2. Configure Python interpreter
3. Enable pytest as test runner
4. Configure code style

## Project Structure

```
q-learning/
├── src/                    # Source code
│   ├── __init__.py        # Package exports
│   ├── grid_world.py      # Base environment
│   ├── q_learning.py      # Q-Learning algorithm
│   ├── sarsa.py           # Sarsa algorithms
│   ├── double_q_learning.py  # Double Q-Learning
│   ├── environments.py    # Additional environments
│   └── visualization.py   # Visualization tools
├── tests/                 # Test suite
├── docs/                  # Documentation
├── README.md             # Project overview
├── LEARNING_NOTES.md     # Learning insights
└── requirements.txt      # Dependencies
```

## Coding Standards

### Python Style

- Follow PEP 8
- Use type hints
- Write docstrings for all public functions
- Keep functions focused and small

### Naming Conventions

- **Classes**: PascalCase (e.g., `QLearningAgent`)
- **Functions**: snake_case (e.g., `choose_action`)
- **Variables**: snake_case (e.g., `state_idx`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `REWARD_GOAL`)

### Docstrings

Use Google-style docstrings:

```python
def update(self, state: tuple[int, int], action: int, reward: float) -> float:
    """Update Q-value using the Q-Learning update rule.

    Args:
        state: Current state as (row, col).
        action: Action taken.
        reward: Reward received.

    Returns:
        The TD error (temporal difference error).

    Raises:
        ValueError: If state is invalid.
    """
```

### Type Hints

```python
from typing import Optional
import numpy as np

def train(
    self,
    env: GridWorld,
    n_episodes: int = 1000,
    max_steps: int = 200,
    seed: Optional[int] = None,
) -> TrainingResult:
    """Train the agent."""
    pass
```

## Development Workflow

### 1. Feature Development

```bash
# Create feature branch
git checkout -b feature/new-algorithm

# Implement changes
# ...

# Run tests
pytest tests/ -v

# Check coverage
pytest tests/ --cov=src --cov-report=term-missing

# Commit changes
git add .
git commit -m "feat: add new algorithm"

# Push to remote
git push origin feature/new-algorithm
```

### 2. Bug Fixes

```bash
# Create bugfix branch
git checkout -b bugfix/fix-update

# Fix the bug
# ...

# Add regression test
# ...

# Run tests
pytest tests/ -v

# Commit changes
git add .
git commit -m "fix: correct Q-value update"
```

### 3. Documentation Updates

```bash
# Create docs branch
git checkout -b docs/update-readme

# Update documentation
# ...

# Commit changes
git add .
git commit -m "docs: update README with new features"
```

## Testing Workflow

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_q_learning.py -v

# Run specific test class
pytest tests/test_q_learning.py::TestQLearningAgent -v

# Run specific test method
pytest tests/test_q_learning.py::TestQLearningAgent::test_update -v
```

### Test Coverage

```bash
# Generate coverage report
pytest tests/ --cov=src --cov-report=term-missing

# Generate HTML report
pytest tests/ --cov=src --cov-report=html

# View HTML report
open htmlcov/index.html
```

### Test-Driven Development (TDD)

1. **Write failing test**
2. **Implement minimum code to pass**
3. **Refactor**
4. **Repeat**

Example:
```python
# 1. Write failing test
def test_new_feature():
    agent = NewAgent(n_states=9, n_actions=4)
    result = agent.new_method()
    assert result == expected_value

# 2. Implement
class NewAgent:
    def new_method(self):
        return expected_value

# 3. Refactor
# ...
```

## Adding New Features

### 1. New Algorithm

**Steps**:
1. Create new file in `src/`
2. Implement algorithm class
3. Add to `__init__.py` exports
4. Create tests in `tests/`
5. Update documentation

**Example** (Adding Q-Learning with eligibility traces):

```python
# src/eligibility_traces.py
class QLearningWithTracesAgent:
    def __init__(self, ...):
        # Initialize
        pass

    def update(self, ...):
        # Update with eligibility traces
        pass

# src/__init__.py
from .eligibility_traces import QLearningWithTracesAgent

# tests/test_eligibility_traces.py
class TestQLearningWithTraces:
    def test_update(self):
        # Test update
        pass
```

### 2. New Environment

**Steps**:
1. Add class to `src/environments.py`
2. Implement environment interface
3. Create tests in `tests/test_environments.py`
4. Update documentation

**Example** (Adding Taxi environment):

```python
# src/environments.py
class Taxi:
    def __init__(self, ...):
        # Initialize
        pass

    def reset(self):
        # Reset environment
        pass

    def step(self, action):
        # Take action
        pass

# tests/test_environments.py
class TestTaxi:
    def test_reset(self):
        # Test reset
        pass
```

### 3. New Visualization

**Steps**:
1. Add function to `src/visualization.py`
2. Add to `__init__.py` exports
3. Create tests
4. Update documentation

**Example** (Adding 3D visualization):

```python
# src/visualization.py
def visualize_3d_q_values(q_table, ...):
    """Create 3D visualization of Q-values."""
    pass

# src/__init__.py
from .visualization import visualize_3d_q_values

# tests/test_visualization.py
def test_visualize_3d_q_values():
    # Test visualization
    pass
```

## Code Review Checklist

### Before Submitting

- [ ] All tests pass
- [ ] Coverage meets minimum (85%+)
- [ ] Code follows style guidelines
- [ ] Docstrings are complete
- [ ] Type hints are used
- [ ] No hardcoded values
- [ ] Error handling is appropriate

### Review Criteria

1. **Correctness**: Does the code work correctly?
2. **Performance**: Is the code efficient?
3. **Readability**: Is the code easy to understand?
4. **Maintainability**: Is the code easy to modify?
5. **Testability**: Is the code easy to test?

## Debugging

### Common Issues

1. **Q-values not converging**:
   - Check learning rate (too high/low)
   - Check exploration rate (too high/low)
   - Check environment rewards

2. **Agent not learning**:
   - Check state representation
   - Check reward structure
   - Check exploration strategy

3. **Tests failing**:
   - Check random seeds
   - Check floating point precision
   - Check edge cases

### Debugging Tools

```python
# Print Q-table
print(agent.q_table)

# Print state indices
print(env.get_state_index(0, 0))

# Print policy
policy = agent.get_policy(env)
print(policy)

# Visualize training
from src.visualization import visualize_training
print(visualize_training(result.episode_rewards, result.episode_steps))
```

## Performance Optimization

### Profiling

```bash
# Profile training
python -m cProfile -o profile.stats src/main.py

# Analyze profile
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative').print_stats(20)"
```

### Optimization Tips

1. **Use NumPy operations** instead of loops
2. **Batch updates** when possible
3. **Cache computed values** (state indices, etc.)
4. **Use appropriate data structures** (arrays vs lists)

## Documentation

### Updating Documentation

1. **README.md**: Project overview, quick start
2. **docs/*.md**: Detailed documentation
3. **LEARNING_NOTES.md**: Learning insights
4. **Docstrings**: Code documentation

### Documentation Standards

- Use Markdown
- Include code examples
- Keep it up to date
- Be clear and concise

## Release Process

### Version Numbering

Follow Semantic Versioning:
- **Major**: Breaking changes
- **Minor**: New features
- **Patch**: Bug fixes

### Release Checklist

1. [ ] All tests pass
2. [ ] Documentation updated
3. [ ] Version number updated
4. [ ] Changelog updated
5. [ ] Tag release

## Contributing

### Getting Started

1. Fork repository
2. Create feature branch
3. Implement changes
4. Add tests
5. Update documentation
6. Submit pull request

### Pull Request Process

1. Create PR with clear description
2. Link related issues
3. Request review
4. Address feedback
5. Merge when approved

### Code of Conduct

- Be respectful
- Be constructive
- Be collaborative
- Be patient

## Resources

### Learning Resources

1. **Sutton & Barto**: Reinforcement Learning: An Introduction
2. **OpenAI Gym**: RL environments
3. **Stable Baselines3**: RL algorithms

### Tools

1. **pytest**: Testing framework
2. **NumPy**: Numerical computing
3. **Matplotlib**: Visualization (optional)
4. **Black**: Code formatting
5. **Flake8**: Linting

## Conclusion

Following these development guidelines ensures code quality, maintainability, and collaboration. The workflow supports iterative development while maintaining high standards.
