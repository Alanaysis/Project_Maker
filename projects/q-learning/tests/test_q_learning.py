"""Tests for the Q-Learning Agent."""

import pytest
import numpy as np

from src.grid_world import GridWorld, Action
from src.q_learning import QLearningAgent, ExplorationStrategy, TrainingResult


class TestQLearningAgent:
    """Tests for the QLearningAgent class."""

    def test_initialization(self):
        agent = QLearningAgent(n_states=25, n_actions=4)
        assert agent.n_states == 25
        assert agent.n_actions == 4
        assert agent.q_table.shape == (25, 4)
        assert np.all(agent.q_table == 0)

    def test_custom_hyperparameters(self):
        agent = QLearningAgent(
            n_states=25,
            n_actions=4,
            alpha=0.2,
            gamma=0.9,
            epsilon=0.5,
        )
        assert agent.alpha == 0.2
        assert agent.gamma == 0.9
        assert agent.epsilon == 0.5

    def test_choose_action_epsilon_greedy_explore(self):
        agent = QLearningAgent(
            n_states=25,
            n_actions=4,
            epsilon=1.0,  # Always explore
            seed=42,
        )
        env = GridWorld(rows=5, cols=5)
        state = (0, 0)

        # With epsilon=1.0, should always explore (random)
        actions = set()
        for _ in range(100):
            action = agent.choose_action(state, env)
            actions.add(action)
        # Should have multiple different actions
        assert len(actions) > 1

    def test_choose_action_epsilon_greedy_exploit(self):
        agent = QLearningAgent(
            n_states=25,
            n_actions=4,
            epsilon=0.0,  # Always exploit
            seed=42,
        )
        env = GridWorld(rows=5, cols=5)
        state = (0, 0)
        state_idx = env.get_state_index(*state)

        # Set Q-values so action 1 is best
        agent.q_table[state_idx] = [0.1, 0.9, 0.2, 0.3]

        # Should always choose action 1
        for _ in range(100):
            action = agent.choose_action(state, env)
            assert action == 1

    def test_choose_action_boltzmann(self):
        agent = QLearningAgent(
            n_states=25,
            n_actions=4,
            strategy=ExplorationStrategy.BOLTZMANN,
            temperature=1.0,
            seed=42,
        )
        env = GridWorld(rows=5, cols=5)
        state = (0, 0)
        state_idx = env.get_state_index(*state)

        # Set Q-values
        agent.q_table[state_idx] = [0.1, 0.9, 0.2, 0.3]

        # Should choose actions with some randomness
        actions = set()
        for _ in range(100):
            action = agent.choose_action(state, env)
            actions.add(action)
        assert len(actions) > 1

    def test_update_q_value(self):
        agent = QLearningAgent(
            n_states=25,
            n_actions=4,
            alpha=0.1,
            gamma=0.9,
        )
        env = GridWorld(rows=5, cols=5)
        state = (0, 0)
        next_state = (0, 1)
        action = Action.RIGHT

        # Initial Q-value is 0
        state_idx = env.get_state_index(*state)
        assert agent.q_table[state_idx, action] == 0.0

        # Update with reward 10, not done
        td_error = agent.update(state, action, 10.0, next_state, False, env)

        # Q-value should be updated
        # Q(s,a) = 0 + 0.1 * [10 + 0.9 * max(Q(s',*)) - 0]
        # Since all Q(s',*) are 0: Q(s,a) = 0.1 * 10 = 1.0
        assert agent.q_table[state_idx, action] == pytest.approx(1.0)
        assert td_error == pytest.approx(10.0)

    def test_update_terminal_state(self):
        agent = QLearningAgent(
            n_states=25,
            n_actions=4,
            alpha=0.1,
            gamma=0.9,
        )
        env = GridWorld(rows=5, cols=5)
        state = (0, 0)
        next_state = (0, 1)
        action = Action.RIGHT

        # Update with reward 100, done=True
        state_idx = env.get_state_index(*state)
        agent.update(state, action, 100.0, next_state, True, env)

        # Q(s,a) = 0 + 0.1 * [100 - 0] = 10.0
        assert agent.q_table[state_idx, action] == pytest.approx(10.0)

    def test_update_with_existing_q_values(self):
        agent = QLearningAgent(
            n_states=25,
            n_actions=4,
            alpha=0.5,  # Large alpha for clear effect
            gamma=0.9,
        )
        env = GridWorld(rows=5, cols=5)
        state = (0, 0)
        next_state = (0, 1)
        action = Action.RIGHT

        # Set existing Q-values
        state_idx = env.get_state_index(*state)
        next_state_idx = env.get_state_index(*next_state)
        agent.q_table[state_idx, action] = 5.0
        agent.q_table[next_state_idx, :] = [10.0, 20.0, 30.0, 40.0]

        # Update
        agent.update(state, action, 1.0, next_state, False, env)

        # Q(s,a) = 5.0 + 0.5 * [1 + 0.9 * 40.0 - 5.0]
        #        = 5.0 + 0.5 * [1 + 36 - 5]
        #        = 5.0 + 0.5 * 32
        #        = 5.0 + 16.0 = 21.0
        expected = 5.0 + 0.5 * (1.0 + 0.9 * 40.0 - 5.0)
        assert agent.q_table[state_idx, action] == pytest.approx(expected)

    def test_decay_epsilon(self):
        agent = QLearningAgent(
            n_states=25,
            n_actions=4,
            epsilon=1.0,
            epsilon_decay=0.9,
            epsilon_min=0.1,
        )

        # Decay multiple times
        for _ in range(5):
            agent.decay_epsilon()

        # Should be decaying but not below min
        assert agent.epsilon < 1.0
        assert agent.epsilon >= 0.1

    def test_epsilon_min_bound(self):
        agent = QLearningAgent(
            n_states=25,
            n_actions=4,
            epsilon=0.05,
            epsilon_decay=0.9,
            epsilon_min=0.1,  # min > initial
        )
        agent.decay_epsilon()
        assert agent.epsilon == 0.1

    def test_get_policy(self):
        agent = QLearningAgent(n_states=25, n_actions=4)
        env = GridWorld(rows=5, cols=5)

        # Set Q-values for state (0, 0)
        state_idx = env.get_state_index(0, 0)
        agent.q_table[state_idx] = [0.1, 0.9, 0.2, 0.3]

        policy = agent.get_policy(env)
        assert policy[0, 0] == 1  # Action RIGHT (index 1) has highest Q-value

    def test_get_value_map(self):
        agent = QLearningAgent(n_states=25, n_actions=4)
        env = GridWorld(rows=5, cols=5)

        # Set Q-values for state (0, 0)
        state_idx = env.get_state_index(0, 0)
        agent.q_table[state_idx] = [0.1, 0.9, 0.2, 0.3]

        value_map = agent.get_value_map(env)
        assert value_map[0, 0] == pytest.approx(0.9)

    def test_train_simple_grid(self):
        """Test training on a simple grid where goal is adjacent to start."""
        env = GridWorld(
            rows=3,
            cols=3,
            start=(0, 0),
            goal=(0, 1),
        )
        agent = QLearningAgent(
            n_states=9,
            n_actions=4,
            alpha=0.5,
            gamma=0.9,
            epsilon=0.3,
            seed=42,
        )

        result = agent.train(env, n_episodes=100, max_steps=10)

        assert isinstance(result, TrainingResult)
        assert result.total_episodes > 0
        assert len(result.episode_rewards) > 0
        assert len(result.episode_steps) > 0

    def test_train_updates_q_table(self):
        """Test that training actually updates Q-values."""
        env = GridWorld(
            rows=3,
            cols=3,
            start=(0, 0),
            goal=(0, 1),
        )
        agent = QLearningAgent(
            n_states=9,
            n_actions=4,
            alpha=0.5,
            gamma=0.9,
            epsilon=0.3,
            seed=42,
        )

        # Q-table should start at zeros
        assert np.all(agent.q_table == 0)

        # Train
        agent.train(env, n_episodes=50, max_steps=10)

        # Q-table should have non-zero values
        assert not np.all(agent.q_table == 0)

    def test_evaluate(self):
        """Test policy evaluation."""
        env = GridWorld(
            rows=3,
            cols=3,
            start=(0, 0),
            goal=(0, 1),
        )
        agent = QLearningAgent(
            n_states=9,
            n_actions=4,
            alpha=0.5,
            gamma=0.9,
            epsilon=0.3,
            seed=42,
        )

        # Train first
        agent.train(env, n_episodes=200, max_steps=10)

        # Evaluate
        metrics = agent.evaluate(env, n_episodes=50, max_steps=10)

        assert "mean_reward" in metrics
        assert "success_rate" in metrics
        assert "mean_steps" in metrics
        assert 0 <= metrics["success_rate"] <= 1

    def test_evaluate_no_exploration(self):
        """Test that evaluation uses no exploration."""
        agent = QLearningAgent(
            n_states=25,
            n_actions=4,
            epsilon=0.5,
        )

        # Store original epsilon
        original_epsilon = agent.epsilon

        # Evaluate should not change epsilon
        env = GridWorld(rows=5, cols=5)
        agent.evaluate(env, n_episodes=5)
        assert agent.epsilon == original_epsilon


class TestTrainingResult:
    """Tests for the TrainingResult class."""

    def test_default_values(self):
        result = TrainingResult()
        assert result.episode_rewards == []
        assert result.episode_steps == []
        assert result.q_table_history == []
        assert result.total_episodes == 0
        assert result.convergence_episode is None


class TestExplorationStrategy:
    """Tests for ExplorationStrategy enum."""

    def test_strategies_exist(self):
        assert ExplorationStrategy.EPSILON_GREEDY.value == "epsilon_greedy"
        assert ExplorationStrategy.BOLTZMANN.value == "boltzmann"
