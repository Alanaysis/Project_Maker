# Q-Learning

A Python implementation of the Q-Learning reinforcement learning algorithm with a grid world environment.

## Overview

Q-Learning is a model-free, off-policy reinforcement learning algorithm that learns the value of an action in a particular state. This implementation includes:

- **Grid World Environment**: A configurable 2D grid with walls, traps, and goals
- **Q-Learning Agent**: Core algorithm with epsilon-greedy and Boltzmann exploration
- **Visualization**: Text-based visualization of training progress, policies, and Q-values

## Project Structure

```
q-learning/
├── src/
│   ├── __init__.py          # Package exports
│   ├── grid_world.py        # Grid World environment
│   ├── q_learning.py        # Q-Learning agent
│   └── visualization.py     # Visualization utilities
├── tests/
│   ├── test_grid_world.py   # Environment tests
│   ├── test_q_learning.py   # Agent tests
│   └── test_visualization.py # Visualization tests
├── docs/
│   ├── 01-RESEARCH.md       # Background research
│   ├── 02-DESIGN.md         # Architecture design
│   ├── 03-IMPLEMENTATION.md # Implementation details
│   ├── 04-TESTING.md        # Testing strategy
│   └── 05-DEVELOPMENT.md    # Development guide
├── README.md
└── LEARNING_NOTES.md
```

## Quick Start

### Installation

```bash
# Clone or navigate to project
cd projects/q-learning

# Create virtual environment (optional)
python -m venv venv
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install numpy pytest
```

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
policy = agent.get_policy(env)
print(visualize_policy(env.grid, policy, env.start.to_tuple(), env.goal.to_tuple()))

# Q-value map
value_map = agent.get_value_map(env)
print(visualize_q_values(env.grid, value_map, env.start.to_tuple(), env.goal.to_tuple()))
```

## Core Concepts

### Q-Learning Update Rule

```
Q(s, a) = Q(s, a) + α * [r + γ * max(Q(s', a')) - Q(s, a)]
```

Where:
- `Q(s, a)`: Current Q-value for state s and action a
- `α`: Learning rate (how much to update)
- `r`: Immediate reward
- `γ`: Discount factor (importance of future rewards)
- `max(Q(s', a'))`: Best Q-value for next state

### Exploration Strategies

1. **Epsilon-Greedy**: Random action with probability ε, best action otherwise
2. **Boltzmann**: Actions chosen with probability proportional to Q-values

### Hyperparameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| α (alpha) | 0.1 | Learning rate |
| γ (gamma) | 0.99 | Discount factor |
| ε (epsilon) | 1.0 | Initial exploration rate |
| ε_decay | 0.995 | Epsilon decay per episode |
| ε_min | 0.01 | Minimum epsilon |

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_grid_world.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing
```

## Documentation

- **[Research](docs/01-RESEARCH.md)**: Background on Q-Learning and RL
- **[Design](docs/02-DESIGN.md)**: Architecture and design decisions
- **[Implementation](docs/03-IMPLEMENTATION.md)**: Code implementation details
- **[Testing](docs/04-TESTING.md)**: Testing strategy and coverage
- **[Development](docs/05-DEVELOPMENT.md)**: Development workflow and tips
- **[Learning Notes](LEARNING_NOTES.md)**: Key concepts and insights

## Examples

### Simple Grid (3x3)

```python
env = GridWorld(rows=3, cols=3, start=(0, 0), goal=(2, 2))
agent = QLearningAgent(n_states=9, n_actions=4, alpha=0.5, gamma=0.9, seed=42)
result = agent.train(env, n_episodes=100, max_steps=20)
```

### Complex Grid with Obstacles

```python
env = GridWorld(
    rows=7,
    cols=7,
    start=(0, 0),
    goal=(6, 6),
    walls=[(1, 1), (2, 2), (3, 3), (4, 2), (5, 1)],
    traps=[(3, 5), (5, 3)],
)
agent = QLearningAgent(n_states=49, n_actions=4, alpha=0.1, gamma=0.99)
result = agent.train(env, n_episodes=2000, max_steps=100)
```

## Key Learnings

1. **Exploration is critical**: Must balance exploration and exploitation
2. **Hyperparameters matter**: Learning rate, discount factor, and epsilon significantly affect performance
3. **Environment design**: Simpler environments learn faster
4. **Convergence**: Monitor training progress to detect convergence
5. **Limitations**: Q-table doesn't scale to large state spaces (see DQN)

## License

This project is part of a learning portfolio and is for educational purposes.
