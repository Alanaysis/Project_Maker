# Testing: Q-Learning Test Strategy

## Overview

This document describes the testing strategy for the Q-Learning project, including test structure, coverage goals, and best practices.

## Test Structure

### Test Files

```
tests/
├── __init__.py                 # Test package
├── test_grid_world.py          # GridWorld environment tests
├── test_q_learning.py          # Q-Learning agent tests
├── test_sarsa.py               # Sarsa and Expected Sarsa tests
├── test_double_q_learning.py   # Double Q-Learning tests
└── test_environments.py        # FrozenLake, Maze, SimpleGame tests
```

### Test Categories

1. **Unit Tests**: Test individual methods and functions
2. **Integration Tests**: Test component interactions
3. **Performance Tests**: Test training convergence and efficiency

## Test Coverage Goals

### Minimum Coverage

- **Core algorithms**: 90%+ coverage
- **Environment classes**: 85%+ coverage
- **Visualization functions**: 80%+ coverage

### Key Areas to Test

1. **Q-Learning Update**: Verify correct Q-value updates
2. **Exploration Strategies**: Test epsilon-greedy and Boltzmann
3. **Training Loop**: Verify episode handling and statistics
4. **Policy Extraction**: Test get_policy() and evaluate()
5. **Environment Dynamics**: Test step(), reset(), and state transitions

## Unit Tests

### 1. GridWorld Tests

**File**: `tests/test_grid_world.py`

**Test Cases**:
- Initialization with different parameters
- Reset functionality
- Step actions (valid moves, walls, traps, goals)
- State index conversion
- Rendering

**Example**:
```python
def test_step_valid():
    env = GridWorld(rows=3, cols=3, start=(0, 0), goal=(2, 2))
    next_state, reward, done, info = env.step(1)  # Move right
    assert next_state == (0, 1)
    assert reward == -1.0
    assert not done
```

### 2. Q-Learning Agent Tests

**File**: `tests/test_q_learning.py`

**Test Cases**:
- Initialization
- Action selection (explore/exploit)
- Q-value update
- Epsilon decay
- Training convergence
- Policy extraction
- Evaluation metrics

**Example**:
```python
def test_update():
    agent = QLearningAgent(n_states=9, n_actions=4, alpha=0.5, gamma=0.9)
    agent.q_table[0, 0] = 1.0
    agent.q_table[1] = [0.0, 2.0, 3.0, 0.0]

    td_error = agent.update((0, 0), 0, 1.0, (1, 1), False, env)

    # Q(0,0) = 1.0 + 0.5 * (1.0 + 0.9 * 3.0 - 1.0) = 2.35
    assert abs(agent.q_table[0, 0] - 2.35) < 1e-6
```

### 3. Sarsa Tests

**File**: `tests/test_sarsa.py`

**Test Cases**:
- SarsaAgent initialization
- Sarsa update rule
- ExpectedSarsaAgent initialization
- Expected Sarsa update rule
- Policy probability calculation
- Training convergence

**Example**:
```python
def test_sarsa_update():
    config = SarsaConfig(n_states=9, n_actions=4, alpha=0.5, gamma=0.9)
    agent = SarsaAgent(config)
    agent.q_table[0, 0] = 1.0
    agent.q_table[1, 1] = 2.0

    td_error = agent.update(0, 0, 1.0, 1, 1, False)

    # Q(0,0) = 1.0 + 0.5 * (1.0 + 0.9 * 2.0 - 1.0) = 1.9
    assert abs(agent.q_table[0, 0] - 1.9) < 1e-6
```

### 4. Double Q-Learning Tests

**File**: `tests/test_double_q_learning.py`

**Test Cases**:
- Initialization with two Q-tables
- Q-table average property
- Action selection
- Terminal state updates
- Non-terminal state updates (random selection)
- Training convergence
- Overestimation reduction

**Example**:
```python
def test_update_terminal():
    agent = DoubleQLearningAgent(n_states=9, n_actions=4, alpha=0.5)
    agent.q_table_a[0, 0] = 1.0
    agent.q_table_b[0, 0] = 1.0

    agent.update(0, 0, 10.0, 1, True)

    # Both tables should be updated equally at terminal
    expected = 1.0 + 0.5 * (10.0 - 1.0)
    assert abs(agent.q_table_a[0, 0] - expected) < 1e-6
    assert abs(agent.q_table_b[0, 0] - expected) < 1e-6
```

### 5. Environment Tests

**File**: `tests/test_environments.py`

**Test Cases**:

**FrozenLake**:
- Map initialization (4x4, 8x8)
- Reset functionality
- Valid/invalid movements
- Goal/hole states
- Slippery movement stochasticity
- State index conversion

**Maze**:
- Custom maze initialization
- Random maze generation
- Wall hit penalties
- Goal reaching
- Rendering

**SimpleGame**:
- Initialization
- Correct/incorrect guesses
- Close guess rewards
- Out of attempts
- State discretization

## Integration Tests

### Training Integration

**Test**: Agent trains successfully on environment

```python
def test_q_learning_trains_gridworld():
    env = GridWorld(rows=3, cols=3, start=(0, 0), goal=(2, 2), seed=42)
    agent = QLearningAgent(n_states=9, n_actions=4, alpha=0.5, gamma=0.9, seed=42)

    result = agent.train(env, n_episodes=100, max_steps=50)

    # Should learn something
    assert np.mean(result.episode_rewards[-50:]) > np.mean(result.episode_rewards[:50])
```

### Algorithm Comparison

**Test**: Compare different algorithms on same environment

