"""Actor-Critic: Reinforcement Learning with Policy and Value Networks."""

from .agents import ActorCriticAgent
from .networks import ActorNetwork, CriticNetwork

__version__ = "1.0.0"
__all__ = ["ActorCriticAgent", "ActorNetwork", "CriticNetwork"]
