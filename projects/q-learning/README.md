# Q-Learning

A comprehensive Python implementation of Q-Learning and related reinforcement learning algorithms with multiple environments and visualization tools.

## Overview

This project implements several reinforcement learning algorithms:

- **Q-Learning**: Off-policy TD control with epsilon-greedy and Boltzmann exploration
- **Sarsa**: On-policy TD control
- **Expected Sarsa**: Off-policy TD control using expected values
- **Double Q-Learning**: Reduces overestimation bias using two Q-tables

## Project Structure

```
q-learning/
├── src/
│   ├── __init__.py          # Package exports
│   ├── grid_world.py        # Grid World environment
│   ├── q_learning.py        # Q-Learning agent
│   ├── sarsa.py             # Sarsa and Expected Sarsa
│   ├── double_q_learning.py # Double Q-Learning
│   ├── environments.py      # FrozenLake, Maze, SimpleGame
│   └── visualization.py     # Visualization utilities
├── tests/
│   ├── test_grid_world.py   # Environment tests
│   ├── test_q_learning.py   # Agent tests
│   ├── test_sarsa.py        # Sarsa tests
│   ├── test_double_q_learning.py  # Double Q-Learning tests
│   └── test_environments.py # Additional environment tests
├── docs/
│   ├── 01_RESEARCH.md       # Background research
│   ├── 02_DESIGN.md         # Architecture design
│   ├── 03_IMPLEMENTATION.md # Implementation details
│   ├── 04_TESTING.md        # Testing strategy
│   └── 05_DEVELOPMENT.md    # Development guide
├── README.md
└── LEARNING_NOTES.md
```

## Quick Start

### Installation

```bash
cd projects/q-learning
pip install numpy pytest
```

### Basic Usage

```python
from src.grid_world import GridWorld
from src.q_learning import QLearningAgent
from src.sarsa import SarsaAgent, SarsaConfig
from src.double_q_learning import DoubleQLearningAgent
from src.environments import FrozenLake, Maze

# Q-Learning
env = GridWorld(rows=5, cols=5, start=(0, 0), goal=(4, 4))
agent = QLearningAgent(n_states=25, n_actions=4, alpha=0.1, gamma=0.99)
result = agent.train(env, n_episodes=1000, max_steps=200)

# Sarsa
config = SarsaConfig(n_states=25, n_actions=4, alpha=0.1, gamma=0.99)
sarsa_agent = SarsaAgent(config)
result = sarsa_agent.train(env, n_episodes=1000, max_steps=200)

# Expected Sarsa
expected_sarsa = ExpectedSarsaAgent(config)
result = expected_sarsa.train(env, n_episodes=1000, max_steps=200)

# Double Q-Learning
double_agent = DoubleQLearningAgent(n_states=25, n_actions=4, alpha=0.1, gamma=0.99)
result = double_agent.train(env, n_episodes=1000, max_steps=200)

# FrozenLake
frozen_env = FrozenLake(map_name="4x4", is_slippery=True)
frozen_agent = QLearningAgent(n_states=16, n_actions=4, alpha=0.1, gamma=0.99)
result = frozen_agent.train(frozen_env, n_episodes=1000, max_steps=100)

# Maze
maze_env = Maze(seed=42)
maze_agent = QLearningAgent(n_states=maze_env.n_states, n_actions=4, alpha=0.1, gamma=0.99)
result = maze_agent.train(maze_env, n_episodes=1000, max_steps=500)
```

### Visualization

