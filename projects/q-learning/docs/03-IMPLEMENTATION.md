# 03 - Implementation: Q-Learning

## Implementation Overview

This document details the implementation decisions and code structure of the Q-Learning project.

## Grid World Implementation

### State Representation

States are represented as `(row, col)` tuples for simplicity and readability:

```python
@dataclass
class State:
    row: int
    col: int

    def to_tuple(self) -> tuple[int, int]:
        return (self.row, self.col)
```

For the Q-table, states are converted to flat indices:

```python
def get_state_index(self, row: int, col: int) -> int:
    return row * self.cols + col
```

### Action Space

Actions are defined as an enum for type safety:

```python
class Action(IntEnum):
    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3
```

Action deltas map actions to movement:

```python
deltas = {
    Action.UP: (-1, 0),
    Action.RIGHT: (0, 1),
    Action.DOWN: (1, 0),
    Action.LEFT: (0, -1),
}
```

### Grid Cell Types

```python
0 = empty (passable)
1 = wall (impassable)
2 = goal (terminal, positive reward)
3 = trap (terminal, negative reward)
```

### Step Function

The step function implements the environment dynamics:

```python
def step(self, action: int) -> tuple[tuple[int, int], float, bool, dict]:
    # Calculate new position
    dr, dc = self._action_to_delta(action)
    new_row = self.agent_pos.row + dr
    new_col = self.agent_pos.col + dc

    # Check validity
    if not self._is_valid(new_row, new_col):
        # Wall/boundary: stay in place, penalty
        return self.agent_pos.to_tuple(), REWARD_WALL, False, {"hit_wall": True}

    # Move agent
    self.agent_pos = State(new_row, new_col)
    cell_type = self.grid[new_row, new_col]

    # Determine reward and done status
    if cell_type == 2:  # Goal
        return state, REWARD_GOAL, True, {"reached_goal": True}
    elif cell_type == 3:  # Trap
        return state, REWARD_TRAP, True, {"fell_in_trap": True}
    else:  # Empty
        return state, REWARD_STEP, False, {}
```

## Q-Learning Agent Implementation

### Q-Table Initialization

The Q-table is initialized with zeros:

```python
self.q_table = np.zeros((n_states, n_actions))
```

This is a common initialization strategy that works well for environments with non-negative rewards. For environments with only negative rewards, a small positive initialization might encourage exploration.

### Epsilon-Greedy Exploration

```python
def _epsilon_greedy(self, state_idx: int) -> int:
    if self.rng.random() < self.epsilon:
        return self.rng.randint(self.n_actions)  # Explore
    else:
        return self._get_best_action(state_idx)  # Exploit
```

Key implementation detail: When exploiting, ties are broken randomly:

```python
def _get_best_action(self, state_idx: int) -> int:
    q_values = self.q_table[state_idx]
    max_q = np.max(q_values)
    best_actions = np.where(q_values == max_q)[0]
    return self.rng.choice(best_actions)
```

### Boltzmann Exploration

```python
def _boltzmann(self, state_idx: int) -> int:
    q_values = self.q_table[state_idx]

    # Prevent overflow by subtracting max
    scaled_q = q_values / self.temperature
    scaled_q -= np.max(scaled_q)

    # Softmax
    exp_q = np.exp(scaled_q)
    probabilities = exp_q / np.sum(exp_q)

    return self.rng.choice(self.n_actions, p=probabilities)
```

The temperature parameter controls exploration:
- High temperature → more uniform distribution → more exploration
- Low temperature → more peaked distribution → more exploitation

### Q-Value Update

The core update rule:

```python
def update(self, state, action, reward, next_state, done, env) -> float:
    state_idx = env.get_state_index(*state)
    next_state_idx = env.get_state_index(*next_state)

    # Current Q-value
    current_q = self.q_table[state_idx, action]

    # Target Q-value
    if done:
        target_q = reward
    else:
        target_q = reward + self.gamma * np.max(self.q_table[next_state_idx])

    # TD error
    td_error = target_q - current_q

    # Update
    self.q_table[state_idx, action] += self.alpha * td_error

    return td_error
```

### Epsilon Decay

```python
def decay_epsilon(self):
    self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
```

This is called at the end of each episode to gradually shift from exploration to exploitation.

### Training Loop

```python
def train(self, env, n_episodes, max_steps, ...):
    for episode in range(n_episodes):
        state = env.reset()

        for step in range(max_steps):
            action = self.choose_action(state, env)
            next_state, reward, done, info = env.step(action)
            self.update(state, action, reward, next_state, done, env)
            state = next_state

            if done:
                break

        self.decay_epsilon()
```

### Convergence Detection

```python
if episode >= convergence_window:
    recent_rewards = result.episode_rewards[-convergence_window:]
    older_rewards = result.episode_rewards[-2*convergence_window:-convergence_window]

    recent_avg = np.mean(recent_rewards)
    older_avg = np.mean(older_rewards)

    if abs(recent_avg - older_avg) < convergence_threshold:
        result.convergence_episode = episode
        break
```

## Visualization Implementation

### ASCII Plot

The ASCII plot converts data to a text-based visualization:

```python
def _ascii_plot(data, width=50, height=10):
    # Resample data to fit width
    # Normalize to height
    # Create grid of characters
    # Use █ for data points
```

### Policy Visualization

Policies are displayed using arrow symbols:

```python
ACTION_SYMBOLS = {0: "↑", 1: "→", 2: "↓", 3: "←"}
```

### Q-Value Heatmap

Q-values are displayed using intensity characters:

```python
intensity_chars = " .:-=+*#%@"
```

Higher intensity characters represent higher Q-values.

## Performance Considerations

1. **Q-table storage**: O(n_states × n_actions) space complexity
2. **Update computation**: O(1) per update
3. **Training complexity**: O(n_episodes × max_steps)
4. **NumPy operations**: Vectorized where possible for efficiency

## Edge Cases Handled

1. **Boundary collisions**: Agent stays in place with penalty
2. **Wall collisions**: Agent stays in place with penalty
3. **Terminal states**: Episode ends immediately
4. **Tied Q-values**: Random selection among best actions
5. **Numerical stability**: Overflow prevention in Boltzmann exploration
