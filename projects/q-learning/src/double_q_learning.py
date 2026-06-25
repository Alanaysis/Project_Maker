"""Double Q-Learning implementation.

Double Q-Learning uses two Q-tables to reduce overestimation bias.
Each update randomly selects one table for the max action and the other for evaluation.
"""

from dataclasses import dataclass
from typing import Optional
import numpy as np

try:
    from .grid_world import GridWorld
    from .q_learning import TrainingResult
except ImportError:
    from grid_world import GridWorld
    from q_learning import TrainingResult


class DoubleQLearningAgent:
    """Double Q-Learning Agent.

    Uses two Q-tables (Q_A and Q_B) to reduce overestimation:
    - Randomly choose which table to update
    - Use the other table to evaluate the chosen action

    Update rule (when updating Q_A):
    Q_A(s, a) = Q_A(s, a) + α * [r + γ * Q_B(s', argmax_a' Q_A(s', a')) - Q_A(s, a)]
    """

    def __init__(
        self,
        n_states: int,
        n_actions: int,
        alpha: float = 0.1,
        gamma: float = 0.99,
        epsilon: float = 1.0,
        epsilon_decay: float = 0.995,
        epsilon_min: float = 0.01,
        seed: Optional[int] = None,
    ):
        """Initialize Double Q-Learning agent.

        Args:
            n_states: Number of states.
            n_actions: Number of actions.
            alpha: Learning rate.
            gamma: Discount factor.
            epsilon: Initial exploration rate.
            epsilon_decay: Epsilon decay rate.
            epsilon_min: Minimum epsilon.
            seed: Random seed.
        """
        self.n_states = n_states
        self.n_actions = n_actions
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        self.rng = np.random.RandomState(seed)

        # Two Q-tables
        self.q_table_a = np.zeros((n_states, n_actions))
        self.q_table_b = np.zeros((n_states, n_actions))

    @property
    def q_table(self) -> np.ndarray:
        """Average of both Q-tables for policy extraction."""
        return (self.q_table_a + self.q_table_b) / 2.0

    def choose_action(self, state_idx: int) -> int:
        """Choose action using epsilon-greedy on combined Q-values."""
        if self.rng.random() < self.epsilon:
            return self.rng.randint(self.n_actions)

        # Use average of both tables for action selection
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
        done: bool,
    ) -> float:
        """Update Q-values using Double Q-Learning.

        Randomly selects one table to update, uses the other for evaluation.

        Args:
            state_idx: Current state index.
            action: Action taken.
            reward: Reward received.
            next_state_idx: Next state index.
            done: Whether episode is done.

        Returns:
            TD error.
        """
        if done:
            target_q = reward
            # Update both tables equally when done
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
        """Train agent using Double Q-Learning.

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
            episode_reward = 0.0
            episode_steps = 0

            for step in range(max_steps):
                action = self.choose_action(state_idx)
                next_state, reward, done, info = env.step(action)
                next_state_idx = env.get_state_index(*next_state)

                self.update(state_idx, action, reward, next_state_idx, done)

                episode_reward += reward
                episode_steps += 1
                state_idx = next_state_idx

                if done:
                    break

            self.decay_epsilon()

            result.episode_rewards.append(episode_reward)
            result.episode_steps.append(episode_steps)

            if verbose and (episode + 1) % 100 == 0:
                avg_reward = np.mean(result.episode_rewards[-100:])
                print(f"Episode {episode + 1}/{n_episodes} | Avg Reward: {avg_reward:.1f} | Epsilon: {self.epsilon:.3f}")

        result.total_episodes = len(result.episode_rewards)
        return result

    def get_policy(self, env: GridWorld) -> np.ndarray:
        """Extract learned policy from combined Q-tables."""
        policy = np.zeros((env.rows, env.cols), dtype=np.int32)
        for r in range(env.rows):
            for c in range(env.cols):
                if env.grid[r, c] != 1:
                    state_idx = env.get_state_index(r, c)
                    q_values = self.q_table[state_idx]
                    max_q = np.max(q_values)
                    best_actions = np.where(q_values == max_q)[0]
                    policy[r, c] = self.rng.choice(best_actions)
        return policy

    def get_value_map(self, env: GridWorld) -> np.ndarray:
        """Get maximum Q-values for each state."""
        values = np.zeros((env.rows, env.cols))
        for r in range(env.rows):
            for c in range(env.cols):
                if env.grid[r, c] != 1:
                    state_idx = env.get_state_index(r, c)
                    values[r, c] = np.max(self.q_table[state_idx])
        return values

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
