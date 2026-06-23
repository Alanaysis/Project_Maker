"""Actor network for policy-based reinforcement learning."""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Categorical


class ActorNetwork(nn.Module):
    """Actor network that outputs action probabilities.

    The actor network learns a policy π(a|s) that maps states to action
    probabilities. It is trained using the policy gradient method with
    advantage estimates from the critic.
    """

    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        hidden_dim: int = 128,
    ) -> None:
        """Initialize the actor network.

        Args:
            state_dim: Dimension of the state space.
            action_dim: Dimension of the action space.
            hidden_dim: Dimension of hidden layers.
        """
        super().__init__()

        self.network = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, action_dim),
        )

    def forward(self, state: torch.Tensor) -> torch.Tensor:
        """Forward pass to get action logits.

        Args:
            state: State tensor of shape (batch_size, state_dim).

        Returns:
            Action logits of shape (batch_size, action_dim).
        """
        return self.network(state)

    def get_action_probs(self, state: torch.Tensor) -> torch.Tensor:
        """Get action probabilities using softmax.

        Args:
            state: State tensor of shape (batch_size, state_dim).

        Returns:
            Action probabilities of shape (batch_size, action_dim).
        """
        logits = self.forward(state)
        return F.softmax(logits, dim=-1)

    def get_action(self, state: torch.Tensor) -> tuple[int, torch.Tensor]:
        """Sample an action from the policy.

        Args:
            state: State tensor of shape (state_dim,).

        Returns:
            Tuple of (action, log_probability).
        """
        action_probs = self.get_action_probs(state.unsqueeze(0))
        dist = Categorical(action_probs)
        action = dist.sample()
        log_prob = dist.log_prob(action)
        return action.item(), log_prob.squeeze()

    def evaluate_actions(
        self, state: torch.Tensor, action: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Evaluate actions given states.

        Args:
            state: State tensor of shape (batch_size, state_dim).
            action: Action tensor of shape (batch_size,).

        Returns:
            Tuple of (log_probabilities, entropy).
        """
        action_probs = self.get_action_probs(state)
        dist = Categorical(action_probs)
        log_prob = dist.log_prob(action)
        entropy = dist.entropy()
        return log_prob, entropy