```python
from src.visualization import (
    visualize_training,
    visualize_policy,
    visualize_q_table_heatmap,
    visualize_learning_curves,
    visualize_strategy_comparison,
)

# Training progress
print(visualize_training(result.episode_rewards, result.episode_steps))

# Learned policy
policy = agent.get_policy(env)
print(visualize_policy(env.grid, policy, env.start.to_tuple(), env.goal.to_tuple()))

# Q-table heatmap
print(visualize_q_table_heatmap(agent.q_table, env.rows, env.cols))

# Compare algorithms
curves = {
    "Q-Learning": q_result.episode_rewards,
    "Sarsa": sarsa_result.episode_rewards,
    "Double Q-Learning": double_result.episode_rewards,
}
print(visualize_learning_curves(curves))

# Compare strategies
results = {
    "Q-Learning": q_metrics,
    "Sarsa": sarsa_metrics,
    "Double Q-Learning": double_metrics,
}
print(visualize_strategy_comparison(results))
```

## Algorithms

### Q-Learning (Off-Policy)

```
Q(s, a) = Q(s, a) + α * [r + γ * max(Q(s', a')) - Q(s, a)]
```

- Uses max Q-value for next state (off-policy)
- Can learn optimal policy while exploring
- May overestimate Q-values

### Sarsa (On-Policy)

```
Q(s, a) = Q(s, a) + α * [r + γ * Q(s', a') - Q(s, a)]
```

- Uses actual action taken in next state (on-policy)
- More conservative, learns about policy being followed
- No overestimation bias

### Expected Sarsa (Off-Policy)

```
Q(s, a) = Q(s, a) + α * [r + γ * Σ π(a'|s') * Q(s', a') - Q(s, a)]
```

- Uses expected value over all actions
- More stable than Q-Learning
- Better than Sarsa in stochastic environments

### Double Q-Learning

- Uses two Q-tables (Q_A and Q_B)
- Randomly selects which table to update
- Uses the other table for evaluation
- Reduces overestimation bias

## Environments

### GridWorld

- Configurable grid size
- Walls, traps, and goals
- Deterministic movement

### FrozenLake

- Classic RL environment
- Stochastic movement (slippery ice)
- Predefined 4x4 and 8x8 maps

### Maze

- Random maze generation
- DFS-based maze creation
- Configurable size

### SimpleGame

- Number guessing game
- Binary search-like learning
- Reward shaping for close guesses

## Hyperparameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| α (alpha) | 0.1 | Learning rate |
| γ (gamma) | 0.99 | Discount factor |
| ε (epsilon) | 1.0 | Initial exploration rate |
| ε_decay | 0.995 | Epsilon decay per episode |
| ε_min | 0.01 | Minimum epsilon |
| temperature | 1.0 | Boltzmann exploration temperature |

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_q_learning.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing
```

## Key Concepts

### Exploration vs Exploitation

- **Epsilon-Greedy**: Random action with probability ε
- **Boltzmann**: Actions proportional to Q-values
- **Decay**: Gradually shift from exploration to exploitation

### On-Policy vs Off-Policy

- **On-Policy (Sarsa)**: Learns about policy being followed
- **Off-Policy (Q-Learning)**: Can learn optimal policy while exploring

### Overestimation Bias

- Q-Learning uses max, which can overestimate
- Double Q-Learning uses two tables to reduce bias
- Expected Sarsa uses expected value, more stable

## Documentation

- **[Research](docs/01_RESEARCH.md)**: Background on Q-Learning and RL
- **[Design](docs/02_DESIGN.md)**: Architecture and design decisions
- **[Implementation](docs/03_IMPLEMENTATION.md)**: Code implementation details
- **[Testing](docs/04_TESTING.md)**: Testing strategy and coverage
- **[Development](docs/05_DEVELOPMENT.md)**: Development workflow and tips
- **[Learning Notes](LEARNING_NOTES.md)**: Key concepts and insights

## Key Learnings

1. **Exploration is critical**: Must balance exploration and exploitation
2. **Hyperparameters matter**: Learning rate, discount factor, and epsilon significantly affect performance
3. **Environment design**: Simpler environments learn faster
4. **Algorithm choice**: Q-Learning for simple tasks, Double Q-Learning for complex ones
5. **Convergence**: Monitor training progress to detect convergence

## License

This project is part of a learning portfolio and is for educational purposes.
