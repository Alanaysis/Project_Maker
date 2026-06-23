"""Advantage function computation for Actor-Critic algorithms."""

import torch
import numpy as np


def compute_returns(
    rewards: list[float],
    gamma: float = 0.99,
) -> list[float]:
    """Compute discounted returns for each timestep.

    The return G_t at timestep t is the discounted sum of future rewards:
    G_t = r_t + γ * r_{t+1} + γ² * r_{t+2} + ...

    Args:
        rewards: List of rewards for each timestep.
        gamma: Discount factor.

    Returns:
        List of discounted returns for each timestep.
    """
    returns = []
    G = 0
    for reward in reversed(rewards):
        G = reward + gamma * G
        returns.insert(0, G)
    return returns


def compute_advantages(
    rewards: list[float],
    values: list[float],
    gamma: float = 0.99,
    gae_lambda: float = 1.0,
) -> list[float]:
    """Compute advantages using Generalized Advantage Estimation (GAE).

    The advantage A_t measures how much better action a_t is compared to
    the average action in state s_t. With GAE, we compute:

    δ_t = r_t + γ * V(s_{t+1}) - V(s_t)
    A_t = Σ_{l=0}^{∞} (γ * λ)^l * δ_{t+l}

    When gae_lambda=1.0, this reduces to the simple advantage:
    A_t = G_t - V(s_t)

    Args:
        rewards: List of rewards for each timestep.
        values: List of value estimates for each timestep.
        gamma: Discount factor.
        gae_lambda: GAE lambda parameter (1.0 for simple advantage).

    Returns:
        List of advantage estimates for each timestep.
    """
    if gae_lambda == 1.0:
        # Simple advantage: A_t = G_t - V(s_t)
        returns = compute_returns(rewards, gamma)
        advantages = [ret - val for ret, val in zip(returns, values)]
        return advantages

    # Full GAE computation
    advantages = []
    gae = 0
    next_value = 0

    for t in reversed(range(len(rewards))):
        delta = rewards[t] + gamma * next_value - values[t]
        gae = delta + gamma * gae_lambda * gae
        advantages.insert(0, gae)
        next_value = values[t]

    return advantages


def normalize_advantages(advantages: list[float]) -> list[float]:
    """Normalize advantages to have zero mean and unit variance.

    Args:
        advantages: List of advantage estimates.

    Returns:
        Normalized advantages.
    """
    adv_array = np.array(advantages)
    mean = adv_array.mean()
    std = adv_array.std() + 1e-8
    normalized = (adv_array - mean) / std
    return normalized.tolist()
