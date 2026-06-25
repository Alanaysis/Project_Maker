# Design: Q-Learning Architecture

## Overview

The Q-Learning project is designed with modularity, extensibility, and clarity in mind. The architecture separates concerns into distinct modules for environments, agents, and visualization.

## Architecture

### Module Structure

```
q-learning/
├── src/
│   ├── __init__.py          # Package exports
│   ├── grid_world.py        # Base grid environment
│   ├── q_learning.py        # Q-Learning algorithm
│   ├── sarsa.py             # Sarsa algorithms
│   ├── double_q_learning.py # Double Q-Learning
│   ├── environments.py      # Additional environments
│   └── visualization.py     # Visualization tools
├── tests/                   # Test suite
└── docs/                    # Documentation
```

### Design Principles

1. **Single Responsibility**: Each module has one clear purpose
2. **Open/Closed**: Easy to extend with new algorithms or environments
3. **Interface Segregation**: Clean interfaces between components
4. **Dependency Inversion**: Depend on abstractions, not implementations

## Component Design

### 1. Environment Interface

All environments implement a common interface:

```python
class Environment:
    def reset() -> State
    def step(action) -> Tuple[State, Reward, Done, Info]
    def get_state_index(state) -> int
    def index_to_state(index) -> State
```

#### GridWorld

- Configurable grid size
- Walls, traps, and goals
- Deterministic movement
- Customizable rewards

#### FrozenLake

- Classic RL benchmark
- Stochastic movement (slippery)
- Predefined maps (4x4, 8x8)
- Hole and goal states

#### Maze

- Random maze generation
- DFS-based algorithm
- Configurable size
- Path finding focus

#### SimpleGame

- Number guessing game
- Binary search learning
- Reward shaping
- Discretized state space

### 2. Agent Interface

All agents implement a common interface:

```python
class Agent:
    def choose_action(state) -> Action
    def update(state, action, reward, next_state, done) -> float
    def decay_epsilon()
    def train(env, n_episodes) -> TrainingResult
    def get_policy(env) -> Policy
    def evaluate(env, n_episodes) -> Metrics
```

#### QLearningAgent

**Algorithm**:
```
Q(s, a) = Q(s, a) + α * [r + γ * max(Q(s', a')) - Q(s, a)]
```

**Features**:
- Epsilon-greedy exploration
- Boltzmann exploration
- Configurable hyperparameters
- Training history tracking

#### SarsaAgent

**Algorithm**:
```
Q(s, a) = Q(s, a) + α * [r + γ * Q(s', a') - Q(s, a)]
```

**Features**:
- On-policy learning
- More conservative updates
- Better for risky environments

#### ExpectedSarsaAgent

**Algorithm**:
```
Q(s, a) = Q(s, a) + α * [r + γ * Σ π(a'|s') * Q(s', a') - Q(s, a)]
```

**Features**:
- Expected value calculation
- More stable than Q-Learning
- Off-policy learning

#### DoubleQLearningAgent

**Algorithm**:
- Uses two Q-tables (Q_A, Q_B)
- Randomly selects which to update
- Uses the other for evaluation

**Features**:
- Reduces overestimation bias
- More accurate value estimates
- Better for complex environments

### 3. Visualization Module

**Functions**:
- `visualize_training()`: ASCII training progress plots
- `visualize_policy()`: Grid policy visualization
- `visualize_q_values()`: Q-value heatmap
- `visualize_q_table_heatmap()`: Detailed Q-table heatmap
- `visualize_learning_curves()`: Algorithm comparison
- `visualize_strategy_comparison()`: Strategy metrics comparison

## Data Flow

### Training Loop

```
1. Initialize environment and agent
2. For each episode:
   a. Reset environment
   b. While not done:
      - Agent chooses action
      - Environment returns (next_state, reward, done, info)
      - Agent updates Q-values
      - Track statistics
   c. Decay epsilon
3. Return training result
```

### Update Flow

```
1. Get current state index
2. Choose action (explore/exploit)
3. Take action in environment
4. Get next state, reward, done
5. Calculate TD target:
   - Q-Learning: max(Q(s', a'))
   - Sarsa: Q(s', a') (actual action)
   - Expected Sarsa: Σ π(a'|s') * Q(s', a')
   - Double Q-Learning: Q_B(s', argmax Q_A(s', a'))
6. Update Q-value:
   Q(s, a) += α * (target - Q(s, a))
7. Return TD error
```

## State Representation

### Grid-Based States

- 2D grid with (row, col) positions
- Flat index: `state_idx = row * cols + col`
- Inverse: `(row, col) = (state_idx // cols, state_idx % cols)`

### Discretized States

- Continuous state space divided into buckets
- Example: SimpleGame uses (low_bucket, high_bucket, attempt)

## Hyperparameter Design

### Learning Rate (α)

- Controls update magnitude
- Typical range: [0.01, 0.5]
- Higher: faster learning, less stable
- Lower: slower learning, more stable

### Discount Factor (γ)

- Controls importance of future rewards
- Typical range: [0.9, 0.99]
- Higher: values future more
- Lower: values immediate reward more

### Epsilon (ε)

- Controls exploration rate
- Initial: 1.0 (full exploration)
- Decay: 0.995 per episode
- Minimum: 0.01 (some exploration)

### Temperature (τ)

- Controls Boltzmann exploration
- Higher: more exploration
- Lower: more exploitation

## Testing Strategy

### Unit Tests

- Test each component independently
- Verify algorithm correctness
- Check edge cases

### Integration Tests

- Test agent-environment interaction
- Verify training convergence
- Check policy quality

### Performance Tests

- Measure training time
- Compare algorithm efficiency
- Test on different environments

## Extension Points

### Adding New Algorithms

1. Create new agent class
2. Implement required interface methods
3. Add to `__init__.py` exports
4. Add tests

### Adding New Environments

1. Create new environment class
2. Implement required interface methods
3. Add to `environments.py`
4. Add tests

### Adding New Visualizations

1. Add function to `visualization.py`
2. Follow existing patterns
3. Add to `__init__.py` exports
4. Add tests

## Future Improvements

### Planned Features

1. **Function Approximation**: Neural network Q-functions
2. **Eligibility Traces**: TD(λ) methods
3. **Prioritized Experience Replay**: Better sample efficiency
4. **Multi-Agent**: Multiple agents learning simultaneously

### Optimization Opportunities

1. **Vectorized Operations**: NumPy optimizations
2. **Parallel Training**: Multi-process training
3. **GPU Support**: CUDA acceleration
4. **Distributed Learning**: Multi-machine training

## Conclusion

The architecture provides a solid foundation for reinforcement learning research and experimentation. The modular design allows for easy extension and modification while maintaining code clarity and testability.
