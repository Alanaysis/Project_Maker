# Implementation: Q-Learning Details

## Overview

This document describes the implementation details of the Q-Learning project, including code structure, key algorithms, and design decisions.

## Core Implementation

### 1. GridWorld Environment

**File**: `src/grid_world.py`

**Key Features**:
- Configurable grid size (rows x cols)
- Cell types: empty (0), wall (1), goal (2), trap (3)
- Agent position tracking
- Action space: UP, RIGHT, DOWN, LEFT

**Implementation**:
```python
class GridWorld:
    def __init__(self, rows, cols, start, goal, walls, traps, seed):
        self.grid = np.zeros((rows, cols), dtype=np.int32)
        # Set walls, goal, traps
        self.agent_pos = State(start[0], start[1])

    def step(self, action):
        # Calculate new position
        # Check validity
        # Return (next_state, reward, done, info)
```

**Rewards**:
- Step: -1.0 (encourages efficiency)
- Goal: +100.0
- Trap: -100.0
- Wall: -5.0

### 2. Q-Learning Agent

**File**: `src/q_learning.py`

**Key Components**:
- Q-table: numpy array (n_states x n_actions)
- Exploration strategies: epsilon-greedy, Boltzmann
- Hyperparameter management
- Training history tracking

**Q-Learning Update**:
```python
def update(self, state, action, reward, next_state, done, env):
    state_idx = env.get_state_index(*state)
    next_state_idx = env.get_state_index(*next_state)

    current_q = self.q_table[state_idx, action]

    if done:
        target_q = reward
    else:
        target_q = reward + self.gamma * np.max(self.q_table[next_state_idx])

    td_error = target_q - current_q
    self.q_table[state_idx, action] += self.alpha * td_error

    return td_error
```

**Training Loop**:
```python
def train(self, env, n_episodes, max_steps):
    for episode in range(n_episodes):
        state = env.reset()
        episode_reward = 0.0

        for step in range(max_steps):
            action = self.choose_action(state, env)
            next_state, reward, done, info = env.step(action)
            self.update(state, action, reward, next_state, done, env)

            episode_reward += reward
            state = next_state

            if done:
                break

        self.decay_epsilon()
        # Record statistics
```

### 3. Sarsa Implementation

**File**: `src/sarsa.py`

**Key Difference**: On-policy learning
- Uses actual action taken in next state
- More conservative updates
- Better for risky environments

**Sarsa Update**:
```python
def update(self, state_idx, action, reward, next_state_idx, next_action, done):
    current_q = self.q_table[state_idx, action]

    if done:
        target_q = reward
    else:
        target_q = reward + self.gamma * self.q_table[next_state_idx, next_action]

    td_error = target_q - current_q
    self.q_table[state_idx, action] += self.alpha * td_error

    return td_error
```

**Training Loop** (requires next action):
```python
def train(self, env, n_episodes, max_steps):
    for episode in range(n_episodes):
        state = env.reset()
        state_idx = env.get_state_index(*state)
        action = self.choose_action(state_idx)

        for step in range(max_steps):
            next_state, reward, done, info = env.step(action)
            next_state_idx = env.get_state_index(*next_state)

            if done:
                self.update(state_idx, action, reward, next_state_idx, 0, done)
                break

            next_action = self.choose_action(next_state_idx)
            self.update(state_idx, action, reward, next_state_idx, next_action, done)

            state_idx = next_state_idx
            action = next_action
```

### 4. Expected Sarsa Implementation

**File**: `src/sarsa.py` (same file as Sarsa)

**Key Difference**: Uses expected value
- More stable than Q-Learning
- Better in stochastic environments

**Expected Sarsa Update**:
```python
def update(self, state_idx, action, reward, next_state_idx, next_action, done):
    current_q = self.q_table[state_idx, action]

    if done:
        target_q = reward
    else:
        # Calculate expected Q-value under current policy
        policy_probs = self._get_policy_probs(next_state_idx)
        expected_q = np.sum(policy_probs * self.q_table[next_state_idx])
        target_q = reward + self.gamma * expected_q

    td_error = target_q - current_q
    self.q_table[state_idx, action] += self.alpha * td_error

    return td_error

def _get_policy_probs(self, state_idx):
    """Get action probabilities under epsilon-greedy policy."""
    probs = np.ones(self.n_actions) * (self.epsilon / self.n_actions)
    best_action = self._get_best_action(state_idx)
    probs[best_action] += (1.0 - self.epsilon)
    return probs
```

### 5. Double Q-Learning Implementation

**File**: `src/double_q_learning.py`

**Key Features**:
- Two Q-tables (Q_A, Q_B)
- Random selection for updates
- Reduces overestimation bias

**Double Q-Learning Update**:
```python
def update(self, state_idx, action, reward, next_state_idx, done):
    if done:
        target_q = reward
        # Update both tables equally
        td_a = target_q - self.q_table_a[state_idx, action]
        td_b = target_q - self.q_table_b[state_idx, action]
        self.q_table_a[state_idx, action] += self.alpha * td_a
        self.q_table_b[state_idx, action] += self.alpha * td_b
        return (td_a + td_b) / 2.0

    # Randomly choose which table to update
    if self.rng.random() < 0.5:
        # Update Q_A, evaluate with Q_B
        best_action = np.argmax(self.q_table_a[next_state_idx])
        target_q = reward + self.gamma * self.q_table_b[next_state_idx, best_action]
        td_error = target_q - self.q_table_a[state_idx, action]
        self.q_table_a[state_idx, action] += self.alpha * td_error
    else:
        # Update Q_B, evaluate with Q_A
        best_action = np.argmax(self.q_table_b[next_state_idx])
        target_q = reward + self.gamma * self.q_table_a[next_state_idx, best_action]
        td_error = target_q - self.q_table_b[state_idx, action]
        self.q_table_b[state_idx, action] += self.alpha * td_error

    return td_error
```

