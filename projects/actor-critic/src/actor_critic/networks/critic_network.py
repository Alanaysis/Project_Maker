"""Critic network for value-based reinforcement learning."""

import torch
import torch.nn as nn


class CriticNetwork(nn.Module):
    """Critic network that estimates state values.

    The critic network learns a value function V(s) that estimates the
    expected return from state s. It is used to compute advantage estimates
    for the actor network.
    """

    def __init__(
        self,
        state_dim: int,
        hidden_dim: int = 128,
    ) -> None:
        """Initialize the critic network.

        Args:
            state_dim: Dimension of the state space.
            hidden_dim: Dimension of hidden layers.
        """
        super().__init__()

        self.network = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, state: torch.Tensor) -> torch.Tensor:
        """Forward pass to get state value estimate.

        Args:
            state: State tensor of shape (batch_size, state_dim).

        Returns:
            State value estimate of shape (batch_size, 1).
        """
        return self.network(state)

    def get_value(self, state: torch.Tensor) -> torch.Tensor:
        """Get the value estimate for a state.

        Args:
            state: State tensor of shape (state_dim,) or (1, state_dim).

        Returns:
            Scalar state value estimate.
        """
        if state.dim() == 1:
            state = state.unsqueeze(0)
            return self.forward(state).squeeze()
        return self.forward(state).squeeze(-1)
