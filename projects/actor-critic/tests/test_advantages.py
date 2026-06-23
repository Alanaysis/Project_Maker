"""Tests for advantage computation utilities."""

import pytest
import torch
import numpy as np
from actor_critic.utils.advantages import (
    compute_returns,
    compute_advantages,
    normalize_advantages,
)


class TestComputeReturns:
    """Test suite for compute_returns function."""

    def test_single_reward(self):
        """Test return computation with single reward."""
        returns = compute_returns([1.0], gamma=0.99)
        assert len(returns) == 1
        assert returns[0] == pytest.approx(1.0)

    def test_multiple_rewards(self):
        """Test return computation with multiple rewards."""
        rewards = [1.0, 1.0, 1.0]
        returns = compute_returns(rewards, gamma=0.99)
        assert len(returns) == 3
        # G_0 = 1 + 0.99 * 1 + 0.99^2 * 1
        assert returns[0] == pytest.approx(1.0 + 0.99 + 0.99**2)
        # G_1 = 1 + 0.99 * 1
        assert returns[1] == pytest.approx(1.0 + 0.99)
        # G_2 = 1
        assert returns[2] == pytest.approx(1.0)

    def test_gamma_zero(self):
        """Test return computation with gamma=0."""
        rewards = [1.0, 2.0, 3.0]
        returns = compute_returns(rewards, gamma=0.0)
        assert returns == [1.0, 2.0, 3.0]

    def test_gamma_one(self):
        """Test return computation with gamma=1."""
        rewards = [1.0, 1.0, 1.0]
        returns = compute_returns(rewards, gamma=1.0)
        assert returns == [3.0, 2.0, 1.0]


class TestComputeAdvantages:
    """Test suite for compute_advantages function."""

    def test_simple_advantage(self):
        """Test simple advantage computation (GAE lambda=1)."""
        rewards = [1.0, 1.0, 1.0]
        values = [0.5, 0.5, 0.5]
        advantages = compute_advantages(rewards, values, gamma=0.99, gae_lambda=1.0)
        assert len(advantages) == 3

    def test_gae_advantage(self):
        """Test GAE advantage computation."""
        rewards = [1.0, 1.0, 1.0]
        values = [0.5, 0.5, 0.5]
        advantages = compute_advantages(rewards, values, gamma=0.99, gae_lambda=0.95)
        assert len(advantages) == 3

    def test_zero_advantage(self):
        """Test advantage when values equal returns."""
        rewards = [1.0, 1.0]
        # For gamma=1, returns are [2.0, 1.0]
        values = [2.0, 1.0]
        advantages = compute_advantages(rewards, values, gamma=1.0, gae_lambda=1.0)
        assert advantages[0] == pytest.approx(0.0, abs=1e-6)
        assert advantages[1] == pytest.approx(0.0, abs=1e-6)


class TestNormalizeAdvantages:
    """Test suite for normalize_advantages function."""

    def test_normalize(self):
        """Test advantage normalization."""
        advantages = [1.0, 2.0, 3.0, 4.0, 5.0]
        normalized = normalize_advantages(advantages)
        normalized_array = np.array(normalized)
        assert normalized_array.mean() == pytest.approx(0.0, abs=1e-6)
        assert normalized_array.std() == pytest.approx(1.0, abs=1e-6)

    def test_constant_advantages(self):
        """Test normalization with constant advantages."""
        advantages = [1.0, 1.0, 1.0]
        normalized = normalize_advantages(advantages)
        # With zero std, should return zeros
        assert all(abs(v) < 1e-6 for v in normalized)
