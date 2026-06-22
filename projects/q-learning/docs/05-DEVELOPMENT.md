# 05 - Development: Q-Learning

## Development Environment Setup

### Prerequisites

- Python 3.9+
- NumPy

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install numpy pytest
```

### Project Structure

```
q-learning/
├── src/
│   ├── __init__.py
│   ├── grid_world.py
│   ├── q_learning.py
│   └── visualization.py
├── tests/
│   ├── __init__.py
│   ├── test_grid_world.py
│   ├── test_q_learning.py
│   └── test_visualization.py
├── docs/
│   ├── 01-RESEARCH.md
│   ├── 02-DESIGN.md
│   ├── 03-IMPLEMENTATION.md
│   ├── 04-TESTING.md
│   └── 05-DEVELOPMENT.md
├── README.md
└── LEARNING_NOTES.md
```

## Running the Code

### Basic Usage

```python
from src.grid_world import GridWorld
from src.q_learning import QLearningAgent

# Create environment
env = GridWorld(
    rows=5,
    cols=5,
    start=(0, 0),
    goal=(4, 4),
    walls=[(1, 1), (2, 2), (3, 1)],
    traps=[(3, 3)],
)

# Create agent
agent = QLearningAgent(
    n_states=env.n_states,
    n_actions=env.n_actions,
    alpha=0.1,
    gamma=0.99,
    epsilon=1.0,
    epsilon_decay=0.995,
    seed=42,
)

# Train
result = agent.train(env, n_episodes=1000, max_steps=200, verbose=True)

# Evaluate
metrics = agent.evaluate(env, n_episodes=100)
print(f"Success rate: {metrics['success_rate']:.1%}")

# Get learned policy
policy = agent.get_policy(env)
```

### Visualization

```python
from src.visualization import (
    visualize_training,
    visualize_policy,
    visualize_q_values,
)

# Training progress
print(visualize_training(result.episode_rewards, result.episode_steps))

# Learned policy
print(visualize_policy(env.grid, policy, env.start.to_tuple(), env.goal.to_tuple()))

# Q-value map
value_map = agent.get_value_map(env)
print(visualize_q_values(env.grid, value_map, env.start.to_tuple(), env.goal.to_tuple()))
```

## Development Workflow

### 1. Feature Development

1. Create feature branch
2. Implement changes
3. Write tests
4. Run tests
5. Update documentation
6. Submit for review

### 2. Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_q_learning.py::TestQLearningAgent::test_update_q_value -v

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing
```

### 3. Code Quality

```bash
# Linting
pylint src/ tests/

# Type checking
mypy src/

# Formatting
black src/ tests/
```

## Common Development Tasks

### Adding a New Exploration Strategy

1. Add to `ExplorationStrategy` enum in `q_learning.py`:
```python
class ExplorationStrategy(Enum):
    EPSILON_GREEDY = "epsilon_greedy"
    BOLTZMANN = "boltzmann"
    UCB = "ucb"  # New
```

2. Implement the strategy in `QLearningAgent`:
```python
def _ucb(self, state_idx: int) -> int:
    # Implement UCB selection
    pass
```

3. Update `choose_action` to handle new strategy:
```python
def choose_action(self, state, env):
    if self.strategy == ExplorationStrategy.UCB:
        return self._ucb(state_idx)
    # ... existing strategies
```

4. Add tests for the new strategy

### Adding a New Environment

1. Create new environment class implementing similar interface:
```python
class NewEnvironment:
    def reset(self) -> tuple:
        pass

    def step(self, action: int) -> tuple[tuple, float, bool, dict]:
        pass

    @property
    def n_states(self) -> int:
        pass

    @property
    def n_actions(self) -> int:
        pass
```

2. The Q-Learning agent can work with any environment that implements this interface.

### Modifying Reward Structure

Edit the reward constants in `GridWorld`:

```python
class GridWorld:
    REWARD_STEP = -1.0      # Step penalty
    REWARD_GOAL = 100.0     # Goal reward
    REWARD_TRAP = -100.0    # Trap penalty
    REWARD_WALL = -5.0      # Wall penalty
```

## Troubleshooting

### Agent Doesn't Learn

1. **Check learning rate**: Too high → unstable, too low → slow
2. **Check discount factor**: Too low → doesn't value future
3. **Check exploration**: Too little → gets stuck, too much → doesn't exploit
4. **Check reward structure**: Ensure goal reward is significant

### Training is Slow

1. **Increase learning rate** (carefully)
2. **Reduce grid size** for testing
3. **Increase epsilon decay** for faster exploitation
4. **Reduce max_steps** per episode

### Q-Values Diverge

1. **Reduce learning rate**
2. **Increase discount factor** (closer to 1.0)
3. **Clip rewards** to reasonable range
4. **Use experience replay** (advanced)

## Performance Optimization

### For Large State Spaces

1. **Function approximation**: Replace Q-table with neural network
2. **Tile coding**: Efficient state representation
3. **Experience replay**: Break correlation in updates

### For Fast Training

1. **Vectorized operations**: Use NumPy for batch updates
2. **Parallel environments**: Run multiple envs simultaneously
3. **Prioritized experience replay**: Focus on important transitions

## Extending the Project

### Ideas for Extension

1. **Deep Q-Network (DQN)**: Replace Q-table with neural network
2. **SARSA**: On-policy variant
3. **Expected SARSA**: Uses expected value instead of max
4. **Double Q-Learning**: Reduces overestimation bias
5. **Multi-agent**: Multiple agents in same environment
6. **Stochastic environment**: Probabilistic transitions
7. **Continuous actions**: Extend to continuous action spaces
8. **Hierarchical RL**: Temporal abstraction
