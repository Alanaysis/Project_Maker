# Q-Learning: Learning Notes

## Key Concepts Learned

### 1. Reinforcement Learning Basics

**Reinforcement Learning (RL)** is a type of machine learning where an agent learns to make decisions by interacting with an environment. The agent receives rewards or penalties based on its actions and learns to maximize cumulative reward.

**Core RL Components:**
- **Agent**: The learner/decision maker
- **Environment**: The world the agent interacts with
- **State**: Current situation of the agent
- **Action**: What the agent can do
- **Reward**: Feedback from the environment
- **Policy**: Strategy for choosing actions

### 2. Q-Value and Bellman Equation

The **Q-function** Q(s, a) represents the expected cumulative reward of taking action `a` in state `s` and then following the optimal policy.

**Bellman Equation:**
```
Q(s, a) = E[r + γ * max_a' Q(s', a')]
```

This recursive relationship is fundamental to value-based RL. It states that the value of a state-action pair equals the immediate reward plus the discounted value of the best next state-action pair.

**Update Rule:**
```
Q(s, a) ← Q(s, a) + α * [r + γ * max(Q(s', a')) - Q(s, a)]
```

The term in brackets is the **temporal difference (TD) error** - the difference between what we expected and what actually happened.

### 3. Exploration vs Exploitation

This is a fundamental tradeoff in RL:

**Exploration:**
- Try new, unknown actions
- Discover potentially better strategies
- Essential in early learning
- May lead to short-term losses

**Exploitation:**
- Use known good actions
- Maximize immediate reward
- Important in later learning
- May miss better unknown strategies

**Epsilon-Greedy Strategy:**
- With probability ε: explore (random action)
- With probability 1-ε: exploit (best known action)
- ε typically decays over time

**Boltzmann Exploration:**
- Actions chosen with probability ∝ exp(Q/T)
- Temperature T controls exploration
- Higher T → more exploration
- Lower T → more exploitation

### 4. Hyperparameter Tuning

**Learning Rate (α):**
- Controls how much we update Q-values
- Too high: unstable, may diverge
- Too low: slow learning
- Typical: 0.01 - 0.5

**Discount Factor (γ):**
- Importance of future rewards
- γ = 0: only care about immediate reward
- γ = 1: future rewards as important as immediate
- Typical: 0.9 - 0.99

**Epsilon (ε):**
- Exploration rate
- Start high (1.0) for exploration
- Decay to low (0.01) for exploitation
- Decay rate: 0.99 - 0.999

### 5. Grid World Environment

A **grid world** is a simple 2D environment commonly used to teach RL concepts:

**Features:**
- Discrete states (grid cells)
- Discrete actions (up, right, down, left)
- Deterministic transitions
- Clear reward structure

**Cell Types:**
- Empty: passable, step penalty
- Wall: impassable, collision penalty
- Goal: terminal, positive reward
- Trap: terminal, negative reward

### 6. Q-Table

The **Q-table** is a lookup table that stores Q-values for all state-action pairs:

```
         Action0  Action1  Action2  Action3
State0   [  0.1,    0.9,    0.2,    0.3  ]
State1   [  0.5,    0.3,    0.8,    0.1  ]
...
```

**Initialization:** Typically zeros (optimistic) or small random values

**Update:** After each step, update the Q-value for the state-action pair taken

**Policy Extraction:** For each state, choose the action with highest Q-value

## Implementation Insights

### 1. State Representation

**Flat Index vs Tuple:**
- Tuples: (row, col) - intuitive, easy to understand
- Flat index: row * cols + col - efficient for Q-table

```python
# Conversion functions
def get_state_index(row, col):
    return row * cols + col

def index_to_state(index):
    return (index // cols, index % cols)
```

### 2. Action Selection with Tie Breaking

When multiple actions have the same Q-value, break ties randomly:

```python
def get_best_action(state_idx):
    q_values = q_table[state_idx]
    max_q = np.max(q_values)
    best_actions = np.where(q_values == max_q)[0]
    return np.random.choice(best_actions)
```

