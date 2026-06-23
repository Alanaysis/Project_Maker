"""Tests for the Actor network."""

import pytest
import torch
from actor_critic.networks.actor_network import ActorNetwork


class TestActorNetwork:
    """Test suite for ActorNetwork."""

    def test_init(self):
        """Test network initialization."""
        network = ActorNetwork(state_dim=4, action_dim=2)
        assert network is not None

    def test_forward_shape(self):
        """Test forward pass output shape."""
        network = ActorNetwork(state_dim=4, action_dim=2)
        state = torch.randn(1, 4)
        output = network(state)
        assert output.shape == (1, 2)

    def test_batch_forward_shape(self):
        """Test forward pass with batch of states."""
        network = ActorNetwork(state_dim=4, action_dim=2)
        states = torch.randn(32, 4)
        output = network(states)
        assert output.shape == (32, 2)

    def test_get_action_probs(self):
        """Test action probabilities sum to 1."""
        network = ActorNetwork(state_dim=4, action_dim=2)
        state = torch.randn(1, 4)
        probs = network.get_action_probs(state)
        assert torch.allclose(probs.sum(dim=-1), torch.ones(1), atol=1e-6)

    def test_get_action(self):
        """Test action selection."""
        network = ActorNetwork(state_dim=4, action_dim=2)
        state = torch.randn(4)
        action, log_prob = network.get_action(state)
        assert 0 <= action < 2
        assert log_prob.dim() == 0

    def test_evaluate_actions(self):
        """Test action evaluation."""
        network = ActorNetwork(state_dim=4, action_dim=2)
        states = torch.randn(32, 4)
        actions = torch.randint(0, 2, (32,))
        log_probs, entropy = network.evaluate_actions(states, actions)
        assert log_probs.shape == (32,)
        assert entropy.shape == (32,)

    def test_different_hidden_dims(self):
        """Test network with different hidden dimensions."""
        for hidden_dim in [64, 128, 256]:
            network = ActorNetwork(state_dim=4, action_dim=2, hidden_dim=hidden_dim)
            state = torch.randn(1, 4)
            output = network(state)
            assert output.shape == (1, 2)
