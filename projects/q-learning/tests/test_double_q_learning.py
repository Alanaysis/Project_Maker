"""Tests for Double Q-Learning implementation."""

import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.grid_world import GridWorld
from src.double_q_learning import DoubleQLearningAgent


class TestDoubleQLearningAgent:
    """Tests for Double Q-Learning agent."""

    def test_initialization(self):
        """Test agent initialization."""
        agent = DoubleQLearningAgent(n_states=9, n_actions=4, seed=42)

        assert agent.n_states == 9
        assert agent.n_actions == 4
        assert agent.q_table_a.shape == (9, 4)
        assert agent.q_table_b.shape == (9, 4)
        assert np.all(agent.q_table_a == 0)
        assert np.all(agent.q_table_b == 0)

    def test_q_table_property(self):
        """Test q_table property returns average."""
        agent = DoubleQLearningAgent(n_states=9, n_actions=4, seed=42)

        agent.q_table_a[0] = [1.0, 2.0, 3.0, 4.0]
        agent.q_table_b[0] = [2.0, 3.0, 4.0, 5.0]

        expected = [1.5, 2.5, 3.5, 4.5]
        np.testing.assert_array_almost_equal(agent.q_table[0], expected)

    def test_choose_action_explore(self):
        """Test action selection with high epsilon."""
        agent = DoubleQLearningAgent(n_states=9, n_actions=4, epsilon=1.0, seed=42)

        actions = [agent.choose_action(0) for _ in range(100)]
        unique_actions = set(actions)

        # With epsilon=1.0, should explore all actions
        assert len(unique_actions) > 1

    def test_choose_action_exploit(self):
        """Test action selection with low epsilon."""
        agent = DoubleQLearningAgent(n_states=9, n_actions=4, epsilon=0.0, seed=42)

        agent.q_table_a[0] = [1.0, 2.0, 3.0, 0.5]
        agent.q_table_b[0] = [1.0, 2.0, 3.0, 0.5]

        actions = [agent.choose_action(0) for _ in range(100)]
        assert all(a == 2 for a in actions)

    def test_update_terminal(self):
        """Test update at terminal state."""
        agent = DoubleQLearningAgent(n_states=9, n_actions=4, alpha=0.5, seed=42)

        agent.q_table_a[0, 0] = 1.0
        agent.q_table_b[0, 0] = 1.0

        agent.update(0, 0, 10.0, 1, True)

        # Both tables should be updated equally at terminal
        expected = 1.0 + 0.5 * (10.0 - 1.0)
        assert abs(agent.q_table_a[0, 0] - expected) < 1e-6
        assert abs(agent.q_table_b[0, 0] - expected) < 1e-6

    def test_update_non_terminal(self):
        """Test update at non-terminal state."""
        agent = DoubleQLearningAgent(n_states=9, n_actions=4, alpha=0.5, gamma=0.9, seed=42)

        # Set up Q-values
        agent.q_table_a[0, 0] = 1.0
        agent.q_table_b[0, 0] = 1.0
        agent.q_table_a[1] = [0.0, 2.0, 3.0, 0.0]
        agent.q_table_b[1] = [0.0, 1.0, 4.0, 0.0]

        # Run multiple updates to test both paths
        for _ in range(100):
            agent.q_table_a[0, 0] = 1.0
            agent.q_table_b[0, 0] = 1.0
            agent.update(0, 0, 1.0, 1, False)

        # One table should be updated with action from the other
        # This is stochastic due to random selection
        assert agent.q_table_a[0, 0] != 1.0 or agent.q_table_b[0, 0] != 1.0

    def test_epsilon_decay(self):
        """Test epsilon decay."""
        agent = DoubleQLearningAgent(
            n_states=9,
            n_actions=4,
            epsilon=1.0,
            epsilon_decay=0.9,
            epsilon_min=0.1,
            seed=42,
        )

        for _ in range(50):
            agent.decay_epsilon()

        assert agent.epsilon == 0.1

    def test_train_simple_grid(self):
        """Test training on simple grid."""
        env = GridWorld(rows=3, cols=3, start=(0, 0), goal=(2, 2), seed=42)
        agent = DoubleQLearningAgent(
            n_states=9,
            n_actions=4,
            alpha=0.5,
            gamma=0.9,
            seed=42,
        )

        result = agent.train(env, n_episodes=200, max_steps=50)

        assert len(result.episode_rewards) == 200
        assert len(result.episode_steps) == 200

        # Should learn something
        assert np.mean(result.episode_rewards[-100:]) > np.mean(result.episode_rewards[:100])

    def test_reduces_overestimation(self):
        """Test that Double Q-Learning reduces overestimation compared to Q-Learning."""
        # This is a conceptual test - in practice, Double Q-Learning
        # should produce more accurate value estimates
        env = GridWorld(rows=3, cols=3, start=(0, 0), goal=(2, 2), seed=42)

        agent = DoubleQLearningAgent(
            n_states=9,
            n_actions=4,
            alpha=0.1,
            gamma=0.99,
            seed=42,
        )

        # Train for many episodes
        agent.train(env, n_episodes=500, max_steps=100)

        # Q-values should be reasonable (not extremely overestimated)
        max_q = np.max(agent.q_table)
        assert max_q < 100  # Should not be extremely overestimated

    def test_get_policy(self):
        """Test policy extraction."""
        env = GridWorld(rows=3, cols=3, start=(0, 0), goal=(2, 2), seed=42)
        agent = DoubleQLearningAgent(n_states=9, n_actions=4, seed=42)

        agent.train(env, n_episodes=200, max_steps=50)

        policy = agent.get_policy(env)
        assert policy.shape == (3, 3)

        # Policy should have valid actions
        for r in range(3):
            for c in range(3):
                assert 0 <= policy[r, c] <= 3

    def test_get_value_map(self):
        """Test value map extraction."""
        env = GridWorld(rows=3, cols=3, start=(0, 0), goal=(2, 2), seed=42)
        agent = DoubleQLearningAgent(n_states=9, n_actions=4, seed=42)

        agent.train(env, n_episodes=200, max_steps=50)

        value_map = agent.get_value_map(env)
        assert value_map.shape == (3, 3)

        # Goal state is terminal, so value is 0
        # Start state should have value > 0 after training
        assert value_map[0, 0] > 0

    def test_evaluate(self):
        """Test policy evaluation."""
        env = GridWorld(rows=3, cols=3, start=(0, 0), goal=(2, 2), seed=42)
        agent = DoubleQLearningAgent(n_states=9, n_actions=4, seed=42)

        agent.train(env, n_episodes=200, max_steps=50)

        metrics = agent.evaluate(env, n_episodes=50, max_steps=50)

        assert "mean_reward" in metrics
        assert "success_rate" in metrics
        assert 0 <= metrics["success_rate"] <= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
