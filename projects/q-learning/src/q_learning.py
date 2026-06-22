"""Q-Learning Agent implementation.

Q-Learning is a model-free reinforcement learning algorithm that learns the value
of an action in a particular state. It uses the Bellman equation to iteratively
update Q-values until convergence.

Q(s, a) = Q(s, a) + α * [r + γ * max(Q(s', a')) - Q(s, a)]

Where:
    - Q(s, a): Current Q-value for state s and action a
    - α (alpha): Learning rate
    - r: Immediate reward
    - γ (gamma): Discount factor
    - max(Q(s', a')): Maximum Q-value for the next state
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import numpy as np

try:
    from .grid_world import GridWorld
except ImportError:
    from grid_world import GridWorld


class ExplorationStrategy(Enum):
    """Exploration strategies for action selection."""
    EPSILON_GREEDY = "epsilon_greedy"
    BOLTZMANN = "boltzmann"


@dataclass
class TrainingResult:
    """Results from training a Q-Learning agent."""
    episode_rewards: list[float] = field(default_factory=list)
    episode_steps: list[int] = field(default_factory=list)
    q_table_history: list[np.ndarray] = field(default_factory=list)
    total_episodes: int = 0
    convergence_episode: Optional[int] = None


class QLearningAgent:
    """Q-Learning Agent.

    Implements the Q-Learning algorithm with support for:
    - Epsilon-greedy exploration
    - Boltzmann exploration
    - Configurable hyperparameters
    - Training history tracking

    Attributes:
        n_states: Number of states in the environment.
        n_actions: Number of possible actions.
        alpha: Learning rate (0 to 1).
        gamma: Discount factor (0 to 1).
        epsilon: Exploration rate for epsilon-greedy (0 to 1).
        epsilon_decay: Rate at which epsilon decays.
        epsilon_min: Minimum epsilon value.
        strategy: Exploration strategy to use.
        temperature: Temperature parameter for Boltzmann exploration.
        q_table: Q-value table (n_states x n_actions).
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
        strategy: ExplorationStrategy = ExplorationStrategy.EPSILON_GREEDY,
        temperature: float = 1.0,
        seed: Optional[int] = None,
    ):
        """Initialize the Q-Learning agent.

        Args:
            n_states: Number of states.
            n_actions: Number of actions.
            alpha: Learning rate.
            gamma: Discount factor.
            epsilon: Initial exploration rate.
            epsilon_decay: Epsilon decay rate per episode.
            epsilon_min: Minimum epsilon value.
            strategy: Exploration strategy.
            temperature: Temperature for Boltzmann exploration.
            seed: Random seed.
        """
        self.n_states = n_states
        self.n_actions = n_actions
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        self.strategy = strategy
        self.temperature = temperature
        self.rng = np.random.RandomState(seed)

        # Initialize Q-table with zeros
        self.q_table = np.zeros((n_states, n_actions))

        # Training statistics
        self.training_history: list[dict] = []

    def choose_action(self, state: tuple[int, int], env: GridWorld) -> int:
        """Choose an action using the exploration strategy.

        Args:
            state: Current state as (row, col).
            env: The grid world environment.

        Returns:
            The chosen action index.
        """
        state_idx = env.get_state_index(*state)

        if self.strategy == ExplorationStrategy.EPSILON_GREEDY:
            return self._epsilon_greedy(state_idx)
        elif self.strategy == ExplorationStrategy.BOLTZMANN:
            return self._boltzmann(state_idx)
        else:
            raise ValueError(f"Unknown strategy: {self.strategy}")

    def _epsilon_greedy(self, state_idx: int) -> int:
        """Epsilon-greedy action selection.

        With probability epsilon, choose a random action (explore).
        Otherwise, choose the action with the highest Q-value (exploit).

        Args:
            state_idx: Flat state index.

        Returns:
            The chosen action index.
        """
        if self.rng.random() < self.epsilon:
            # Explore: random action
            return self.rng.randint(self.n_actions)
        else:
            # Exploit: best known action
            return self._get_best_action(state_idx)

    def _boltzmann(self, state_idx: int) -> int:
        """Boltzmann (softmax) exploration.

        Actions are chosen with probability proportional to their Q-values,
        scaled by a temperature parameter. Higher temperature = more exploration.

        Args:
            state_idx: Flat state index.

        Returns:
            The chosen action index.
        """
        q_values = self.q_table[state_idx]

        # Prevent overflow by subtracting max
        scaled_q = q_values / self.temperature
        scaled_q -= np.max(scaled_q)

        # Softmax
        exp_q = np.exp(scaled_q)
        probabilities = exp_q / np.sum(exp_q)

        return self.rng.choice(self.n_actions, p=probabilities)

    def _get_best_action(self, state_idx: int) -> int:
        """Get the action with the highest Q-value for a state.

        Args:
            state_idx: Flat state index.

        Returns:
            The best action index.
        """
        q_values = self.q_table[state_idx]
        # Handle ties by choosing randomly among best actions
        max_q = np.max(q_values)
        best_actions = np.where(q_values == max_q)[0]
        return self.rng.choice(best_actions)

    def update(
        self,
        state: tuple[int, int],
        action: int,
        reward: float,
        next_state: tuple[int, int],
        done: bool,
        env: GridWorld,
    ) -> float:
        """Update Q-value using the Q-Learning update rule.

        Q(s, a) = Q(s, a) + α * [r + γ * max(Q(s', a')) - Q(s, a)]

        Args:
            state: Current state.
            action: Action taken.
            reward: Reward received.
            next_state: Next state.
            done: Whether the episode is done.
            env: The grid world environment.

        Returns:
            The TD error (temporal difference error).
        """
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

        # Update Q-value
        self.q_table[state_idx, action] += self.alpha * td_error

        return td_error

    def decay_epsilon(self):
        """Decay the exploration rate.

        Called at the end of each episode to gradually shift from
        exploration to exploitation.
        """
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    def train(
        self,
        env: GridWorld,
        n_episodes: int = 1000,
        max_steps: int = 200,
        convergence_window: int = 100,
        convergence_threshold: float = 0.01,
        save_history: bool = True,
        verbose: bool = False,
    ) -> TrainingResult:
        """Train the agent on the grid world environment.

        Args:
            env: The grid world environment.
            n_episodes: Maximum number of training episodes.
            max_steps: Maximum steps per episode.
            convergence_window: Number of episodes to check for convergence.
            convergence_threshold: Reward change threshold for convergence.
            save_history: Whether to save Q-table snapshots.
            verbose: Whether to print progress.

        Returns:
            TrainingResult with training statistics.
        """
        result = TrainingResult()

        for episode in range(n_episodes):
            state = env.reset()
            episode_reward = 0.0
            episode_steps = 0

            for step in range(max_steps):
                # Choose action
                action = self.choose_action(state, env)

                # Take action
                next_state, reward, done, info = env.step(action)

                # Update Q-value
                self.update(state, action, reward, next_state, done, env)

                # Update tracking
                episode_reward += reward
                episode_steps += 1
                state = next_state

                if done:
                    break

            # Decay exploration rate
            self.decay_epsilon()

            # Record statistics
            result.episode_rewards.append(episode_reward)
            result.episode_steps.append(episode_steps)

            # Save Q-table snapshot periodically
            if save_history and (episode % 100 == 0 or episode == n_episodes - 1):
                result.q_table_history.append(self.q_table.copy())

            # Verbose output
            if verbose and (episode + 1) % 100 == 0:
                avg_reward = np.mean(result.episode_rewards[-100:])
                avg_steps = np.mean(result.episode_steps[-100:])
                print(
                    f"Episode {episode + 1}/{n_episodes} | "
                    f"Avg Reward: {avg_reward:.1f} | "
                    f"Avg Steps: {avg_steps:.1f} | "
                    f"Epsilon: {self.epsilon:.3f}"
                )

            # Check for convergence
            if episode >= convergence_window:
                recent_rewards = result.episode_rewards[-convergence_window:]
                older_rewards = result.episode_rewards[
                    -2 * convergence_window : -convergence_window
                ]
                if len(older_rewards) >= convergence_window:
                    recent_avg = np.mean(recent_rewards)
                    older_avg = np.mean(older_rewards)
                    if abs(recent_avg - older_avg) < convergence_threshold:
                        result.convergence_episode = episode
                        if verbose:
                            print(f"Converged at episode {episode + 1}")
                        break

        result.total_episodes = len(result.episode_rewards)
        return result

    def get_policy(self, env: GridWorld) -> np.ndarray:
        """Extract the learned policy.

        Args:
            env: The grid world environment.

        Returns:
            2D array of best actions for each state.
        """
        policy = np.zeros((env.rows, env.cols), dtype=np.int32)
        for r in range(env.rows):
            for c in range(env.cols):
                if env.grid[r, c] != 1:  # Not a wall
                    state_idx = env.get_state_index(r, c)
                    policy[r, c] = self._get_best_action(state_idx)
        return policy

    def get_value_map(self, env: GridWorld) -> np.ndarray:
        """Get the maximum Q-value for each state (state values).

        Args:
            env: The grid world environment.

        Returns:
            2D array of maximum Q-values.
        """
        values = np.zeros((env.rows, env.cols))
        for r in range(env.rows):
            for c in range(env.cols):
                if env.grid[r, c] != 1:
                    state_idx = env.get_state_index(r, c)
                    values[r, c] = np.max(self.q_table[state_idx])
        return values

    def evaluate(
        self, env: GridWorld, n_episodes: int = 100, max_steps: int = 200
    ) -> dict:
        """Evaluate the learned policy without exploration.

        Args:
            env: The grid world environment.
            n_episodes: Number of evaluation episodes.
            max_steps: Maximum steps per episode.

        Returns:
            Dictionary with evaluation metrics.
        """
        old_epsilon = self.epsilon
        self.epsilon = 0.0  # No exploration during evaluation

        rewards = []
        steps_list = []
        successes = 0

        for _ in range(n_episodes):
            state = env.reset()
            episode_reward = 0.0

            for step in range(max_steps):
                action = self.choose_action(state, env)
                next_state, reward, done, info = env.step(action)
                episode_reward += reward
                state = next_state

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
            "min_reward": np.min(rewards),
            "max_reward": np.max(rewards),
        }
