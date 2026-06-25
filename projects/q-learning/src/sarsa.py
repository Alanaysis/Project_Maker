"""Sarsa and Expected Sarsa implementations.

Sarsa (State-Action-Reward-State-Action) is an on-policy TD control algorithm.
Expected Sarsa uses the expected value of next Q-values instead of the maximum.
"""

from dataclasses import dataclass, field
from typing import Optional
import numpy as np

try:
    from .grid_world import GridWorld
    from .q_learning import TrainingResult, ExplorationStrategy
except ImportError:
    from grid_world import GridWorld
    from q_learning import TrainingResult, ExplorationStrategy


@dataclass
class SarsaConfig:
    """Configuration for Sarsa agents."""
    n_states: int
    n_actions: int
    alpha: float = 0.1
    gamma: float = 0.99
    epsilon: float = 1.0
    epsilon_decay: float = 0.995
    epsilon_min: float = 0.01
    temperature: float = 1.0
    seed: Optional[int] = None


class SarsaAgent:
    """Sarsa Agent (on-policy TD control).

    Update rule:
    Q(s, a) = Q(s, a) + α * [r + γ * Q(s', a') - Q(s, a)]

    Where a' is the action actually taken in s' (on-policy).
    """

    def __init__(self, config: SarsaConfig):
        self.config = config
        self.n_states = config.n_states
        self.n_actions = config.n_actions
        self.alpha = config.alpha
        self.gamma = config.gamma
        self.epsilon = config.epsilon
        self.epsilon_decay = config.epsilon_decay
        self.epsilon_min = config.epsilon_min
        self.temperature = config.temperature
        self.rng = np.random.RandomState(config.seed)
        self.q_table = np.zeros((config.n_states, config.n_actions))

    def choose_action(self, state_idx: int) -> int:
        """Choose action using epsilon-greedy policy."""
        if self.rng.random() < self.epsilon:
            return self.rng.randint(self.n_actions)
        return self._get_best_action(state_idx)

    def _get_best_action(self, state_idx: int) -> int:
        """Get action with highest Q-value."""
        q_values = self.q_table[state_idx]
        max_q = np.max(q_values)
        best_actions = np.where(q_values == max_q)[0]
        return self.rng.choice(best_actions)

    def update(
        self,
        state_idx: int,
        action: int,
        reward: float,
        next_state_idx: int,
        next_action: int,
        done: bool,
    ) -> float:
        """Update Q-value using Sarsa update rule.

        Args:
            state_idx: Current state index.
            action: Action taken.
            reward: Reward received.
            next_state_idx: Next state index.
            next_action: Action taken in next state (on-policy).
            done: Whether episode is done.

        Returns:
            TD error.
        """
        current_q = self.q_table[state_idx, action]

        if done:
            target_q = reward
        else:
            target_q = reward + self.gamma * self.q_table[next_state_idx, next_action]

        td_error = target_q - current_q
        self.q_table[state_idx, action] += self.alpha * td_error

        return td_error

    def decay_epsilon(self):
        """Decay exploration rate."""
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    def train(
        self,
        env: GridWorld,
        n_episodes: int = 1000,
        max_steps: int = 200,
        verbose: bool = False,
    ) -> TrainingResult:
        """Train agent using Sarsa algorithm.

        Args:
            env: GridWorld environment.
            n_episodes: Number of training episodes.
            max_steps: Max steps per episode.
            verbose: Print progress.

        Returns:
            TrainingResult with statistics.
        """
        result = TrainingResult()

        for episode in range(n_episodes):
            state = env.reset()
            state_idx = env.get_state_index(*state)
            action = self.choose_action(state_idx)

            episode_reward = 0.0
            episode_steps = 0

            for step in range(max_steps):
                next_state, reward, done, info = env.step(action)
                next_state_idx = env.get_state_index(*next_state)

                if done:
                    self.update(state_idx, action, reward, next_state_idx, 0, done)
                    episode_reward += reward
                    episode_steps += 1
                    break

                next_action = self.choose_action(next_state_idx)
                self.update(state_idx, action, reward, next_state_idx, next_action, done)

                episode_reward += reward
                episode_steps += 1
                state_idx = next_state_idx
                action = next_action

            self.decay_epsilon()

            result.episode_rewards.append(episode_reward)
            result.episode_steps.append(episode_steps)

            if verbose and (episode + 1) % 100 == 0:
                avg_reward = np.mean(result.episode_rewards[-100:])
                print(f"Episode {episode + 1}/{n_episodes} | Avg Reward: {avg_reward:.1f} | Epsilon: {self.epsilon:.3f}")

        result.total_episodes = len(result.episode_rewards)
        return result

    def get_policy(self, env: GridWorld) -> np.ndarray:
        """Extract learned policy."""
        policy = np.zeros((env.rows, env.cols), dtype=np.int32)
        for r in range(env.rows):
            for c in range(env.cols):
                if env.grid[r, c] != 1:
                    state_idx = env.get_state_index(r, c)
                    policy[r, c] = self._get_best_action(state_idx)
        return policy

    def evaluate(self, env: GridWorld, n_episodes: int = 100, max_steps: int = 200) -> dict:
        """Evaluate learned policy."""
        old_epsilon = self.epsilon
        self.epsilon = 0.0

        rewards = []
        steps_list = []
        successes = 0

        for _ in range(n_episodes):
            state = env.reset()
            state_idx = env.get_state_index(*state)
            episode_reward = 0.0

            for step in range(max_steps):
                action = self.choose_action(state_idx)
                next_state, reward, done, info = env.step(action)
                episode_reward += reward
                state_idx = env.get_state_index(*next_state)

                if done:
                    if info.get("reached_goal", False):
                        successes += 1
                    break

            rewards.append(episode_reward)
            steps_list.append(step + 1)

        self.epsilon = old_epsilon

        return {
            "mean_reward": np.mean(rewards),
            "std_reward": np.std(rewards),
            "mean_steps": np.mean(steps_list),
            "success_rate": successes / n_episodes,
        }


class ExpectedSarsaAgent(SarsaAgent):
    """Expected Sarsa Agent (off-policy TD control).

    Update rule:
    Q(s, a) = Q(s, a) + α * [r + γ * Σ π(a'|s') * Q(s', a') - Q(s, a)]

    Uses expected value over all actions weighted by policy probabilities.
    """

    def update(
        self,
        state_idx: int,
        action: int,
        reward: float,
        next_state_idx: int,
        next_action: int,
        done: bool,
    ) -> float:
        """Update Q-value using Expected Sarsa update rule."""
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

    def _get_policy_probs(self, state_idx: int) -> np.ndarray:
        """Get action probabilities under epsilon-greedy policy."""
        probs = np.ones(self.n_actions) * (self.epsilon / self.n_actions)
        best_action = self._get_best_action(state_idx)
        probs[best_action] += (1.0 - self.epsilon)
        return probs