This prevents the agent from being biased toward certain actions when they're equally good.

### 3. Terminal State Handling

When an episode ends (done=True), there's no future reward:

```python
if done:
    target_q = reward
else:
    target_q = reward + gamma * max(q_table[next_state])
```

### 4. Numerical Stability in Boltzmann

Prevent overflow when computing softmax:

```python
scaled_q = q_values / temperature
scaled_q -= np.max(scaled_q)  # Prevent overflow
exp_q = np.exp(scaled_q)
probabilities = exp_q / np.sum(exp_q)
```

### 5. Convergence Detection

Monitor if the agent has learned the optimal policy:

```python
# Compare average rewards over recent episodes
recent_avg = mean(rewards[-window:])
older_avg = mean(rewards[-2*window:-window])

if abs(recent_avg - older_avg) < threshold:
    print("Converged!")
```

## Common Pitfalls

### 1. Learning Rate Too High

**Symptom:** Q-values oscillate, never converge

**Solution:** Reduce learning rate (e.g., from 0.5 to 0.1)

### 2. Insufficient Exploration

**Symptom:** Agent gets stuck in suboptimal policy

**Solution:** Increase initial epsilon or slow down decay

### 3. Discount Factor Too Low

**Symptom:** Agent doesn't value future rewards enough

**Solution:** Increase gamma (e.g., from 0.9 to 0.99)

### 4. Reward Shaping Issues

**Symptom:** Agent finds unexpected behaviors

**Solution:** Review reward structure, ensure goal reward is significant

### 5. Max Steps Too Low

**Symptom:** Agent can't reach goal in time

**Solution:** Increase max_steps or simplify environment

## Experimental Observations

### Experiment 1: Simple 3x3 Grid

**Setup:**
- 3x3 grid, start=(0,0), goal=(0,2)
- No walls or traps
- α=0.5, γ=0.9, ε=0.3

**Result:**
- Converges in ~50 episodes
- Learns optimal policy (right, right)
- Success rate: 100%

**Insight:** Simple environments converge quickly with moderate learning rate.

### Experiment 2: 5x5 Grid with Obstacles

**Setup:**
- 5x5 grid, start=(0,0), goal=(4,4)
- Walls at (1,1), (2,2), (3,1)
- Trap at (3,3)
- α=0.1, γ=0.99, ε=1.0, decay=0.995

**Result:**
- Converges in ~500 episodes
- Learns to navigate around walls
- Avoids trap
- Success rate: ~90%

**Insight:** More complex environments need more episodes and careful hyperparameter tuning.

### Experiment 3: Epsilon Decay Comparison

**Setup:** Same as Experiment 2, varying epsilon decay

| Decay Rate | Episodes to Converge | Final Success Rate |
|------------|---------------------|-------------------|
| 0.99 | 300 | 85% |
| 0.995 | 500 | 92% |
| 0.999 | 1000 | 95% |

**Insight:** Slower decay → better final performance but longer training.

## Key Takeaways

1. **Q-Learning is simple but powerful**: Easy to understand and implement, works well for discrete state/action spaces

2. **Hyperparameters matter**: Learning rate, discount factor, and exploration rate significantly affect performance

3. **Exploration is crucial**: Must balance exploration and exploitation for optimal learning

4. **Environment design affects learning**: Simpler environments learn faster; reward shaping guides behavior

5. **Convergence isn't guaranteed in practice**: Need to monitor and adjust; real-world problems often need more sophisticated methods

6. **Q-table has limitations**: Doesn't scale to large/continuous state spaces; need function approximation (neural networks)

## Next Steps for Learning

1. **Deep Q-Network (DQN)**: Replace Q-table with neural network for large state spaces
2. **SARSA**: On-policy variant for safer learning
3. **Policy Gradient Methods**: Directly optimize policy instead of values
4. **Actor-Critic**: Combine value and policy methods
5. **Multi-Agent RL**: Multiple agents interacting
6. **Transfer Learning**: Apply learned knowledge to new tasks