## Environment Implementations

### 1. FrozenLake

**File**: `src/environments.py`

**Key Features**:
- Predefined maps (4x4, 8x8)
- Stochastic movement (slippery)
- Hole and goal states

**Slippery Movement**:
```python
if self.is_slippery:
    prob = self.rng.random()
    if prob < 0.1:
        action = (action - 1) % 4  # Turn left
    elif prob < 0.2:
        action = (action + 1) % 4  # Turn right
    # else: intended action (80%)
```

### 2. Maze

**File**: `src/environments.py`

**Key Features**:
- Random maze generation using DFS
- Configurable size
- Wall penalties

**Maze Generation**:
```python
def _generate_maze(self, rows, cols):
    # Initialize with walls
    maze = np.ones((rows, cols), dtype=np.int32)

    # Carve paths using DFS
    def carve(r, c):
        maze[r, c] = 0
        directions = [(0, 2), (2, 0), (0, -2), (-2, 0)]
        self.rng.shuffle(directions)

        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 1 <= nr < rows - 1 and 1 <= nc < cols - 1 and maze[nr, nc] == 1:
                maze[r + dr // 2, c + dc // 2] = 0
                carve(nr, nc)

    carve(1, 1)
    return maze
```

### 3. SimpleGame

**File**: `src/environments.py`

**Key Features**:
- Number guessing game
- Discretized state space
- Reward shaping for close guesses

**State Discretization**:
```python
def _get_state(self):
    low_bucket = min(self.n_buckets - 1, int(self.low / self.max_number * self.n_buckets))
    high_bucket = min(self.n_buckets - 1, int(self.high / self.max_number * self.n_buckets))
    return (low_bucket, high_bucket, self.attempt)
```

## Visualization Implementation

**File**: `src/visualization.py`

### ASCII Plot

```python
def _ascii_plot(data, width=50, height=10):
    # Resample data to fit width
    # Normalize to height
    # Create plot grid
    # Build string with Unicode block characters
```

### Q-Table Heatmap

```python
def visualize_q_table_heatmap(q_table, rows, cols, title):
    # Get max Q-value for each state
    # Normalize to intensity characters
    # Create ASCII heatmap
```

### Learning Curves Comparison

```python
def visualize_learning_curves(curves, window, title):
    # Calculate moving averages
    # Compare final performance
    # Create ASCII visualization
```

## Design Decisions

### 1. State Representation

**Decision**: Use flat state indices for Q-tables.

**Reasoning**:
- Efficient memory usage
- Fast lookup
- Compatible with numpy operations

**Implementation**:
```python
state_idx = row * cols + col
```

### 2. Exploration Strategy

**Decision**: Support both epsilon-greedy and Boltzmann.

**Reasoning**:
- Epsilon-greedy: simple, effective
- Boltzmann: smoother exploration
- User can choose based on problem

### 3. Hyperparameter Management

**Decision**: Use dataclasses for configuration.

**Reasoning**:
- Type safety
- Default values
- Easy serialization

**Example**:
```python
@dataclass
class SarsaConfig:
    n_states: int
    n_actions: int
    alpha: float = 0.1
    gamma: float = 0.99
    epsilon: float = 1.0
    epsilon_decay: float = 0.995
    epsilon_min: float = 0.01
```

### 4. Training Result

**Decision**: Use dataclass for training results.

**Reasoning**:
- Structured data
- Easy to extend
- Clear interface

**Example**:
```python
@dataclass
class TrainingResult:
    episode_rewards: list[float] = field(default_factory=list)
    episode_steps: list[int] = field(default_factory=list)
    q_table_history: list[np.ndarray] = field(default_factory=list)
    total_episodes: int = 0
    convergence_episode: Optional[int] = None
```

### 5. Visualization

**Decision**: Use ASCII-based visualization.

**Reasoning**:
- No external dependencies
- Works in any terminal
- Easy to understand

## Performance Considerations

### 1. Memory Usage

- Q-table size: O(n_states × n_actions)
- GridWorld 5×5: 25 × 4 = 100 entries
- FrozenLake 8×8: 64 × 4 = 256 entries
- Maze 11×11: 121 × 4 = 484 entries

### 2. Training Time

- Q-Learning: O(n_episodes × max_steps)
- Sarsa: O(n_episodes × max_steps)
- Double Q-Learning: O(n_episodes × max_steps)

### 3. Convergence

- Depends on environment complexity
- Typically 100-1000 episodes for simple grids
- May need 10000+ for complex environments

## Testing Strategy

### 1. Unit Tests

- Test each method independently
- Verify algorithm correctness
- Check edge cases

### 2. Integration Tests

- Test agent-environment interaction
- Verify training convergence
- Check policy quality

### 3. Performance Tests

- Measure training time
- Compare algorithm efficiency
- Test on different environments

## Future Improvements

### 1. Function Approximation

- Neural network Q-functions
- Better generalization
- Handle large state spaces

### 2. Eligibility Traces

- TD(λ) methods
- Faster learning
- Better credit assignment

### 3. Prioritized Experience Replay

- Better sample efficiency
- Focus on important transitions
- Faster convergence

### 4. Multi-Agent Support

- Multiple agents learning simultaneously
- Cooperative or competitive
- Communication between agents

## Conclusion

The implementation provides a solid foundation for reinforcement learning research. The modular design allows for easy extension while maintaining code clarity and testability. Key design decisions prioritize simplicity and educational value.
