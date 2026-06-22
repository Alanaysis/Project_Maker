# 04 - Testing: Q-Learning

## Testing Strategy

The testing approach covers:
1. **Unit tests**: Individual component testing
2. **Integration tests**: Component interaction testing
3. **Behavioral tests**: Algorithm correctness verification

## Test Structure

```
tests/
├── test_grid_world.py      # Environment tests
├── test_q_learning.py      # Agent tests
└── test_visualization.py   # Visualization tests
```

## Grid World Tests

### State Tests

- **Creation**: Verify row/col assignment
- **Equality**: Two states with same coordinates are equal
- **Hashing**: Equal states have same hash
- **Conversion**: to_tuple() returns correct tuple

### Environment Tests

#### Initialization

```python
def test_initialization():
    env = GridWorld(rows=5, cols=5, start=(0, 0), goal=(4, 4))
    assert env.rows == 5
    assert env.cols == 5
```

#### Grid Setup

```python
def test_grid_with_walls():
    walls = [(1, 1), (2, 2)]
    env = GridWorld(rows=5, cols=5, walls=walls)
    assert env.grid[1, 1] == 1
    assert env.grid[2, 2] == 1
```

#### Movement

```python
def test_step_valid_move():
    env = GridWorld(rows=5, cols=5, start=(2, 2), goal=(4, 4))
    env.reset()
    next_state, reward, done, info = env.step(Action.RIGHT)
    assert next_state == (2, 3)
    assert reward == GridWorld.REWARD_STEP
    assert not done
```

#### Collisions

```python
def test_step_into_wall():
    walls = [(1, 1)]
    env = GridWorld(rows=5, cols=5, start=(1, 0), goal=(4, 4), walls=walls)
    env.reset()
    next_state, reward, done, info = env.step(Action.RIGHT)
    assert next_state == (1, 0)  # Stay in place
    assert reward == GridWorld.REWARD_WALL
```

#### Terminal States

```python
def test_step_reach_goal():
    env = GridWorld(rows=5, cols=5, start=(3, 4), goal=(4, 4))
    env.reset()
    next_state, reward, done, info = env.step(Action.DOWN)
    assert next_state == (4, 4)
    assert reward == GridWorld.REWARD_GOAL
    assert done is True
```

#### State Index Conversion

```python
def test_state_index_conversion():
    env = GridWorld(rows=5, cols=5)
    assert env.get_state_index(0, 0) == 0
    assert env.get_state_index(0, 4) == 4
    assert env.get_state_index(1, 0) == 5
```

## Q-Learning Agent Tests

### Initialization Tests

```python
def test_initialization():
    agent = QLearningAgent(n_states=25, n_actions=4)
    assert agent.q_table.shape == (25, 4)
    assert np.all(agent.q_table == 0)
```

### Action Selection Tests

#### Epsilon-Greedy (Exploration)

```python
def test_choose_action_epsilon_greedy_explore():
    agent = QLearningAgent(n_states=25, n_actions=4, epsilon=1.0, seed=42)
    env = GridWorld(rows=5, cols=5)
    state = (0, 0)

    actions = set()
    for _ in range(100):
        action = agent.choose_action(state, env)
        actions.add(action)
    assert len(actions) > 1  # Multiple different actions
```

#### Epsilon-Greedy (Exploitation)

```python
def test_choose_action_epsilon_greedy_exploit():
    agent = QLearningAgent(n_states=25, n_actions=4, epsilon=0.0, seed=42)
    env = GridWorld(rows=5, cols=5)
    state = (0, 0)
    state_idx = env.get_state_index(*state)

    agent.q_table[state_idx] = [0.1, 0.9, 0.2, 0.3]

    for _ in range(100):
        action = agent.choose_action(state, env)
        assert action == 1  # Always best action
```

#### Boltzmann Exploration

```python
def test_choose_action_boltzmann():
    agent = QLearningAgent(
        n_states=25, n_actions=4,
        strategy=ExplorationStrategy.BOLTZMANN,
        temperature=1.0, seed=42
    )
    # Should choose actions with probability proportional to Q-values
```

### Q-Value Update Tests

#### Basic Update

```python
def test_update_q_value():
    agent = QLearningAgent(n_states=25, n_actions=4, alpha=0.1, gamma=0.9)
    env = GridWorld(rows=5, cols=5)
    state = (0, 0)
    next_state = (0, 1)
    action = Action.RIGHT

    # Q(s,a) = 0 + 0.1 * [10 + 0.9 * 0 - 0] = 1.0
    agent.update(state, action, 10.0, next_state, False, env)
    state_idx = env.get_state_index(*state)
    assert agent.q_table[state_idx, action] == pytest.approx(1.0)
```

#### Terminal State Update

```python
def test_update_terminal_state():
    # When done=True, target = reward (no future discount)
    agent.update(state, action, 100.0, next_state, True, env)
    assert agent.q_table[state_idx, action] == pytest.approx(10.0)
```

#### Update with Existing Q-Values

```python
def test_update_with_existing_q_values():
    # Verifies correct propagation of future values
    agent.q_table[state_idx, action] = 5.0
    agent.q_table[next_state_idx, :] = [10.0, 20.0, 30.0, 40.0]

    agent.update(state, action, 1.0, next_state, False, env)
    expected = 5.0 + 0.5 * (1.0 + 0.9 * 40.0 - 5.0)
    assert agent.q_table[state_idx, action] == pytest.approx(expected)
```

### Epsilon Decay Tests

```python
def test_decay_epsilon():
    agent = QLearningAgent(epsilon=1.0, epsilon_decay=0.9, epsilon_min=0.1)
    for _ in range(5):
        agent.decay_epsilon()
    assert agent.epsilon < 1.0
    assert agent.epsilon >= 0.1
```

### Training Tests

```python
def test_train_simple_grid():
    env = GridWorld(rows=3, cols=3, start=(0, 0), goal=(0, 1))
    agent = QLearningAgent(n_states=9, n_actions=4, alpha=0.5, gamma=0.9, seed=42)

    result = agent.train(env, n_episodes=100, max_steps=10)

    assert result.total_episodes > 0
    assert len(result.episode_rewards) > 0
```

### Evaluation Tests

```python
def test_evaluate():
    # Train first
    agent.train(env, n_episodes=200, max_steps=10)

    # Evaluate without exploration
    metrics = agent.evaluate(env, n_episodes=50, max_steps=10)

    assert "mean_reward" in metrics
    assert "success_rate" in metrics
    assert 0 <= metrics["success_rate"] <= 1
```

## Visualization Tests

### Training Visualization

```python
def test_visualize_training():
    rewards = [1.0, 2.0, 3.0, 4.0, 5.0]
    steps = [10, 8, 6, 4, 2]
    result = visualize_training(rewards, steps, window=3)

    assert "TRAINING PROGRESS" in result
    assert "Total Episodes: 5" in result
```

### Policy Visualization

```python
def test_visualize_policy():
    grid = np.zeros((3, 3), dtype=np.int32)
    grid[0, 2] = 2
    policy = np.array([[1, 1, 0], [2, 2, 0], [2, 2, 0]])

    result = visualize_policy(grid, policy, (0, 0), (0, 2))
    assert "S" in result
    assert "G" in result
```

## Test Coverage

| Component | Coverage Target | Key Tests |
|-----------|----------------|-----------|
| GridWorld | 95% | All cell types, boundaries, collisions |
| QLearningAgent | 95% | Update rules, exploration, convergence |
| Visualization | 90% | Output format, edge cases |

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_grid_world.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing
```
