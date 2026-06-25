"""Tests for Sarsa and Expected Sarsa implementations."""

import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.grid_world import GridWorld
from src.sarsa import SarsaAgent, ExpectedSarsaAgent, SarsaConfig


class TestSarsaAgent:
    """Tests for Sarsa agent."""

    def test_initialization(self):
        """Test agent initialization."""
        config = SarsaConfig(n_states=9, n_actions=4, seed=42)
        agent = SarsaAgent(config)

        assert agent.n_states == 9
        assert agent.n_actions == 4
        assert agent.q_table.shape == (9, 4)
        assert np.all(agent.q_table == 0)

    def test_choose_action_explore(self):
        """Test action selection with high epsilon (exploration)."""
        config = SarsaConfig(n_states=9, n_actions=4, epsilon=1.0, seed=42)
        agent = SarsaAgent(config)

        actions = [agent.choose_action(0) for _ in range(100)]
        unique_actions = set(actions)

        # With epsilon=1.0, should explore all actions
        assert len(unique_actions) > 1

    def test_choose_action_exploit(self):
        """Test action selection with low epsilon (exploitation)."""
        config = SarsaConfig(n_states=9, n_actions=4, epsilon=0.0, seed=42)
        agent = SarsaAgent(config)

        # Set Q-values for state 0
        agent.q_table[0] = [1.0, 2.0, 3.0, 0.5]

        actions = [agent.choose_action(0) for _ in range(100)]
        assert all(a == 2 for a in actions)  # Should always choose action 2

    def test_update(self):
        """Test Q-value update."""
        config = SarsaConfig(n_states=9, n_actions=4, alpha=0.5, gamma=0.9, seed=42)
        agent = SarsaAgent(config)

        # Set initial Q-value
        agent.q_table[0, 0] = 1.0
        agent.q_table[1, 1] = 2.0

        # Update: state=0, action=0, reward=1.0, next_state=1, next_action=1
        td_error = agent.update(0, 0, 1.0, 1, 1, False)

        # Expected: Q(0,0) = 1.0 + 0.5 * (1.0 + 0.9 * 2.0 - 1.0) = 1.0 + 0.5 * 1.8 = 1.9
        assert abs(agent.q_table[0, 0] - 1.9) < 1e-6
        assert abs(td_error - 1.8) < 1e-6

    def test_update_terminal(self):
        """Test Q-value update at terminal state."""
        config = SarsaConfig(n_states=9, n_actions=4, alpha=0.5, gamma=0.9, seed=42)
        agent = SarsaAgent(config)

        agent.q_table[0, 0] = 1.0

        # Terminal state: reward only, no future value
        td_error = agent.update(0, 0, 10.0, 1, 0, True)

        # Expected: Q(0,0) = 1.0 + 0.5 * (10.0 - 1.0) = 5.5
        assert abs(agent.q_table[0, 0] - 5.5) < 1e-6

    def test_epsilon_decay(self):
        """Test epsilon decay."""
        config = SarsaConfig(
            n_states=9,
            n_actions=4,
            epsilon=1.0,
            epsilon_decay=0.9,
            epsilon_min=0.1,
            seed=42,
        )
        agent = SarsaAgent(config)

        for _ in range(50):
            agent.decay_epsilon()

        assert agent.epsilon == 0.1  # Should be at minimum

    def test_train_simple_grid(self):
        """Test training on a simple grid."""
        env = GridWorld(rows=3, cols=3, start=(0, 0), goal=(2, 2), seed=42)
        config = SarsaConfig(n_states=9, n_actions=4, alpha=0.5, gamma=0.9, seed=42)
        agent = SarsaAgent(config)

        result = agent.train(env, n_episodes=100, max_steps=50)

        assert len(result.episode_rewards) == 100
        assert len(result.episode_steps) == 100

        # Should learn something
        assert np.mean(result.episode_rewards[-50:]) > np.mean(result.episode_rewards[:50])

    def test_get_policy(self):
        """Test policy extraction."""
        env = GridWorld(rows=3, cols=3, start=(0, 0), goal=(2, 2), seed=42)
        config = SarsaConfig(n_states=9, n_actions=4, seed=42)
        agent = SarsaAgent(config)

        # Train agent
        agent.train(env, n_episodes=200, max_steps=50)

        policy = agent.get_policy(env)
        assert policy.shape == (3, 3)

        # Policy should have valid actions (0-3)
        for r in range(3):
            for c in range(3):
                assert 0 <= policy[r, c] <= 3


class TestExpectedSarsaAgent:
    """Tests for Expected Sarsa agent."""

    def test_initialization(self):
        """Test agent initialization."""
        config = SarsaConfig(n_states=9, n_actions=4, seed=42)
        agent = ExpectedSarsaAgent(config)

        assert agent.n_states == 9
        assert agent.n_actions == 4

    def test_get_policy_probs(self):
        """Test policy probability calculation."""
        config = SarsaConfig(n_states=9, n_actions=4, epsilon=0.1, seed=42)
        agent = ExpectedSarsaAgent(config)

        agent.q_table[0] = [1.0, 2.0, 3.0, 0.5]

        probs = agent._get_policy_probs(0)
        assert len(probs) == 4
        assert abs(np.sum(probs) - 1.0) < 1e-6
        # Action 2 has highest Q-value, should have highest probability
        assert probs[2] > probs[0]
        assert probs[2] > probs[1]
        assert probs[2] > probs[3]

    def test_update(self):
        """Test Expected Sarsa update."""
        config = SarsaConfig(n_states=9, n_actions=4, alpha=0.5, gamma=0.9, epsilon=0.1, seed=42)
        agent = ExpectedSarsaAgent(config)

        agent.q_table[0, 0] = 1.0
        agent.q_table[1] = [1.0, 2.0, 3.0, 0.5]

        td_error = agent.update(0, 0, 1.0, 1, 0, False)

        # Should use expected value, not max
        assert td_error != 0
        assert agent.q_table[0, 0] != 1.0

    def test_train(self):
        """Test training with Expected Sarsa."""
        env = GridWorld(rows=3, cols=3, start=(0, 0), goal=(2, 2), seed=42)
        config = SarsaConfig(n_states=9, n_actions=4, alpha=0.5, gamma=0.9, seed=42)
        agent = ExpectedSarsaAgent(config)

        result = agent.train(env, n_episodes=100, max_steps=50)

        assert len(result.episode_rewards) == 100

        # Should learn something
        assert np.mean(result.episode_rewards[-50:]) > np.mean(result.episode_rewards[:50])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