```python
def test_algorithms_comparison():
    env = GridWorld(rows=5, cols=5, start=(0, 0), goal=(4, 4), seed=42)

    # Q-Learning
    q_agent = QLearningAgent(n_states=25, n_actions=4, seed=42)
    q_result = q_agent.train(env, n_episodes=200, max_steps=100)
    q_metrics = q_agent.evaluate(env, n_episodes=50)

    # Sarsa
    config = SarsaConfig(n_states=25, n_actions=4, seed=42)
    sarsa_agent = SarsaAgent(config)
    sarsa_result = sarsa_agent.train(env, n_episodes=200, max_steps=100)
    sarsa_metrics = sarsa_agent.evaluate(env, n_episodes=50)

    # Both should learn
    assert q_metrics["success_rate"] > 0
    assert sarsa_metrics["success_rate"] > 0
```

## Performance Tests

### Convergence Test

**Test**: Verify algorithms converge on simple environments

```python
def test_convergence():
    env = GridWorld(rows=3, cols=3, start=(0, 0), goal=(2, 2), seed=42)
    agent = QLearningAgent(n_states=9, n_actions=4, seed=42)

    result = agent.train(env, n_episodes=500, max_steps=50)

    # Should converge (success rate > 80% in last 100 episodes)
    metrics = agent.evaluate(env, n_episodes=100)
    assert metrics["success_rate"] > 0.8
```

### Training Time Test

**Test**: Measure training time

```python
import time

def test_training_time():
    env = GridWorld(rows=5, cols=5, start=(0, 0), goal=(4, 4), seed=42)
    agent = QLearningAgent(n_states=25, n_actions=4, seed=42)

    start_time = time.time()
    agent.train(env, n_episodes=1000, max_steps=100)
    elapsed = time.time() - start_time

    # Should complete within reasonable time
    assert elapsed < 10.0  # 10 seconds
```

## Edge Cases

### 1. Immediate Goal

**Test**: Agent starts next to goal

```python
def test_immediate_goal():
    env = GridWorld(rows=3, cols=3, start=(0, 0), goal=(0, 1), seed=42)
    agent = QLearningAgent(n_states=9, n_actions=4, seed=42)

    result = agent.train(env, n_episodes=10, max_steps=10)

    # Should reach goal in 1 step
    assert min(result.episode_steps) == 1
```

### 2. Unreachable Goal

**Test**: Goal is blocked by walls

```python
def test_unreachable_goal():
    env = GridWorld(
        rows=3, cols=3,
        start=(0, 0), goal=(2, 2),
        walls=[(1, 1)],  # Block all paths
        seed=42,
    )
    agent = QLearningAgent(n_states=9, n_actions=4, seed=42)

    result = agent.train(env, n_episodes=100, max_steps=50)

    # Should not reach goal
    metrics = agent.evaluate(env, n_episodes=50)
    assert metrics["success_rate"] == 0.0
```

### 3. Trap States

**Test**: Agent falls into trap

```python
def test_trap_state():
    env = GridWorld(
        rows=3, cols=3,
        start=(0, 0), goal=(2, 2),
        traps=[(1, 1)],
        seed=42,
    )
    agent = QLearningAgent(n_states=9, n_actions=4, seed=42)

    result = agent.train(env, n_episodes=100, max_steps=50)

    # Should learn to avoid traps
    # (rewards should improve over time)
    assert np.mean(result.episode_rewards[-50:]) > np.mean(result.episode_rewards[:50])
```

## Test Best Practices

### 1. Use Fixed Seeds

```python
env = GridWorld(rows=3, cols=3, start=(0, 0), goal=(2, 2), seed=42)
agent = QLearningAgent(n_states=9, n_actions=4, seed=42)
```

### 2. Test Deterministic Behavior

```python
def test_deterministic():
    agent = QLearningAgent(n_states=9, n_actions=4, epsilon=0.0, seed=42)
    agent.q_table[0] = [1.0, 2.0, 3.0, 0.5]

    # Should always choose action 2
    actions = [agent.choose_action(0) for _ in range(100)]
    assert all(a == 2 for a in actions)
```

### 3. Test Edge Cases

```python
def test_epsilon_min():
    agent = QLearningAgent(
        n_states=9, n_actions=4,
        epsilon=1.0, epsilon_decay=0.9, epsilon_min=0.1,
        seed=42,
    )

    for _ in range(100:
        agent.decay_epsilon()

    # Should not go below minimum
    assert agent.epsilon == 0.1
```

### 4. Use Assertions Appropriately

```python
# Exact equality (for integers)
assert agent.n_states == 9

# Approximate equality (for floats)
assert abs(agent.q_table[0, 0] - 2.35) < 1e-6

# Range checks
assert 0 <= metrics["success_rate"] <= 1

# Collection checks
assert len(result.episode_rewards) == 100
```

## Running Tests

### Basic Test Run

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_q_learning.py -v

# Run specific test
pytest tests/test_q_learning.py::TestQLearningAgent::test_update -v
```

### With Coverage

```bash
# Run with coverage report
pytest tests/ --cov=src --cov-report=term-missing

# Generate HTML coverage report
pytest tests/ --cov=src --cov-report=html
```

### Parallel Tests

```bash
# Run tests in parallel
pytest tests/ -n auto
```

## Continuous Integration

### GitHub Actions

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
        run: pip install numpy pytest pytest-cov
      - name: Run tests
        run: pytest tests/ --cov=src --cov-report=xml
```

## Test Maintenance

### Adding New Tests

1. Create test file in `tests/`
2. Import components from `src/`
3. Use pytest fixtures for common setup
4. Follow naming conventions
5. Add to CI pipeline

### Updating Existing Tests

1. Update test when algorithm changes
2. Maintain backward compatibility
3. Document test purpose
4. Keep tests independent

## Conclusion

The testing strategy ensures code quality, correctness, and reliability. By following these guidelines, we can maintain a robust test suite that catches regressions and validates new features.
