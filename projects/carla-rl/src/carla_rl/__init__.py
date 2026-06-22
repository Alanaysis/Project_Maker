"""
CARLA RL - Autonomous Driving Reinforcement Learning Environment

A Gymnasium-compatible environment for training RL agents in the CARLA simulator.
"""

__version__ = "0.1.0"

from carla_rl.envs.carla_env import CarlaRLEnv
from carla_rl.agents.ppo_agent import PPOTrainer

__all__ = ["CarlaRLEnv", "PPOTrainer"]
