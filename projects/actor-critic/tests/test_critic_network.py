"""Tests for the Critic network."""

import pytest
import torch
from actor_critic.networks.critic_network import CriticNetwork


class TestCriticNetwork:
    """Test suite for CriticNetwork."""

    def test_init(self):
        """Test network initialization."""
        network = CriticNetwork(state_dim=4)
        assert network is not None

    def test_forward_shape(self):
        """Test forward pass output shape."""
        network = CriticNetwork(state_dim=4)
        state = torch.randn(1, 4)
        output = network(state)
        assert output.shape == (1, 1)

    def test_batch_forward_shape(self):
        """Test forward pass with batch of states."""
        network = CriticNetwork(state_dim=4)
        states = torch.randn(32, 4)
        output = network(states)
        assert output.shape == (32, 1)

    def test_get_value_single(self):
        """Test value estimation for single state."""
        network = CriticNetwork(state_dim=4)
        state = torch.randn(4)
        value = network.get_value(state)
        assert value.dim() == 0

    def test_get_value_batch(self):
        """Test value estimation for batch of states."""
        network = CriticNetwork(state_dim=4)
        states = torch.randn(32, 4)
        values = network.get_value(states)
        assert values.shape == (32,)

    def test_different_hidden_dims(self):
        """Test network with different hidden dimensions."""
        for hidden_dim in [64, 128, 256]:
            network = CriticNetwork(state_dim=4, hidden_dim=hidden_dim)
            state = torch.randn(1, 4)
            output = network(state)
            assert output.shape == (1, 1)
