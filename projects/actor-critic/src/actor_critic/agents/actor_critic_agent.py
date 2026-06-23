"""Actor-Critic agent implementation."""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from typing import Optional

from ..networks import ActorNetwork, CriticNetwork
from ..utils.advantages import compute_advantages, normalize_advantages


class ActorCriticAgent:
    """Actor-Critic agent that combines policy and value-based learning.

    The agent uses two networks:
    - Actor: Learns a policy π(a|s) to select actions
    - Critic: Learns a value function V(s) to evaluate states

    The actor is updated using the policy gradient with advantage estimates
    from the critic. The critic is updated to minimize the TD error.
    """

    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        hidden_dim: int = 128,
        actor_lr: float = 3e-4,
        critic_lr: float = 1e-3,
        gamma: float = 0.99,
        gae_lambda: float = 1.0,
        entropy_coef: float = 0.01,
        value_loss_coef: float = 0.5,
        device: Optional[str] = None,
    ) -> None:
        """Initialize the Actor-Critic agent.

        Args:
            state_dim: Dimension of the state space.
            action_dim: Dimension of the action space.
            hidden_dim: Dimension of hidden layers.
            actor_lr: Learning rate for the actor network.
            critic_lr: Learning rate for the critic network.
            gamma: Discount factor for future rewards.
            gae_lambda: GAE lambda parameter.
            entropy_coef: Coefficient for entropy bonus.
            value_loss_coef: Coefficient for value loss.
            device: Device to use for computation (cpu/cuda).
        """
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = torch.device(device)

        # Hyperparameters
        self.gamma = gamma
        self.gae_lambda = gae_lambda
        self.entropy_coef = entropy_coef
        self.value_loss_coef = value_loss_coef

        # Networks
        self.actor = ActorNetwork(state_dim, action_dim, hidden_dim).to(self.device)
        self.critic = CriticNetwork(state_dim, hidden_dim).to(self.device)

        # Optimizers
        self.actor_optimizer = optim.Adam(self.actor.parameters(), lr=actor_lr)
        self.critic_optimizer = optim.Adam(self.critic.parameters(), lr=critic_lr)

        # Episode storage
        self.states: list[torch.Tensor] = []
        self.actions: list[int] = []
        self.rewards: list[float] = []
        self.log_probs: list[torch.Tensor] = []
        self.values: list[float] = []

    def select_action(self, state: np.ndarray) -> int:
        """Select an action given a state.

        Args:
            state: State as numpy array.

        Returns:
            Selected action index.
        """
        state_tensor = torch.FloatTensor(state).to(self.device)
        action, log_prob = self.actor.get_action(state_tensor)
        value = self.critic.get_value(state_tensor)

        # Store for training
        self.states.append(state_tensor)
        self.actions.append(action)
        self.log_probs.append(log_prob)
        self.values.append(value.item())

        return action

    def store_reward(self, reward: float) -> None:
        """Store a reward for the current timestep.

        Args:
            reward: Reward value.
        """
        self.rewards.append(reward)

    def update(self) -> dict[str, float]:
        """Update actor and critic networks.

        Computes advantages and updates both networks using the stored
        episode data.

        Returns:
            Dictionary containing loss metrics.
        """
        if len(self.rewards) == 0:
            return {"actor_loss": 0.0, "critic_loss": 0.0, "entropy": 0.0}

        # Compute advantages
        advantages = compute_advantages(
            self.rewards, self.values, self.gamma, self.gae_lambda
        )
        advantages = normalize_advantages(advantages)

        # Convert to tensors
        states = torch.stack(self.states).to(self.device)
        actions = torch.LongTensor(self.actions).to(self.device)
        old_log_probs = torch.stack(self.log_probs).to(self.device)
        advantages_tensor = torch.FloatTensor(advantages).to(self.device)

        # Compute returns for critic loss
        returns = []
        G = 0
        for reward in reversed(self.rewards):
            G = reward + self.gamma * G
            returns.insert(0, G)
        returns_tensor = torch.FloatTensor(returns).to(self.device)

        # Update critic
        values = self.critic(states).squeeze(-1)
        critic_loss = nn.MSELoss()(values, returns_tensor)

        self.critic_optimizer.zero_grad()
        critic_loss.backward()
        self.critic_optimizer.step()

        # Update actor
        log_probs, entropy = self.actor.evaluate_actions(states, actions)
        actor_loss = -(log_probs * advantages_tensor.detach()).mean()
        entropy_loss = -entropy.mean()

        total_actor_loss = actor_loss + self.entropy_coef * entropy_loss

        self.actor_optimizer.zero_grad()
        total_actor_loss.backward()
        self.actor_optimizer.step()

        # Clear episode storage
        self.clear_memory()

        return {
            "actor_loss": actor_loss.item(),
            "critic_loss": critic_loss.item(),
            "entropy": entropy.mean().item(),
        }

    def clear_memory(self) -> None:
        """Clear episode storage."""
        self.states.clear()
        self.actions.clear()
        self.rewards.clear()
        self.log_probs.clear()
        self.values.clear()

    def save(self, path: str) -> None:
        """Save model checkpoints.

        Args:
            path: Path to save directory.
        """
        torch.save(
            {
                "actor": self.actor.state_dict(),
                "critic": self.critic.state_dict(),
            },
            path,
        )

    def load(self, path: str) -> None:
        """Load model checkpoints.

        Args:
            path: Path to checkpoint file.
        """
        checkpoint = torch.load(path, map_location=self.device)
        self.actor.load_state_dict(checkpoint["actor"])
        self.critic.load_state_dict(checkpoint["critic"])
