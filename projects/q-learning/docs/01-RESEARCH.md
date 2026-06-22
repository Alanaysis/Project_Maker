# 01 - Research: Q-Learning

## What is Q-Learning?

Q-Learning is a **model-free**, **off-policy** reinforcement learning algorithm. It learns the value of an action in a particular state without requiring a model of the environment.

### Key Characteristics

- **Model-Free**: Does not need to know the transition probabilities of the environment
- **Off-Policy**: Can learn the optimal policy while following a different (exploratory) policy
- **Value-Based**: Learns value functions rather than directly learning a policy
- **Temporal Difference (TD)**: Updates estimates based on other estimates (bootstrapping)

## The Q-Function

The Q-function Q(s, a) represents the expected cumulative reward of taking action `a` in state `s` and then following the optimal policy thereafter.

### Bellman Equation

The Q-values are updated using the Bellman equation:

```
Q(s, a) = E[r + γ * max_a' Q(s', a')]
```

Where:
- `s` = current state
- `a` = action taken
- `r` = immediate reward
- `γ` (gamma) = discount factor (0 to 1)
- `s'` = next state
- `a'` = possible next actions

### Update Rule

The practical update rule used in Q-Learning:

```
Q(s, a) ← Q(s, a) + α * [r + γ * max(Q(s', a')) - Q(s, a)]
```

Where:
- `α` (alpha) = learning rate (0 to 1)
- The term in brackets is the **temporal difference (TD) error**

## Exploration vs Exploitation

A fundamental challenge in reinforcement learning is the **exploration-exploitation tradeoff**:

### Exploration
- Try new actions to discover potentially better strategies
- Essential in early learning stages
- May lead to short-term losses

### Exploitation
- Use known good actions to maximize reward
- Important in later learning stages
- May miss better unknown strategies

### Common Strategies

1. **Epsilon-Greedy**
   - With probability ε, choose a random action (explore)
   - With probability 1-ε, choose the best known action (exploit)
   - ε typically decays over time

2. **Boltzmann Exploration (Softmax)**
   - Choose actions with probability proportional to their Q-values
   - Temperature parameter controls exploration level
   - Higher temperature = more exploration

3. **Upper Confidence Bound (UCB)**
   - Considers both estimated value and uncertainty
   - Naturally balances exploration and exploitation

## Hyperparameters

| Parameter | Symbol | Typical Range | Description |
|-----------|--------|---------------|-------------|
| Learning Rate | α | 0.01 - 0.5 | How much to update Q-values |
| Discount Factor | γ | 0.9 - 0.99 | Importance of future rewards |
| Epsilon | ε | 0.1 - 1.0 | Exploration rate |
| Epsilon Decay | - | 0.99 - 0.999 | Rate of epsilon reduction |

## Convergence

Q-Learning is guaranteed to converge to the optimal Q-values under these conditions:
1. All state-action pairs are visited infinitely often
2. The learning rate decays appropriately (Robbins-Monro conditions)

In practice, convergence is often detected when:
- Average reward stabilizes
- Q-values stop changing significantly
- Policy no longer changes

## Related Algorithms

| Algorithm | Type | Key Difference |
|-----------|------|----------------|
| SARSA | On-policy | Uses the actual next action taken |
| Deep Q-Network (DQN) | Value-based | Uses neural network for Q-function |
| Policy Gradient | Policy-based | Directly optimizes the policy |
| Actor-Critic | Hybrid | Combines value and policy methods |

## Applications

Q-Learning and its variants are used in:
- Game playing (Atari, board games)
- Robotics control
- Autonomous vehicles
- Resource management
- Recommendation systems
