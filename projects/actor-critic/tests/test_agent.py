"""Tests for the Actor-Critic agent."""

import pytest
import torch
import numpy as np
from actor_critic.agents.actor_critic_agent import ActorCriticAgent


class TestActorCriticAgent:
    """Test suite for ActorCriticAgent."""

    def test_init(self):
        """Test agent initialization."""
        agent = ActorCriticAgent(state_dim=4, action_dim=2)
        assert agent is not None

    def test_select_action(self):
        """Test action selection."""
        agent = ActorCriticAgent(state_dim=4, action_dim=2)
        state = np.array([1.0, 2.0, 3.0, 4.0])
        action = agent.select_action(state)
        assert 0 <= action < 2

    def test_store_reward(self):
        """Test reward storage."""
        agent = ActorCriticAgent(state_dim=4, action_dim=2)
        agent.store_reward(1.0)
        assert len(agent.rewards) == 1
        assert agent.rewards[0] == 1.0

    def test_clear_memory(self):
        """Test memory clearing."""
        agent = ActorCriticAgent(state_dim=4, action_dim=2)
        state = np.array([1.0, 2.0, 3.0, 4.0])
        agent.select_action(state)
        agent.store_reward(1.0)
        agent.clear_memory()
        assert len(agent.states) == 0
        assert len(agent.actions) == 0
        assert len(agent.rewards) == 0

    def test_update(self):
        """Test network update."""
        agent = ActorCriticAgent(state_dim=4, action_dim=2)

        # Simulate an episode
        for _ in range(10):
            state = np.random.randn(4)
            agent.select_action(state)
            agent.store_reward(np.random.randn())

        losses = agent.update()
        assert "actor_loss" in losses
        assert "critic_loss" in losses
        assert "entropy" in losses

    def test_update_empty_episode(self):
        """Test update with empty episode."""
        agent = ActorCriticAgent(state_dim=4, action_dim=2)
        losses = agent.update()
        assert losses["actor_loss"] == 0.0
        assert losses["critic_loss"] == 0.0
        assert losses["entropy"] == 0.0

    def test_multiple_episodes(self):
        """Test training across multiple episodes."""
        agent = ActorCriticAgent(state_dim=4, action_dim=2)

        for episode in range(3):
            for _ in range(10):
                state = np.random.randn(4)
                agent.select_action(state)
                agent.store_reward(np.random.randn())
            agent.update()

    def test_save_load(self, tmp_path):
        """Test model saving and loading."""
        agent = ActorCriticAgent(state_dim=4, action_dim=2)
        save_path = tmp_path / "checkpoint.pt"

        agent.save(str(save_path))
        assert save_path.exists()

        agent2 = ActorCriticAgent(state_dim=4, action_dim=2)
        agent2.load(str(save_path))

        # Verify parameters match
        for p1, p2 in zip(agent.actor.parameters(), agent2.actor.parameters()):
            assert torch.allclose(p1, p2)

    def test_device_selection(self):
        """Test device selection."""
        agent = ActorCriticAgent(state_dim=4, action_dim=2, device="cpu")
        assert agent.device == torch.device("cpu")
