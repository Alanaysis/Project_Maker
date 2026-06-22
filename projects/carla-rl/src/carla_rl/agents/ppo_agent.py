"""
PPO Agent for CARLA RL

Wraps Stable-Baselines3 PPO for use with CARLA environments.
Provides convenient training and evaluation interfaces.
"""

import os
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, Callable

from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.vec_env import SubprocVecEnv, DummyVecEnv
from stable_baselines3.common.callbacks import (
    EvalCallback,
    CheckpointCallback,
    CallbackList,
)
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.evaluation import evaluate_policy


class PPOTrainer:
    """
    PPO trainer for CARLA RL environments.

    Provides high-level interface for training and evaluating
    PPO agents in CARLA environments.
    """

    def __init__(
        self,
        env_class: type,
        env_kwargs: Optional[Dict[str, Any]] = None,
        policy: str = "MlpPolicy",
        learning_rate: float = 3e-4,
        n_steps: int = 2048,
        batch_size: int = 64,
        n_epochs: int = 10,
        gamma: float = 0.99,
        gae_lambda: float = 0.95,
        clip_range: float = 0.2,
        ent_coef: float = 0.0,
        vf_coef: float = 0.5,
        max_grad_norm: float = 0.5,
        n_envs: int = 1,
        seed: Optional[int] = None,
        device: str = "auto",
        tensorboard_log: Optional[str] = None,
        verbose: int = 1,
    ):
        """
        Initialize PPO trainer.

        Args:
            env_class: Environment class to use
            env_kwargs: Keyword arguments for environment
            policy: Policy type ('MlpPolicy', 'CnnPolicy', 'MultiInputPolicy')
            learning_rate: Learning rate
            n_steps: Number of steps per update
            batch_size: Minibatch size
            n_epochs: Number of epochs per update
            gamma: Discount factor
            gae_lambda: GAE lambda parameter
            clip_range: PPO clip range
            ent_coef: Entropy coefficient
            vf_coef: Value function coefficient
            max_grad_norm: Maximum gradient norm
            n_envs: Number of parallel environments
            seed: Random seed
            device: Device ('cpu', 'cuda', 'auto')
            tensorboard_log: TensorBoard log directory
            verbose: Verbosity level
        """
        self.env_class = env_class
        self.env_kwargs = env_kwargs or {}
        self.policy = policy
        self.n_envs = n_envs
        self.seed = seed
        self.verbose = verbose

        # Store PPO hyperparameters
        self.ppo_kwargs = {
            "learning_rate": learning_rate,
            "n_steps": n_steps,
            "batch_size": batch_size,
            "n_epochs": n_epochs,
            "gamma": gamma,
            "gae_lambda": gae_lambda,
            "clip_range": clip_range,
            "ent_coef": ent_coef,
            "vf_coef": vf_coef,
            "max_grad_norm": max_grad_norm,
            "device": device,
            "tensorboard_log": tensorboard_log,
            "verbose": verbose,
        }

        # Create environments
        self.env = self._make_env()
        self.eval_env = self._make_env()

        # Create model
        self.model = PPO(
            policy=policy,
            env=self.env,
            seed=seed,
            **self.ppo_kwargs,
        )

        if verbose > 0:
            print(f"PPO Trainer initialized with {n_envs} environments")
            print(f"Policy: {policy}")
            print(f"Device: {self.model.device}")

    def _make_env(self) -> Any:
        """
        Create vectorized environment.

        Returns:
            Vectorized environment
        """
        def make_single_env():
            env = self.env_class(**self.env_kwargs)
            env = Monitor(env)
            return env

        if self.n_envs == 1:
            return DummyVecEnv([make_single_env])
        else:
            return SubprocVecEnv(
                [make_single_env for _ in range(self.n_envs)]
            )

    def train(
        self,
        total_timesteps: int = 1_000_000,
        eval_freq: int = 10_000,
        n_eval_episodes: int = 10,
        save_freq: int = 50_000,
        save_path: Optional[str] = None,
        callback: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Train the PPO agent.

        Args:
            total_timesteps: Total training timesteps
            eval_freq: Evaluation frequency (in timesteps)
            n_eval_episodes: Number of evaluation episodes
            save_freq: Checkpoint save frequency
            save_path: Path to save checkpoints
            callback: Additional callback

        Returns:
            Training information
        """
        if self.verbose > 0:
            print(f"\nStarting training for {total_timesteps} timesteps...")

        # Setup callbacks
        callbacks = []

        # Evaluation callback
        eval_callback = EvalCallback(
            self.eval_env,
            n_eval_episodes=n_eval_episodes,
            eval_freq=eval_freq,
            verbose=self.verbose,
        )
        callbacks.append(eval_callback)

        # Checkpoint callback
        if save_path:
            os.makedirs(save_path, exist_ok=True)
            checkpoint_callback = CheckpointCallback(
                save_freq=save_freq,
                save_path=save_path,
                name_prefix="ppo_carla",
            )
            callbacks.append(checkpoint_callback)

        # Add custom callback
        if callback:
            callbacks.append(callback)

        callback_list = CallbackList(callbacks) if len(callbacks) > 1 else callbacks[0]

        # Train
        self.model.learn(
            total_timesteps=total_timesteps,
            callback=callback_list,
            progress_bar=self.verbose > 0,
        )

        if self.verbose > 0:
            print("Training completed!")

        return {
            "total_timesteps": total_timesteps,
            "model": self.model,
        }

    def evaluate(
        self,
        n_episodes: int = 10,
        deterministic: bool = True,
    ) -> Dict[str, float]:
        """
        Evaluate the trained agent.

        Args:
            n_episodes: Number of evaluation episodes
            deterministic: Whether to use deterministic policy

        Returns:
            Evaluation metrics
        """
        if self.verbose > 0:
            print(f"\nEvaluating agent over {n_episodes} episodes...")

        mean_reward, std_reward = evaluate_policy(
            self.model,
            self.eval_env,
            n_eval_episodes=n_episodes,
            deterministic=deterministic,
        )

        results = {
            "mean_reward": mean_reward,
            "std_reward": std_reward,
        }

        if self.verbose > 0:
            print(f"Mean reward: {mean_reward:.2f} +/- {std_reward:.2f}")

        return results

    def predict(
        self,
        observation: Dict[str, np.ndarray],
        deterministic: bool = True,
    ) -> np.ndarray:
        """
        Get action from policy.

        Args:
            observation: Current observation
            deterministic: Whether to use deterministic policy

        Returns:
            Action array
        """
        action, _ = self.model.predict(observation, deterministic=deterministic)
        return action

    def save(self, path: str):
        """
        Save model to file.

        Args:
            path: Path to save model
        """
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        self.model.save(path)
        if self.verbose > 0:
            print(f"Model saved to {path}")

    def load(self, path: str):
        """
        Load model from file.

        Args:
            path: Path to load model from
        """
        self.model = PPO.load(path, env=self.env)
        if self.verbose > 0:
            print(f"Model loaded from {path}")

    def get_hyperparameters(self) -> Dict[str, Any]:
        """Get current hyperparameters."""
        return {
            "policy": self.policy,
            "n_envs": self.n_envs,
            **self.ppo_kwargs,
        }

    def close(self):
        """Close environments."""
        self.env.close()
        self.eval_env.close()
