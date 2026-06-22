# 04 - Testing Guide

## Testing Strategy

The project uses pytest for testing with the following structure:

```
src/tests/
├── __init__.py
├── test_mock_env.py    # Mock environment tests
├── test_utils.py       # Utility function tests
└── test_agent.py       # Agent tests
```

## Running Tests

### Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Install package in development mode
pip install -e .
```

### Run All Tests

```bash
# Run all tests
pytest src/tests/

# Run with verbose output
pytest src/tests/ -v

# Run with coverage
pytest src/tests/ --cov=carla_rl --cov-report=html
```

### Run Specific Tests

```bash
# Run mock environment tests
pytest src/tests/test_mock_env.py -v

# Run utility tests
pytest src/tests/test_utils.py -v

# Run agent tests
pytest src/tests/test_agent.py -v

# Run specific test class
pytest src/tests/test_mock_env.py::TestMockCarlaRLEnv -v

# Run specific test
pytest src/tests/test_mock_env.py::TestMockCarlaRLEnv::test_reset -v
```

## Test Categories

### 1. Unit Tests

**Mock Environment Tests (`test_mock_env.py`):**

| Test | Description |
|------|-------------|
| `test_init` | Environment initialization |
| `test_observation_space` | Observation space definition |
| `test_action_space` | Action space definition |
| `test_reset` | Environment reset |
| `test_step` | Single step execution |
| `test_multiple_steps` | Multiple steps |
| `test_collision_termination` | Collision detection |
| `test_reward_calculation` | Reward computation |
| `test_camera_observation` | Camera observations |
| `test_random_seed` | Seed reproducibility |
| `test_action_space_sample` | Action sampling |
| `test_vehicle_state` | Vehicle state extraction |
| `test_render` | Render function |
| `test_close` | Environment cleanup |

**Utility Tests (`test_utils.py`):**

| Test | Description |
|------|-------------|
| `test_process_features` | Feature extraction |
| `test_process_features_normalization` | Feature normalization |
| `test_process_image` | Image processing |
| `test_resize_image` | Image resizing |
| `test_normalize_image` | Image normalization |
| `test_grayscale` | Grayscale conversion |
| `test_stack_frames` | Frame stacking |
| `test_speed_reward` | Speed reward component |
| `test_lane_reward` | Lane keeping reward |
| `test_heading_reward` | Heading reward |
| `test_collision_penalty` | Collision penalty |
| `test_custom_weights` | Custom reward weights |

**Agent Tests (`test_agent.py`):**

| Test | Description |
|------|-------------|
| `test_init` | Trainer initialization |
| `test_hyperparameters` | Hyperparameter storage |
| `test_train_short` | Short training run |
| `test_predict` | Action prediction |
| `test_save_load` | Model save/load |
| `test_evaluate` | Evaluation |

### 2. Integration Tests

**Gymnasium Compatibility:**
```python
def test_gymnasium_compatibility(self):
    env = MockCarlaRLEnv()
    assert isinstance(env, gym.Env)
    assert hasattr(env, "observation_space")
    assert hasattr(env, "action_space")
```

**SB3 Compatibility:**
```python
def test_sb3_compatibility(self):
    from stable_baselines3.common.env_checker import check_env
    env = MockCarlaRLEnv()
    check_env(env)  # Validates interface
```

**Training Integration:**
```python
def test_training_loop(self):
    from stable_baselines3 import PPO
    env = MockCarlaRLEnv(max_steps=100)
    model = PPO("MlpPolicy", env, verbose=0)
    model.learn(total_timesteps=128)
```

## Test Fixtures

**Environment Fixture:**
```python
@pytest.fixture
def env():
    env = MockCarlaRLEnv(seed=42)
    yield env
    env.close()
```

**Temporary Directory:**
```python
def test_save_load(self, tmp_path):
    save_path = str(tmp_path / "model")
    trainer.save(save_path)
```

## Expected Results

### Unit Tests

All unit tests should pass with:
- No CARLA installation required
- Deterministic results (fixed seed)
- Fast execution (< 30 seconds total)

### Integration Tests

Integration tests verify:
- Gymnasium API compliance
- SB3 compatibility
- Training loop functionality

## Debugging Tests

### Verbose Output

```bash
pytest src/tests/ -v -s
```

### Print Statements

```python
def test_step(self):
    env = MockCarlaRLEnv(seed=42)
    obs, info = env.reset()
    print(f"Observation: {obs}")
    print(f"Info: {info}")
```

### Debugger

```bash
pytest src/tests/ --pdb  # Drop into debugger on failure
```

## Coverage Report

```bash
# Generate coverage report
pytest src/tests/ --cov=carla_rl --cov-report=html

# View report
open htmlcov/index.html
```

**Target Coverage:**
- Overall: > 80%
- Core modules: > 90%

## Continuous Integration

**GitHub Actions Example:**
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: pip install -e .
      - run: pytest src/tests/ --cov=carla_rl
```

## Common Issues

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'carla_rl'`

**Solution:**
```bash
pip install -e .
```

### CARLA Import Errors

**Problem:** `ImportError: CARLA Python API not found`

**Solution:** Use mock environment for testing:
```bash
pytest src/tests/ -k "not carla"
```

### Timeout Errors

**Problem:** Tests hang or timeout

**Solution:** Check for infinite loops in environment reset/step.

## Best Practices

1. **Isolation:** Each test should be independent
2. **Determinism:** Use fixed seeds for reproducibility
3. **Speed:** Mock external dependencies
4. **Coverage:** Test both success and failure paths
5. **Documentation:** Clear test names and docstrings
