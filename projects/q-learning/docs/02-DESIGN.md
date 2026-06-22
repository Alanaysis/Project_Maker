# 02 - Design: Q-Learning

## Architecture Overview

The Q-Learning implementation follows a modular design with clear separation of concerns:

```
q-learning/
├── src/
│   ├── __init__.py          # Package exports
│   ├── grid_world.py        # Environment definition
│   ├── q_learning.py        # Agent implementation
│   └── visualization.py     # Visualization utilities
├── tests/
│   ├── test_grid_world.py   # Environment tests
│   ├── test_q_learning.py   # Agent tests
│   └── test_visualization.py # Visualization tests
└── docs/
    ├── 01-RESEARCH.md
    ├── 02-DESIGN.md
    ├── 03-IMPLEMENTATION.md
    ├── 04-TESTING.md
    └── 05-DEVELOPMENT.md
```

## Core Components

### 1. Grid World Environment (`grid_world.py`)

The environment provides:
- **State representation**: 2D grid with cell types (empty, wall, goal, trap)
- **Action space**: 4 discrete actions (up, right, down, left)
- **Transition dynamics**: Deterministic movement with boundary/wall handling
- **Reward structure**: Step penalty, goal reward, trap penalty, wall penalty

#### Design Decisions

1. **State as (row, col) tuples**: Simple and intuitive representation
2. **Flat state index**: For efficient Q-table indexing
3. **Configurable grid**: Flexible grid setup with walls, traps, and goals
4. **Deterministic transitions**: Simplifies learning while maintaining core concepts

#### Class Diagram

```
GridWorld
├── rows: int
├── cols: int
├── start: State
├── goal: State
├── grid: np.ndarray
├── agent_pos: State
├── reset() → (row, col)
├── step(action) → (state, reward, done, info)
├── render() → str
└── get_all_states() → list[(row, col)]
```

### 2. Q-Learning Agent (`q_learning.py`)

The agent implements:
- **Q-table management**: Store and update Q-values
- **Action selection**: Epsilon-greedy and Boltzmann strategies
- **Learning**: Q-value updates using temporal difference
- **Training loop**: Episode-based training with convergence detection

#### Design Decisions

1. **NumPy Q-table**: Efficient storage and computation
2. **Strategy pattern**: Pluggable exploration strategies
3. **Training history**: Track rewards, steps, and Q-table snapshots
4. **Evaluation mode**: Separate evaluation without exploration

#### Class Diagram

```
QLearningAgent
├── q_table: np.ndarray (n_states × n_actions)
├── alpha: float (learning rate)
├── gamma: float (discount factor)
├── epsilon: float (exploration rate)
├── strategy: ExplorationStrategy
├── choose_action(state, env) → int
├── update(state, action, reward, next_state, done, env) → float
├── decay_epsilon()
├── train(env, n_episodes, ...) → TrainingResult
├── get_policy(env) → np.ndarray
└── evaluate(env, n_episodes, ...) → dict
```

### 3. Visualization (`visualization.py`)

Provides text-based visualizations:
- **Training progress**: Reward and step plots
- **Policy visualization**: Arrow-based policy display
- **Q-value heatmap**: Intensity-based value display
- **Episode path**: Path taken during an episode

#### Design Decisions

1. **Text-based output**: No external dependencies (matplotlib, etc.)
2. **ASCII plots**: Simple but effective visualization
3. **Modular functions**: Each visualization is independent

## Data Flow

### Training Loop

```
Initialize Q-table (zeros)
For each episode:
    state = env.reset()
    While not done:
        action = agent.choose_action(state)  # ε-greedy or Boltzmann
        next_state, reward, done = env.step(action)
        agent.update(state, action, reward, next_state)
        state = next_state
    agent.decay_epsilon()
```

### Q-Value Update

```
Current Q-value: Q(s, a)
Target: r + γ * max(Q(s', a'))
TD Error: target - current
New Q-value: Q(s, a) + α * TD_error
```

## Reward Structure

| Event | Reward | Purpose |
|-------|--------|---------|
| Each step | -1.0 | Encourage efficiency |
| Reach goal | +100.0 | Strong positive signal |
| Fall in trap | -100.0 | Strong negative signal |
| Hit wall | -5.0 | Mild penalty for invalid moves |

## Hyperparameter Choices

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| α (learning rate) | 0.1 | Balance between learning speed and stability |
| γ (discount factor) | 0.99 | Value future rewards highly |
| ε (initial) | 1.0 | Start with full exploration |
| ε decay | 0.995 | Gradual transition to exploitation |
| ε min | 0.01 | Maintain some exploration |

## Extensibility Points

1. **New environments**: Implement similar interface to GridWorld
2. **New exploration strategies**: Add to ExplorationStrategy enum
3. **New visualizations**: Add functions to visualization module
4. **Stochastic transitions**: Modify GridWorld.step() for probabilistic outcomes
5. **Larger state spaces**: Replace Q-table with function approximation
