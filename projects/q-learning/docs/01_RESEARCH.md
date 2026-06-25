# Research: Q-Learning and Reinforcement Learning

## Background

Reinforcement Learning (RL) is a type of machine learning where an agent learns to make decisions by taking actions in an environment to maximize cumulative reward.

## Key Concepts

### Markov Decision Process (MDP)

An MDP is defined by:
- **States (S)**: All possible situations the agent can be in
- **Actions (A)**: All possible moves the agent can make
- **Transition Function (P)**: Probability of moving from state s to s' given action a
- **Reward Function (R)**: Expected reward for taking action a in state s
- **Discount Factor (γ)**: How much to value future rewards (0 to 1)

### Value Functions

**State Value Function V(s)**:
```
V(s) = E[Σ γ^t * r_t | s_0 = s]
```

**Action Value Function Q(s, a)**:
```
Q(s, a) = E[Σ γ^t * r_t | s_0 = s, a_0 = a]
```

### Bellman Equations

**For V(s)**:
```
V(s) = Σ_a π(a|s) * Σ_s' P(s'|s,a) * [R(s,a,s') + γ * V(s')]
```

**For Q(s, a)**:
```
Q(s, a) = Σ_s' P(s'|s,a) * [R(s,a,s') + γ * Σ_a' π(a'|s') * Q(s', a')]
```

## Temporal Difference (TD) Learning

TD methods learn directly from experience without needing a model of the environment.

### TD Prediction (Policy Evaluation)

```
V(s) = V(s) + α * [r + γ * V(s') - V(s)]
```

### TD Control

**Q-Learning (Off-Policy)**:
```
Q(s, a) = Q(s, a) + α * [r + γ * max_a' Q(s', a') - Q(s, a)]
```

**Sarsa (On-Policy)**:
```
Q(s, a) = Q(s, a) + α * [r + γ * Q(s', a') - Q(s, a)]
```

**Expected Sarsa**:
```
Q(s, a) = Q(s, a) + α * [r + γ * Σ_a' π(a'|s') * Q(s', a') - Q(s, a)]
```

## Exploration Strategies

### Epsilon-Greedy

- With probability ε, choose random action (explore)
- With probability 1-ε, choose best action (exploit)
- ε typically decays over time

### Boltzmann Exploration (Softmax)

Actions chosen with probability proportional to their Q-values:
```
P(a|s) = exp(Q(s,a)/τ) / Σ_a' exp(Q(s,a')/τ)
```

Where τ is temperature parameter.

### Upper Confidence Bound (UCB)

```
a_t = argmax_a [Q(s,a) + c * sqrt(ln(t) / N(s,a))]
```

## Overestimation Bias

### Problem

Q-Learning uses max operator, which can overestimate Q-values due to:
1. Noise in estimates
2. Stochastic environments
3. Function approximation errors

### Solution: Double Q-Learning

Uses two Q-tables:
1. Randomly select which table to update
2. Use the other table for evaluation

```
Q_A(s, a) = Q_A(s, a) + α * [r + γ * Q_B(s', argmax_a' Q_A(s', a')) - Q_A(s, a)]
```

## On-Policy vs Off-Policy

### On-Policy (Sarsa)

- Learns about the policy being followed
- More conservative
- Better for risky environments

### Off-Policy (Q-Learning)

- Can learn optimal policy while exploring
- More sample efficient
- Can use experience from any policy

## Convergence

### Conditions for Convergence

1. **Learning rate**: Σ α = ∞, Σ α² < ∞
2. **Exploration**: Every state-action pair visited infinitely often
3. **Tabular representation**: Finite state and action spaces

### Practical Considerations

- Use decaying learning rate
- Ensure sufficient exploration
- Monitor training progress

## Applications

### Game Playing

- Board games (Chess, Go)
- Video games (Atari, Mario)
- Card games (Poker)

### Robotics

- Robot navigation
- Manipulation tasks
- Autonomous driving

### Resource Management

- Network routing
- Job scheduling
- Inventory management

## References

1. Sutton, R. S., & Barto, A. G. (2018). Reinforcement Learning: An Introduction.
2. Watkins, C. J. C. H., & Dayan, P. (1992). Q-learning. Machine Learning.
3. Van Hasselt, H. (2010). Double Q-learning. Advances in Neural Information Processing Systems.
4. Van Seijen, H., et al. (2009). True online TD(lambda). International Conference on Machine Learning.
